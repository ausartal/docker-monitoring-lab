"""
Log Generator — mensimulasikan log dari aplikasi production.
Menghasilkan log JSON ke stdout. Docker fluentd driver menangkap
dan mengirim ke Fluent Bit → PostgreSQL.
"""
import json, time, random, socket, datetime, os

HOSTNAME = socket.gethostname()
LOG_INTERVAL = float(os.environ.get("LOG_INTERVAL", "2"))

EVENTS = [
    {"level": "INFO",     "weight": 50, "messages": [
        "User login successful",
        "Page /dashboard loaded in {ms}ms",
        "API request GET /api/users completed",
        "Session created for user_{uid}",
        "Cache hit for key: product_{pid}",
        "Health check passed",
        "Background job completed: email_send"
    ]},
    {"level": "DEBUG",    "weight": 20, "messages": [
        "Database query executed in {ms}ms",
        "Redis connection pool: {pool} active",
        "Request headers: content-type=application/json",
        "Middleware chain completed in {ms}ms"
    ]},
    {"level": "WARN",     "weight": 15, "messages": [
        "Slow query detected: {ms}ms (threshold: 1000ms)",
        "Memory usage at {mem}% — approaching limit",
        "Rate limit approaching for IP 192.168.{ip}.{host}",
        "Deprecated API endpoint called: /api/v1/legacy",
        "Certificate expires in {days} days"
    ]},
    {"level": "ERROR",    "weight": 10, "messages": [
        "Failed to connect to database: timeout after 5s",
        "NullPointerException in UserService.getProfile()",
        "HTTP 500 Internal Server Error on /api/checkout",
        "Disk write failed: /var/log/app.log — Permission denied",
        "Payment gateway returned error code {code}"
    ]},
    {"level": "CRITICAL", "weight": 5,  "messages": [
        "Database connection pool exhausted — all {pool} connections in use",
        "Out of memory: container killed by OOM",
        "SSL certificate EXPIRED — HTTPS unavailable",
        "Data corruption detected in table: orders"
    ]}
]

def weighted_choice():
    total = sum(e["weight"] for e in EVENTS)
    r = random.uniform(0, total)
    cumulative = 0
    for event in EVENTS:
        cumulative += event["weight"]
        if r <= cumulative:
            return event
    return EVENTS[0]

def generate_log():
    event = weighted_choice()
    msg = random.choice(event["messages"])
    msg = msg.format(
        ms=random.randint(5, 3000),
        uid=random.randint(1000, 9999),
        pid=random.randint(1, 500),
        pool=random.randint(1, 50),
        mem=random.randint(60, 98),
        ip=random.randint(1, 254),
        host=random.randint(1, 254),
        days=random.randint(1, 30),
        code=random.choice([400, 401, 403, 500, 502, 503])
    )
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "level": event["level"],
        "hostname": HOSTNAME,
        "service": "log-generator",
        "message": msg,
        "request_id": f"req-{random.randint(100000, 999999)}"
    }
    print(json.dumps(log_entry), flush=True)

if __name__ == "__main__":
    print(json.dumps({
        "timestamp": datetime.datetime.now().isoformat(),
        "level": "INFO", "hostname": HOSTNAME,
        "service": "log-generator",
        "message": f"Log generator started, interval={LOG_INTERVAL}s"
    }), flush=True)
    while True:
        generate_log()
        time.sleep(LOG_INTERVAL + random.uniform(-0.5, 0.5))
