from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime, date
import pandas as pd
import os
import json
import csv
import logging
import requests
from io import StringIO

app = Flask(__name__, template_folder='templates')
app.secret_key = 'MekeshKumar1236'
CORS(app)  # Allow cross-origin requests

# ----------------- BILLING FUNCTIONALITY -----------------

PATIENTS_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRIqCMcGG9eq_qCuGDmro202jB85I7Zmb2os4CWLXSR3RkJjQw1OrTo2yq5vOK1S3Y-GR2lE-xhWYL6/pub?gid=1505206895&single=true&output=csv"

def calc_age(dob_str):
    if not dob_str or pd.isna(dob_str):
        return ""
    try:
        if '-' in dob_str:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
        else:
            dob = datetime.strptime(dob_str, "%d/%m/%Y")
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except Exception:
        return ""

@app.route('/billing')
def billing_page():
    try:
        df = pd.read_csv(PATIENTS_CSV_URL, dtype=str)
        df.columns = df.columns.str.strip()
        if 'patient_id' in df.columns and 'name' in df.columns:
            patients = df[['patient_id', 'name']].to_dict(orient='records')
        else:
            patients = []
    except Exception:
        patients = []
    return render_template('billing.html', patients=patients, today=date.today())

@app.route('/api/get_patient')
def get_patient():
    patient_id = request.args.get('id', '').strip().upper()
    if not patient_id:
        return jsonify({"error": "Missing Patient ID"}), 400
    try:
        df = pd.read_csv(PATIENTS_CSV_URL, dtype=str)
        df.columns = df.columns.str.strip()
    except Exception:
        return jsonify({"error": "Could not load patient data"}), 500

    if 'patient_id' not in df.columns:
        return jsonify({"error": "CSV missing 'patient_id' column. Available: " + str(list(df.columns))}), 500

    df['patient_id'] = df['patient_id'].astype(str).str.strip().str.upper()
    patient_row = df[df['patient_id'] == patient_id]
    if patient_row.empty:
        return jsonify({"error": f"Patient ID '{patient_id}' not found"}), 404

    row = patient_row.iloc[0]
    dob = row.get('dob', '')
    age = calc_age(dob)
    result = {
        "patient_id": row.get('patient_id', ''),
        "name": row.get('name', ''),
        "age": age,
        "gender": row.get('gender', ''),
        "admission_date": row.get('admission_date', ''),
        "room": row.get('room', ''),
        "insurance_id": row.get('insurance_id', ''),
    }
    return jsonify(result)

@app.route('/api/save_billing', methods=['POST'])
def save_billing():
    data = request.json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"billing_{timestamp}.json"
    filepath = os.path.join('static', 'billings', filename)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

    return jsonify({'status': 'success', 'file': filename}), 200

# ----------------- LOGIN FUNCTIONALITY -----------------

LOGIN_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRrzEuPi1OrdiXhGaEKpO9yhlPuxVxCEVA2s-D1m-0ChyYPbxk1-LxwLtwyBrLizPLUM-V8fdN4NioT/pub?gid=1836937116&single=true&output=csv"

logging.basicConfig(filename='app.log', level=logging.INFO)

def read_users_from_csv():
    users = []
    try:
        response = requests.get(LOGIN_CSV_URL)
        response.raise_for_status()
        csv_data = StringIO(response.text)
        reader = csv.DictReader(csv_data)

        for row in reader:
            users.append({k.strip(): v.strip() for k, v in row.items()})
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
    return users

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()

    users = read_users_from_csv()

    for user in users:
        if user.get('email') == email and user.get('password') == password:
            return jsonify(success=True, message="Login successful")

    return jsonify(success=False, message="Incorrect email or password.")

# ----------------- MAIN -----------------

if __name__ == '__main__':
    app.run(debug=True, port=5000)
