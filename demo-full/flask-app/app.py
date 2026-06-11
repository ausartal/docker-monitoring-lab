import os, time, json, logging
from datetime import datetime
from flask import Flask, jsonify, request, g
import psycopg2
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({"timestamp": datetime.utcnow().isoformat(),
                           "level": record.levelname, "message": record.getMessage()})

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
app.logger.handlers = [handler]
app.logger.setLevel(logging.INFO)

REQUEST_COUNT   = Counter('flask_request_count_total', 'Total requests', ['method','endpoint','status'])
REQUEST_LATENCY = Histogram('flask_request_latency_seconds', 'Latency', ['endpoint'])
DB_CONNECTIONS  = Gauge('flask_db_connections_active', 'Active DB connections')
APP_INFO        = Gauge('flask_app_info', 'App info', ['version'])
APP_INFO.labels(version='1.0.0').set(1)

def read_secret(name):
    try:
        with open(f'/run/secrets/{name}') as f: return f.read().strip()
    except FileNotFoundError:
        return os.environ.get(name.upper(), '')

def get_db():
    try:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST','postgres-main'), port=5432,
            dbname=os.environ.get('DB_NAME','labdb'),
            user=read_secret('db_user') or 'labuser',
            password=read_secret('db_password') or 'labpass123',
            connect_timeout=3)
        DB_CONNECTIONS.inc()
        return conn
    except Exception as e:
        app.logger.error(f"DB error: {e}")
        return None

@app.before_request
def before_request(): g.start_time = time.time()

@app.after_request
def after_request(response):
    latency = time.time() - g.start_time
    REQUEST_COUNT.labels(method=request.method, endpoint=request.path, status=response.status_code).inc()
    REQUEST_LATENCY.labels(endpoint=request.path).observe(latency)
    return response

@app.route('/')
def index():
    return jsonify({"service":"Flask Demo","version":"1.0.0","lab":"Docker Monitoring Lab — PENS",
                    "endpoints":["/api/health","/api/mahasiswa","/api/stats","/api/logs/stats","/metrics"]})

@app.route('/api/health')
def health():
    conn = get_db()
    db_ok = False
    if conn:
        try:
            conn.cursor().execute('SELECT 1'); db_ok = True; conn.close(); DB_CONNECTIONS.dec()
        except: pass
    return jsonify({"status":"healthy" if db_ok else "degraded",
                    "database":"connected" if db_ok else "disconnected",
                    "timestamp":datetime.utcnow().isoformat()}), 200 if db_ok else 503

@app.route('/api/mahasiswa', methods=['GET'])
def get_mahasiswa():
    conn = get_db()
    if not conn: return jsonify({"error":"DB unavailable"}), 503
    cur = conn.cursor()
    cur.execute('SELECT nrp,nama,jurusan,angkatan FROM app.mahasiswa ORDER BY nama LIMIT 50')
    rows = cur.fetchall(); cur.close(); conn.close(); DB_CONNECTIONS.dec()
    return jsonify([{"nrp":r[0],"nama":r[1],"jurusan":r[2],"angkatan":r[3]} for r in rows])

@app.route('/api/mahasiswa', methods=['POST'])
def add_mahasiswa():
    data = request.get_json()
    if not data or not all(k in data for k in ['nrp','nama','jurusan','angkatan']):
        return jsonify({"error":"Missing fields"}), 400
    conn = get_db()
    if not conn: return jsonify({"error":"DB unavailable"}), 503
    cur = conn.cursor()
    cur.execute('INSERT INTO app.mahasiswa (nrp,nama,jurusan,angkatan) VALUES (%s,%s,%s,%s)',
                (data['nrp'],data['nama'],data['jurusan'],data['angkatan']))
    conn.commit(); cur.close(); conn.close(); DB_CONNECTIONS.dec()
    return jsonify({"status":"created","nrp":data['nrp']}), 201

@app.route('/api/stats')
def stats():
    conn = get_db()
    if not conn: return jsonify({"error":"DB unavailable"}), 503
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM app.mahasiswa'); m = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM app.matakuliah'); mk = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM logs.fluentbit WHERE time > NOW()-INTERVAL '1 hour'"); l = cur.fetchone()[0]
    cur.close(); conn.close(); DB_CONNECTIONS.dec()
    return jsonify({"mahasiswa":m,"matakuliah":mk,"logs_last_1h":l,"timestamp":datetime.utcnow().isoformat()})

@app.route('/api/logs/stats')
def log_stats():
    conn = get_db()
    if not conn: return jsonify({"error":"DB unavailable","total_logs":0}), 200
    try:
        cur = conn.cursor()
        cur.execute("SELECT data->>'level',COUNT(*) FROM logs.fluentbit WHERE time>NOW()-INTERVAL '1 hour' GROUP BY 1 ORDER BY 2 DESC")
        rows = cur.fetchall()
        cur.execute('SELECT COUNT(*) FROM logs.fluentbit'); total = cur.fetchone()[0]
        cur.close(); conn.close(); DB_CONNECTIONS.dec()
        return jsonify({"total_logs":total,"last_1h_by_level":{r[0]:r[1] for r in rows if r[0]},"timestamp":datetime.utcnow().isoformat()})
    except Exception as e:
        return jsonify({"error":str(e),"total_logs":0}), 200

@app.route('/api/logs/search')
def log_search():
    level = request.args.get('level','').upper()
    q     = request.args.get('q','')
    tag   = request.args.get('tag','')
    limit = min(int(request.args.get('limit',50)),200)
    conn  = get_db()
    if not conn: return jsonify({"error":"DB unavailable"}), 503
    filters, params = ["1=1"], []
    if level: filters.append("data->>'level'=%s"); params.append(level)
    if tag:   filters.append("tag ILIKE %s");      params.append(f'%{tag}%')
    if q:     filters.append("data::text ILIKE %s"); params.append(f'%{q}%')
    params.append(limit)
    cur = conn.cursor()
    cur.execute(f"SELECT tag,time,data FROM logs.fluentbit WHERE {' AND '.join(filters)} ORDER BY time DESC LIMIT %s", params)
    rows = cur.fetchall(); cur.close(); conn.close(); DB_CONNECTIONS.dec()
    return jsonify([{"tag":r[0],"time":r[1].isoformat(),"data":r[2]} for r in rows])

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
