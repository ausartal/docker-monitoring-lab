import os, socket, datetime
from flask import Flask, jsonify, request
import psycopg2

app = Flask(__name__)

def get_db():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "db"),
        dbname=os.environ.get("DB_NAME", "labdb"),
        user=os.environ.get("DB_USER", "labuser"),
        password=os.environ.get("DB_PASS", "labpass123"))

@app.route("/")
def index():
    return jsonify({
        "service": "Flask Backend API",
        "hostname": socket.gethostname(),
        "timestamp": datetime.datetime.now().isoformat(),
        "client_ip": request.headers.get("X-Real-IP", request.remote_addr),
        "proto": request.headers.get("X-Forwarded-Proto", "http")
    })

@app.route("/api/health")
def health():
    result = {"status": "ok", "database": "unknown"}
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        result["database"] = cur.fetchone()[0]
        result["db_status"] = "connected"
        cur.close(); conn.close()
    except Exception as e:
        result["db_status"] = f"error: {e}"
    return jsonify(result)

@app.route("/api/visitors", methods=["POST"])
def add_visitor():
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS visitors (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
        name = request.json.get("name", "anonymous")
        cur.execute("INSERT INTO visitors (name) VALUES (%s) RETURNING id, visited_at", (name,))
        row = cur.fetchone()
        conn.commit(); cur.close(); conn.close()
        return jsonify({"id": row[0], "name": name, "visited_at": str(row[1])}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/visitors", methods=["GET"])
def get_visitors():
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT id, name, visited_at FROM visitors ORDER BY id DESC LIMIT 20")
        rows = [{"id": r[0], "name": r[1], "visited_at": str(r[2])} for r in cur.fetchall()]
        cur.close(); conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
