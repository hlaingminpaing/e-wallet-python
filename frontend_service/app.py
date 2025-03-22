from flask import Flask, render_template, request, redirect, url_for
import requests
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Service URLs from environment variables
USER_SERVICE_URL = os.getenv('USER_SERVICE_URL')
WALLET_SERVICE_URL = os.getenv('WALLET_SERVICE_URL')

@app.route('/')
def index():
    # Fetch all users
    users_response = requests.get(f'{USER_SERVICE_URL}/users')
    users = users_response.json() if users_response.status_code == 200 else []

    # Fetch all wallets
    wallets = []
    for user in users:
        wallet_response = requests.get(f'{WALLET_SERVICE_URL}/wallets/{user["id"]}')
        if wallet_response.status_code == 200:
            wallets.append(wallet_response.json())
        else:
            wallets.append({'user_id': user['id'], 'balance': 'N/A'})

    return render_template('index.html', users=users, wallets=wallets)

@app.route('/create_user', methods=['POST'])
def create_user():
    username = request.form['username']
    email = request.form['email']
    response = requests.post(f'{USER_SERVICE_URL}/users', json={'username': username, 'email': email})
    if response.status_code == 201:
        user_id = response.json()['id']
        # Create a wallet for the new user
        requests.post(f'{WALLET_SERVICE_URL}/wallets', json={'user_id': user_id})
    return redirect(url_for('index'))

@app.route('/deposit/<int:wallet_id>', methods=['POST'])
def deposit(wallet_id):
    amount = float(request.form['amount'])
    requests.post(f'{WALLET_SERVICE_URL}/wallets/{wallet_id}/deposit', json={'amount': amount})
    return redirect(url_for('index'))

@app.route('/withdraw/<int:wallet_id>', methods=['POST'])
def withdraw(wallet_id):
    amount = float(request.form['amount'])
    requests.post(f'{WALLET_SERVICE_URL}/wallets/{wallet_id}/withdraw', json={'amount': amount})
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)