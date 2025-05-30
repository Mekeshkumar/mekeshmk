import pandas as pd
from flask import Flask, request, jsonify, render_template, Blueprint
from flask_cors import CORS
from datetime import datetime, date
import os
import json

billing_bp = Blueprint('billing', __name__)

app = Flask(__name__)
CORS(app)

PATIENTS_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRIqCMcGG9eq_qCuGDmro202jB85I7Zmb2os4CWLXSR3RkJjQw1OrTo2yq5vOK1S3Y-GR2lE-xhWYL6/pub?gid=1505206895&single=true&output=csv"

def calc_age(dob_str):
    if not dob_str or pd.isna(dob_str):
        return ""
    try:
        # Handles "YYYY-MM-DD" and "DD/MM/YYYY"
        if '-' in dob_str:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
        else:
            dob = datetime.strptime(dob_str, "%d/%m/%Y")
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except Exception:
        return ""

@app.route('/')
def billing_page():
    try:
        df = pd.read_csv(PATIENTS_CSV_URL, dtype=str)
        df.columns = df.columns.str.strip()  # Just in case
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

@billing_bp.route('/billing')
def billing_home():
    return "Billing Page"

if __name__ == '__main__':
    app.run(debug=True, port=5000)