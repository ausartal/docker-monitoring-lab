import os, socket, datetime
from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)

@app.route("/api/health")
def health():
    result = {"status": "ok", "hostname": socket.gethostname(),
              "timestamp": datetime.datetime.now().isoformat()}
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST", "db"),
            dbname=os.environ.get("DB_NAME", "labdb"),
            user=os.environ.get("DB_USER", "labuser"),
            password=os.environ.get("DB_PASS", "labpass123"))
        cur = conn.cursor()
        cur.execute("SELECT version();")
        result["database"] = cur.fetchone()[0]
        result["db_status"] = "connected"
        cur.close(); conn.close()
    except Exception as e:
        result["db_status"] = f"error: {e}"
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
