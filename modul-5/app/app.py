"""
Flask App — Structured JSON logging ke stdout + API untuk query log.
Log yang keluar ke stdout ditangkap oleh Docker fluentd driver → Fluent Bit → PostgreSQL.
"""
import os, json, socket, datetime, logging, sys
from flask import Flask, jsonify, request
import psycopg2

app = Flask(__name__)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.datetime.now().isoformat(),
            "level": record.levelname,
            "hostname": socket.gethostname(),
            "service": "flask-app",
            "message": record.getMessage(),
            "module": record.module
        })

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
app.logger.handlers = [handler]
app.logger.setLevel(logging.INFO)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

DB = dict(
    host=os.environ.get("DB_HOST", "postgres-db"),
    dbname=os.environ.get("DB_NAME", "labdb"),
    user=os.environ.get("DB_USER", "labuser"),
    password=os.environ.get("DB_PASS", "labpass123")
)

def get_db():
    return psycopg2.connect(**DB)

@app.route("/")
def index():
    app.logger.info(f"Index accessed from {request.remote_addr}")
    return jsonify({"service": "flask-app", "status": "running",
                    "hostname": socket.gethostname()})

@app.route("/api/logs/stats")
def log_stats():
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM logs.fluentbit")
        total = cur.fetchone()[0]
        cur.execute("""
            SELECT tag, COUNT(*) AS count FROM logs.fluentbit
            WHERE time > NOW() - INTERVAL '1 hour'
            GROUP BY tag ORDER BY count DESC""")
        by_tag = [{"tag": r[0], "count": r[1]} for r in cur.fetchall()]
        cur.execute("""
            SELECT (data->>'log')::jsonb->>'level' AS level, COUNT(*) AS count
            FROM logs.fluentbit
            WHERE time > NOW() - INTERVAL '1 hour'
              AND data->>'log' IS NOT NULL AND LEFT(TRIM(data->>'log'), 1) = '{'
            GROUP BY level ORDER BY count DESC""")
        by_level = [{"level": r[0], "count": r[1]} for r in cur.fetchall()]
        cur.close(); conn.close()
        return jsonify({"total_logs_all_time": total,
                        "last_hour_by_tag": by_tag,
                        "last_hour_by_level": by_level})
    except Exception as e:
        app.logger.error(f"Failed to query log stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/logs/search")
def log_search():
    keyword = request.args.get("q", "")
    level   = request.args.get("level", "")
    tag     = request.args.get("tag", "")
    limit   = min(int(request.args.get("limit", 50)), 200)
    try:
        conn = get_db(); cur = conn.cursor()
        query = """SELECT id, received_at, tag, container_name, log_level, message, service
                   FROM logs.structured_logs WHERE 1=1"""
        params = []
        if keyword:
            query += " AND message ILIKE %s"; params.append(f"%{keyword}%")
        if level:
            query += " AND log_level = %s"; params.append(level.upper())
        if tag:
            query += " AND tag ILIKE %s"; params.append(f"%{tag}%")
        query += " ORDER BY received_at DESC LIMIT %s"; params.append(limit)
        cur.execute(query, params)
        logs = [{"id": r[0], "time": str(r[1]), "tag": r[2],
                 "container": r[3], "level": r[4], "message": r[5], "service": r[6]}
                for r in cur.fetchall()]
        cur.close(); conn.close()
        return jsonify({"count": len(logs), "results": logs})
    except Exception as e:
        app.logger.error(f"Log search error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/logs/raw")
def log_raw():
    limit = min(int(request.args.get("limit", 20)), 100)
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            SELECT id, time, tag,
                   REPLACE(data->>'container_name', '/', '') AS container,
                   data->>'source' AS source,
                   LEFT(data->>'log', 300) AS log_content
            FROM logs.fluentbit ORDER BY time DESC LIMIT %s""", (limit,))
        logs = [{"id": r[0], "time": str(r[1]), "tag": r[2],
                 "container": r[3], "source": r[4], "log": r[5]}
                for r in cur.fetchall()]
        cur.close(); conn.close()
        return jsonify({"count": len(logs), "results": logs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
