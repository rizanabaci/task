from flask import Flask, request, jsonify
import psycopg2
from psycopg2 import pool

app = Flask(__name__)

DB_CONFIG = {
    'dbname': 'flask',
    'user': 'postgres',
    'password': '1234',
    'host': 'localhost',
    'port': '5432'
}

try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, **DB_CONFIG)
    if connection_pool:
        print(" Connection pool created successfully")
except (Exception, psycopg2.DatabaseError) as error:
    print(" Error while connecting to PostgreSQL:", error)


def get_db_connection():
    return connection_pool.getconn()


def release_db_connection(conn):
    connection_pool.putconn(conn)


@app.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')

    if not name or not email:
        return jsonify({'error': 'Name and email are required!'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id;",
            (name, email)
        )

        user_id = cur.fetchone()[0]
        conn.commit()

        cur.close()
        release_db_connection(conn)

        return jsonify({'message': 'User added successfully', 'user_id': user_id}), 201

    except psycopg2.Error as e:
        if conn:
            release_db_connection(conn)
        return jsonify({'error': str(e)}), 500


@app.route('/users', methods=['GET'])
def get_users():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id, name, email FROM users ORDER BY id;")
        rows = cur.fetchall()
        users = [{'id': row[0], 'name': row[1], 'email': row[2]} for row in rows]

        cur.close()
        release_db_connection(conn)

        return jsonify(users), 200

    except psycopg2.Error as e:
        if conn:
            release_db_connection(conn)
        return jsonify({'error': str(e)}), 500



@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = %s RETURNING id;", (user_id,))
        deleted = cur.fetchone()

        if deleted:
            conn.commit()
            cur.close()
            release_db_connection(conn)
            return jsonify({'message': 'User deleted successfully'}), 200
        else:
            cur.close()
            release_db_connection(conn)
            return jsonify({'error': 'User not found'}), 404

    except psycopg2.Error as e:
        if conn:
            release_db_connection(conn)
        return jsonify({'error': str(e)}), 500


import atexit

def close_connection_pool():
    if connection_pool:
        connection_pool.closeall()
        print("Connection pool closed.")

# Register cleanup handler to run only when the app stops
atexit.register(close_connection_pool)



if __name__ == '__main__':
    app.run(debug=True)
