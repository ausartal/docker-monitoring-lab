import os, socket, datetime
from flask import Flask, jsonify

app = Flask(__name__)

def read_secret(name, default=""):
    """Baca secret dari /run/secrets/ atau fallback ke env."""
    secret_path = f"/run/secrets/{name}"
    if os.path.exists(secret_path):
        with open(secret_path, "r") as f:
            return f.read().strip()
    return os.environ.get(name.upper(), default)

@app.route("/")
def index():
    return jsonify({
        "service": "flask-app-secured",
        "hostname": socket.gethostname(),
        "user": os.getenv("USER", "unknown"),
        "uid": os.getuid(),
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route("/api/health")
def health():
    import psycopg2
    try:
        conn = psycopg2.connect(
            host=read_secret("db_host", "postgres-db"),
            dbname=read_secret("db_name", "labdb"),
            user=read_secret("db_user", "labuser"),
            password=read_secret("db_password", ""))
        cur = conn.cursor()
        cur.execute("SELECT version();")
        ver = cur.fetchone()[0]
        cur.close(); conn.close()
        return jsonify({"status": "ok", "database": ver, "secrets_method": "file-based"})
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
