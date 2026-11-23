import serial
import time
import re  # make sure this is at top of file

PORT = "COM7"
BAUD_RATE = 9600
SAMPLES = 10

def read_average_parameters():
    try:
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print("\nConnected to Arduino...")
    except Exception as e:
        print("Serial Error:", e)
        return None

    heart_rate_values = []
    body_temp_values = []
    humidity_values = []
    room_temp_values = []

    print("\nCollecting first 10 readings...\n")

    while len(heart_rate_values) < SAMPLES:

        line = ser.readline().decode("utf-8", errors="ignore").strip()

        if not line:
            continue

        print("RAW:", line)

        if "Heart Rate:" in line:

            match = re.search(
                r"Heart Rate:\s*([\d.]+)\s*BPM\s*\|\s*Body Temp:\s*([\d.]+)\s*°C\s*\|\s*Atmos Temp:\s*([\d.]+)\s*°C\s*\|\s*Humidity:\s*([\d.]+)",
                line
            )

            if match:
                heart_rate = float(match.group(1))
                body_temp = float(match.group(2))
                room_temp = float(match.group(3))
                humidity = float(match.group(4))

                # Only reject completely unrealistic BPM
                if heart_rate > 20:

                    heart_rate_values.append(heart_rate)
                    body_temp_values.append(body_temp)
                    room_temp_values.append(room_temp)
                    humidity_values.append(humidity)

                    reading_number = len(heart_rate_values)

                    print(f"\nReading {reading_number}:")
                    print(f"  HeartRate (MAX30102): {heart_rate}")
                    print(f"  BodyTemp (LM35): {body_temp}")
                    print(f"  Humidity: {humidity}")
                    print(f"  RoomTemp: {room_temp}")
                    print("-----------------------------------")

    ser.close()

    avg_heart = round(sum(heart_rate_values) / SAMPLES, 2)
    avg_body = round(sum(body_temp_values) / SAMPLES, 2)
    avg_humidity = round(sum(humidity_values) / SAMPLES, 2)
    avg_room = round(sum(room_temp_values) / SAMPLES, 2)

    print("\nFinal Averaged Values:")
    print(f"  Avg HeartRate: {avg_heart}")
    print(f"  Avg BodyTemp: {avg_body}")
    print(f"  Avg Humidity: {avg_humidity}")
    print(f"  Avg RoomTemp: {avg_room}")
    print("===================================\n")

    return avg_heart, avg_body, avg_humidity, avg_room
