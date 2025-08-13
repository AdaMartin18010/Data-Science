import sys, json, csv

if len(sys.argv) < 3:
    print("Usage: python aggregate_results.py output.csv input1.json [input2.json ...]")
    sys.exit(1)

out = sys.argv[1]
ins = sys.argv[2:]
rows = []
for p in ins:
    with open(p, 'r', encoding='utf-8') as f:
        try:
            obj = json.load(f)
            obj['source'] = p
            rows.append(obj)
        except Exception:
            pass

# Collect header keys
keys = set()
for r in rows:
    keys.update(r.keys())
keys = list(keys)

with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=keys)
    w.writeheader()
    for r in rows:
        w.writerow(r)

print(f"Wrote {len(rows)} rows to {out}") 