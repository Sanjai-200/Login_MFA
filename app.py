from flask import Flask, request, jsonify, render_template
import pickle
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# ================= EMAIL CONFIG =================
EMAIL_SENDER = "smart7mfa@gmail.com"
EMAIL_PASSWORD = "qbfq ujgg pnpo ikrc"

# LOAD MODEL
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

# ROUTES
@app.route("/")
def login():
    return render_template("index.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/otp")
def otp():
    return render_template("otp.html")

@app.route("/home")
def home():
    return render_template("home.html")


# ================= EMAIL =================
def send_email(receiver, otp):
    try:
        msg = MIMEText(f"Your OTP is: {otp}")
        msg["Subject"] = "Your OTP Code"
        msg["From"] = EMAIL_SENDER
        msg["To"] = receiver

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("✅ OTP Email sent")

    except Exception as e:
        print("❌ Email Error:", e)


@app.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.json
    send_email(data.get("email"), data.get("otp"))
    return jsonify({"status": "sent"})


# ================= PARSERS =================
def safe_int(value, default=0):
    try:
        return int(value)
    except:
        return default


def parse_time(time_str):
    try:
        return int(str(time_str).split(":")[0])
    except:
        return 12


# ✅ CORRECT ENCODING (DO NOT CHANGE)
def parse_location(location):
    if not location:
        return 0
    loc = str(location).lower()
    if loc in ["india", "unknown", ""]:
        return 0
    return 1


def parse_device(device):
    if not device:
        return 0
    dev = str(device).lower()
    if "mobile" in dev:
        return 1
    return 0


# ================= ENCODE =================
def encode(data):
    device = parse_device(data.get("device"))
    location = parse_location(data.get("location"))
    loginCount = safe_int(data.get("loginCount"), 1)
    failedAttempts = safe_int(data.get("failedAttempts"), 0)
    hour = parse_time(data.get("time"))

    df = pd.DataFrame(
        [[device, location, loginCount, hour, failedAttempts]],
        columns=["device", "location", "loginCount", "hour", "failedAttempts"]
    )

    print("FINAL INPUT:", df.values.tolist())

    return df


# ================= PREDICT =================
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json

    input_data = encode(data)

    pred = model.predict(input_data)[0]

    print("PREDICTION:", pred)

    return jsonify({"prediction": int(pred)})


# RUN
if __name__ == "__main__":
    app.run(debug=True)
