import os
import time
import json
import random
import psycopg2
import numpy as np

PG_URL = os.environ.get("PG_URL", "postgres://postgres:postgres@localhost:5432/postgres")
EVENT_RATE = int(os.environ.get("EVENT_RATE", "2000"))  # events/sec
DURATION_S = int(os.environ.get("DURATION_S", "30"))
WINDOW_SEC = int(os.environ.get("WINDOW_SEC", "60"))

conn = psycopg2.connect(PG_URL)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS user_events (
  user_id BIGINT,
  event_type TEXT,
  event_data JSONB,
  ts TIMESTAMPTZ
);
""")
conn.commit()

lat = []
start = time.time()
end = start + DURATION_S
batch = []

while time.time() < end:
    now = time.time()
    for _ in range(EVENT_RATE):
        uid = random.randint(1, 1000000)
        et = random.choice(["view", "click", "purchase"]) 
        ed = {"value": random.random()}
        batch.append((uid, et, json.dumps(ed), time.strftime('%Y-%m-%d %H:%M:%S%z', time.localtime(now))))
    args = ",".join(cur.mogrify("(%s,%s,%s,%s)", b).decode() for b in batch)
    cur.execute("INSERT INTO user_events (user_id, event_type, event_data, ts) VALUES " + args)
    conn.commit()
    batch.clear()

    t0 = time.time()
    cur.execute(
        """
        SELECT COUNT(*)
        FROM user_events
        WHERE ts >= now() - INTERVAL '%s seconds'
        """,
        (WINDOW_SEC,)
    )
    _ = cur.fetchone()[0]
    lat.append((time.time() - t0) * 1000)

cur.close()
conn.close()

result = {
    "event_rate": EVENT_RATE,
    "duration_s": DURATION_S,
    "window_sec": WINDOW_SEC,
    "p50_ms": float(np.percentile(lat, 50)) if lat else 0.0,
    "p95_ms": float(np.percentile(lat, 95)) if lat else 0.0,
    "p99_ms": float(np.percentile(lat, 99)) if lat else 0.0,
    "avg_ms": float(np.mean(lat)) if lat else 0.0,
}
print(json.dumps(result, ensure_ascii=False)) 