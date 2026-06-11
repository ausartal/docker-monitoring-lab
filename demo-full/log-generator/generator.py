import time, random, json, sys
from datetime import datetime

LEVELS   = ['INFO']*50 + ['DEBUG']*20 + ['WARN']*15 + ['ERROR']*10 + ['CRITICAL']*5
SERVICES = ['auth-service','payment-service','api-gateway','user-service','notification-service']
MESSAGES = {
    'INFO':     ['Request processed successfully','User login successful','Cache hit','Health check passed'],
    'DEBUG':    ['DB query 12ms','Token validated','Cache miss','Config loaded'],
    'WARN':     ['High memory 78%','Slow query 1200ms','Retry 2/3'],
    'ERROR':    ['DB connection timeout','Payment failed','JWT expired'],
    'CRITICAL': ['Out of memory','DB cluster down','All retries exhausted'],
}
while True:
    lvl = random.choice(LEVELS)
    print(json.dumps({"timestamp":datetime.utcnow().isoformat(),"level":lvl,
                      "service":random.choice(SERVICES),"message":random.choice(MESSAGES[lvl]),
                      "request_id":f"req-{random.randint(10000,99999)}",
                      "duration_ms":random.randint(5,2000)}), flush=True)
    time.sleep(random.uniform(0.5,2.5))
