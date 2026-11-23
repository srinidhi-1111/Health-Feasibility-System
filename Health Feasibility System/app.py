import matplotlib
matplotlib.use("Agg") 
from flask import Flask, render_template, request, session, redirect, jsonify, flash
import sqlite3
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import os
from werkzeug.security import generate_password_hash, check_password_hash
from arduino_serial_reader import read_average_parameters
import requests
# ---------------- TELEGRAM CONFIG ----------------
TELEGRAM_BOT_TOKEN = "8060929635:AAHCRr4Al6VtCAOgFVwjiUh0abJGkpzPF0g"
TELEGRAM_CHAT_ID = "1221911146"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, data=payload)
        print("Telegram Response:", response.text)
    except Exception as e:
        print("Telegram Error:", e)

app = Flask(__name__)
app.secret_key = "super_secret_key"

PLOT_DIR = "static/plots"
os.makedirs(PLOT_DIR, exist_ok=True)

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("auth.db")

def init_db():
    with get_db() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            dob TEXT,
            email TEXT UNIQUE,
            username TEXT UNIQUE,
            password TEXT
        )
        """)
init_db()

# ---------------- LOAD MODEL ----------------
model = joblib.load("rf_health_model.pkl")
metrics = joblib.load("model_metrics.pkl")
cm = joblib.load("confusion_matrix.pkl")

# ---------------- DASHBOARD ----------------
@app.route("/")
def root():
    session.clear()              # 🔥 FORCE LOGOUT
    return redirect("/login-page")


@app.route("/login-page")
def login_page():
    if "user" in session:
        return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login-page")
    print("Session content:", dict(session))

    return render_template("dashboard.html", user=session["user"])





# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    identifier = request.form["identifier"]
    password = request.form["password"]

    user = get_db().execute(
        "SELECT * FROM users WHERE username=? OR email=?",
        (identifier, identifier)
    ).fetchone()

    if user and check_password_hash(user[5], password):
        session.clear()
        session["user"] = user[1]      # real name
        session["user_email"] = user[3]
        flash(f"Welcome back, {user[1]}!", "success")
        return jsonify(success=True)

    return jsonify(success=False, message="Invalid credentials")

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.form
    try:
        db = get_db()
        db.execute(
            """
            INSERT INTO users (name, dob, email, username, password)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data["name"],
                data["dob"],
                data["email"],
                data["username"],
                generate_password_hash(data["password"])
            )
        )
        db.commit()
        flash("Account created successfully. You can now login.", "success")
        return jsonify(success=True)
    except sqlite3.IntegrityError as e:
        msg = str(e)
        if 'users.email' in msg or 'email' in msg:
            friendly = 'Email already registered'
        elif 'users.username' in msg or 'username' in msg:
            friendly = 'Username already taken'
        else:
            friendly = 'Account creation failed (duplicate data)'
        return jsonify(success=False, message=friendly)

# ---------------- ARDUINO ----------------
@app.route("/arduino")
def arduino():
    try:
        result = read_average_parameters()

        if result is None:
            return jsonify(success=False, error="No data received")

        hb, bt, hum, rt = result

        return jsonify(
            success=True,
            heart_beat=hb,
            body_temp=bt,
            humidity=hum,
            atm_temp=rt
        )

    except Exception as e:
        print("ARDUINO ERROR:", e)
        return jsonify(success=False, error=str(e))



# ---------------- PREDICT ----------------
@app.route("/predict", methods=["POST"])
def predict():

    if "user" not in session:
        return jsonify(error="Unauthorized"), 401

    try:
        hb = float(request.form["heart_beat"])
        bt = float(request.form["body_temp"])
        hum = float(request.form["humidity"])
        rt = float(request.form["atm_temp"])

        df = pd.DataFrame([[hb, bt, hum, rt]], columns=[
            "Heart Beat",
            "Human Body Temperature",
            "Humidity",
            "Atmospheric Temperature"
        ])

        pred = model.predict(df)[0]


        # 🔔 Send Telegram Alert if Abnormal
        if pred == 0:
            alert_message = f"""
⚠️ HEALTH ALERT ⚠️

User: {session.get("user")}

Prediction: Abnormal

Heart Rate: {hb}
Body Temp: {bt}
Humidity: {hum}
Room Temp: {rt}

Immediate medical attention recommended.
"""
            send_telegram_alert(alert_message)

        return jsonify(
            success=True,
            prediction=int(pred),
            label="Feasible / Normal" if pred == 1 else "Not Feasible / Abnormal"
        )

    except Exception as e:
        print("Prediction Error:", e)
        return jsonify(success=False)

# ---------------- PLOTS ----------------
@app.route("/plots")
def plots():
    # Metrics plot
    plt.figure(figsize=(5, 3))
    plt.bar(metrics.keys(), metrics.values())
    plt.ylim(0, 1)
    for i, v in enumerate(metrics.values()):
        plt.text(i, v + 0.01, f"{v:.2f}", ha="center")
    plt.savefig(f"{PLOT_DIR}/metrics.png")
    plt.close()

    # Confusion matrix
    plt.figure(figsize=(8, 6))
    plt.imshow(cm)
    plt.xticks([0, 1], ["Non-Feasible", "Feasible"])
    plt.yticks([0, 1], ["Non-Feasible", "Feasible"])
    for i in range(2):
        for j in range(2):
            plt.text(j, i, cm[i][j], ha="center", va="center")
    plt.savefig(f"{PLOT_DIR}/confusion_matrix.png")
    plt.close()

    return jsonify(success=True)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
