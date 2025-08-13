import os
import time
import json
import random
import string
import psycopg2
import numpy as np

PG_URL = os.environ.get("PG_URL", "postgres://postgres:postgres@localhost:5432/postgres")
NQ = int(os.environ.get("NQ", "1000"))
BATCH = int(os.environ.get("BATCH", "1"))
MODEL = os.environ.get("MODEL", "sentiment_analyzer")

conn = psycopg2.connect(PG_URL)
cur = conn.cursor()

texts = [
    "这款产品非常好用", "物流很快, 包装不错", "体验不佳, 需要改进",
    "客服响应及时", "性价比很高", "做工一般", "推荐给朋友了", "不会再次购买"
]

def rand_text():
    base = random.choice(texts)
    suffix = ''.join(random.choices(string.ascii_letters, k=8))
    return f"{base}-{suffix}"

lat = []
start = time.time()

for _ in range(0, NQ, BATCH):
    batch = [rand_text() for __ in range(min(BATCH, NQ))]
    t0 = time.time()
    if BATCH == 1:
        cur.execute(
            "SELECT * FROM ai_inference(%s, json_build_object('text', %s))",
            (MODEL, batch[0])
        )
        _ = cur.fetchall()
    else:
        args = ",".join(cur.mogrify("(ai_inference(%s, json_build_object('text', %s)))", (MODEL, t)).decode() for t in batch)
        cur.execute("SELECT * FROM (VALUES " + args + ") as t(res)")
        _ = cur.fetchall()
    lat.append((time.time() - t0) * 1000)

elapsed = time.time() - start
cur.close()
conn.close()

result = {
    "model": MODEL,
    "nq": NQ,
    "batch": BATCH,
    "throughput_qps": float(NQ / elapsed) if elapsed > 0 else 0.0,
    "p50_ms": float(np.percentile(lat, 50)) if lat else 0.0,
    "p95_ms": float(np.percentile(lat, 95)) if lat else 0.0,
    "p99_ms": float(np.percentile(lat, 99)) if lat else 0.0,
    "avg_ms": float(np.mean(lat)) if lat else 0.0,
}
print(json.dumps(result, ensure_ascii=False)) 