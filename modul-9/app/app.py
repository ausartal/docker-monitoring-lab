"""Flask Demo App untuk CI/CD Pipeline Lab."""
import os, socket, datetime
from flask import Flask, jsonify

app = Flask(__name__)
VERSION = os.environ.get("APP_VERSION", "1.0.0")

@app.route("/")
def index():
    return jsonify({
        "app": "flask-demo",
        "version": VERSION,
        "hostname": socket.gethostname(),
        "timestamp": datetime.datetime.now().isoformat(),
        "message": "Deployed via CI/CD Pipeline! 🚀"
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "version": VERSION})

def add(a, b):
    """Fungsi sederhana untuk unit test."""
    return a + b

def multiply(a, b):
    """Fungsi sederhana untuk unit test."""
    return a * b

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
