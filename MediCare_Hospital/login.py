from flask import Flask, request, jsonify, render_template, Blueprint
from flask_cors import CORS
import csv
import logging
import requests
from io import StringIO

app = Flask(__name__, template_folder='templates')
CORS(app)  # ✅ Allows cross-origin from HTML on different port

login_bp = Blueprint('login', __name__)

logging.basicConfig(filename='app.log', level=logging.INFO)

def read_users_from_csv():
    users = []
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRrzEuPi1OrdiXhGaEKpO9yhlPuxVxCEVA2s-D1m-0ChyYPbxk1-LxwLtwyBrLizPLUM-V8fdN4NioT/pub?gid=1836937116&single=true&output=csv"

    try:
        response = requests.get(url)
        response.raise_for_status()
        csv_data = StringIO(response.text)
        reader = csv.DictReader(csv_data)

        for row in reader:
            users.append({k.strip(): v.strip() for k, v in row.items()})  # 🔍 Remove extra whitespace

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

@login_bp.route('/login')
def login_home():
    return "Login Page"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
