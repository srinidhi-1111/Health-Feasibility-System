import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
)
import joblib

# Load dataset
df = pd.read_csv("synthetic_health_dataset.csv")

X = df.drop("Class", axis=1)
y = df["Class"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Predictions
y_pred = model.predict(X_test)

# Metrics
metrics = {
    "Accuracy": accuracy_score(y_test, y_pred),
    "Precision": precision_score(y_test, y_pred),
    "Recall": recall_score(y_test, y_pred),
    "F1 Score": f1_score(y_test, y_pred)
}

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred)

# Save everything
joblib.dump(model, "rf_health_model.pkl")
joblib.dump(metrics, "model_metrics.pkl")
joblib.dump(cm, "confusion_matrix.pkl")

print("Training completed.")
print("Metrics:", metrics)
print("Confusion Matrix:\n", cm)
