
from flask import Flask, request, jsonify
import psycopg2



app = Flask(__name__)

DB_CONFIG = {
    'dbname': 'flask',
    'user': 'postgres',
    'password': '1234',
    'host': 'localhost',
    'port': '5432'
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn


@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')

    if not name or not email:
        return jsonify({'error': 'Name and email are required!'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id;",
            (name, email)
        )

        new_id = cur.fetchone()[0]
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({'message': 'User added successfully', 'user_id': new_id}), 201

    except psycopg2.Error as e:
        return jsonify({'error': str(e)}), 500


# --- Route to view all users ---
@app.route('/users', methods=['GET'])
def get_users():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, email FROM users;")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # Convert to list of dicts
        users = [{'id': row[0], 'name': row[1], 'email': row[2]} for row in rows]

        return jsonify(users)

    except psycopg2.Error as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
