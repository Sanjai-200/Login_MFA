from flask import Flask, request, jsonify, render_template
import pickle
import pandas as pd
from datetime import datetime

app = Flask(__name__)

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


# ================= SAFE PARSERS =================

def safe_int(value, default=0):
    try:
        return int(value)
    except:
        return default


def parse_time(time_str):
    if not time_str:
        return 12

    time_str = str(time_str).strip()

    try:
        # 24-hour format (21:24:18)
        if ":" in time_str and "AM" not in time_str and "PM" not in time_str:
            return int(time_str.split(":")[0])

        # 12-hour format (7:24:18 PM)
        if "AM" in time_str or "PM" in time_str:
            try:
                return datetime.strptime(time_str, "%I:%M:%S %p").hour
            except:
                return datetime.strptime(time_str, "%I:%M %p").hour

    except:
        pass

    return 12  # fallback


def parse_location(location):
    if not location:
        return 0

    loc = str(location).strip().lower()

    # treat safe
    if loc in ["india", "unknown", ""]:
        return 0

    return 1  # risky


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

    return df


# ================= PREDICT =================

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json

    input_data = encode(data)

    pred = model.predict(input_data)[0]

    # DEBUG (optional)
    print("RAW INPUT:", data)
    print("PROCESSED:", input_data.to_dict())
    print("PREDICTION:", pred)

    return jsonify({"prediction": int(pred)})


# RUN
if __name__ == "__main__":
    app.run(debug=True)
