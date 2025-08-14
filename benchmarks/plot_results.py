import sys, json, pandas as pd
import plotly.express as px

if len(sys.argv) < 2:
    print("Usage: python benchmarks/plot_results.py bench_stream.json [bench_infer.json ...]")
    sys.exit(1)

def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

rows = []
for p in sys.argv[1:]:
    try:
        r = load(p); r['source'] = p; rows.append(r)
    except Exception:
        pass

df = pd.DataFrame(rows)
for col in ['p50_ms','p95_ms','p99_ms','avg_ms','throughput_qps']:
    if col in df.columns:
        fig = px.bar(df, x='source', y=col, title=f'{col} by source')
        out = f'{col}.html'
        fig.write_html(out)
        print(f'Wrote {out}') 