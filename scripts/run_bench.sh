#!/usr/bin/env bash
set -euo pipefail

export PG_URL=${PG_URL:-"postgres://postgres:postgres@localhost:5432/postgres"}
export NQ=${NQ:-1000}
export K=${K:-10}
export MODEL=${MODEL:-sentiment_analyzer}

python benchmarks/bench_stream.py > bench_stream.json
MODEL=$MODEL NQ=$NQ BATCH=4 python benchmarks/bench_inference.py > bench_infer.json

mkdir -p results
python benchmarks/aggregate_results.py results/all.csv bench_stream.json bench_infer.json
python benchmarks/plot_results.py bench_stream.json bench_infer.json

echo "bench_stream.json:" && cat bench_stream.json
echo "bench_infer.json:" && cat bench_infer.json
echo "results/all.csv:" && head -n 5 results/all.csv 