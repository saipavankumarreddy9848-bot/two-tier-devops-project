
from flask import Flask, jsonify, request
from mysql.connector import Error
from db import get_db_connection

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "healthy"}), 200


@app.get("/db-health")
def db_health():
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        return jsonify({"database": "connected"}), 200
    except Error:
        return jsonify({"database": "unavailable"}), 503
    finally:
        if connection and connection.is_connected():
            connection.close()


@app.get("/employees")
def get_employees():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, email FROM employees ORDER BY id"
        )
        return jsonify(cursor.fetchall()), 200
    except Error:
        return jsonify({"error": "Database unavailable"}), 503
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.post("/employees")
def create_employee():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    email = data.get("email")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Name is required"}), 400
    if not isinstance(email, str) or not email.strip():
        return jsonify({"error": "Email is required"}), 400

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO employees (name, email) VALUES (%s, %s)",
            (name.strip(), email.strip()),
        )
        connection.commit()
        return jsonify({
            "message": "Employee created",
            "id": cursor.lastrowid,
        }), 201
    except Error:
        if connection and connection.is_connected():
            connection.rollback()
        return jsonify({"error": "Could not create employee"}), 503
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
