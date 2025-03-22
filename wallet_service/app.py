from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Database configuration from environment variables
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT', 3306))
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# CRUD Operations for Wallets (same as before)
@app.route('/wallets', methods=['POST'])
def create_wallet():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO wallets (user_id, balance) VALUES (%s, %s)', (user_id, 0.00))
        conn.commit()
        wallet_id = cursor.lastrowid
        return jsonify({'id': wallet_id, 'user_id': user_id, 'balance': 0.00}), 201
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/wallets/<int:wallet_id>', methods=['GET'])
def get_wallet(wallet_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM wallets WHERE id = %s', (wallet_id,))
        wallet = cursor.fetchone()
        if wallet:
            return jsonify(wallet), 200
        return jsonify({'error': 'Wallet not found'}), 404
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/wallets/<int:wallet_id>/deposit', methods=['POST'])
def deposit(wallet_id):
    data = request.get_json()
    amount = data.get('amount')

    if not amount or amount <= 0:
        return jsonify({'error': 'Valid amount is required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE wallets SET balance = balance + %s WHERE id = %s', (amount, wallet_id))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Wallet not found'}), 404

        cursor.execute('INSERT INTO transactions (wallet_id, amount, transaction_type) VALUES (%s, %s, %s)', 
                       (wallet_id, amount, 'DEPOSIT'))
        conn.commit()
        return jsonify({'message': 'Deposit successful'}), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/wallets/<int:wallet_id>/withdraw', methods=['POST'])
def withdraw(wallet_id):
    data = request.get_json()
    amount = data.get('amount')

    if not amount or amount <= 0:
        return jsonify({'error': 'Valid amount is required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM wallets WHERE id = %s', (wallet_id,))
        wallet = cursor.fetchone()
        if not wallet:
            return jsonify({'error': 'Wallet not found'}), 404

        balance = wallet[0]
        if balance < amount:
            return jsonify({'error': 'Insufficient balance'}), 400

        cursor.execute('UPDATE wallets SET balance = balance - %s WHERE id = %s', (amount, wallet_id))
        cursor.execute('INSERT INTO transactions (wallet_id, amount, transaction_type) VALUES (%s, %s, %s)', 
                       (wallet_id, amount, 'WITHDRAW'))
        conn.commit()
        return jsonify({'message': 'Withdrawal successful'}), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/wallets/<int:wallet_id>/transactions', methods=['GET'])
def get_transactions(wallet_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM transactions WHERE wallet_id = %s', (wallet_id,))
        transactions = cursor.fetchall()
        return jsonify(transactions), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)