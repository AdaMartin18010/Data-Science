Param(
  [string]$PgUrl = $env:PG_URL
)

if (-not $PgUrl) { $PgUrl = "postgres://postgres:postgres@localhost:5432/postgres" }
$env:PG_URL = $PgUrl
if (-not $env:NQ) { $env:NQ = "1000" }
if (-not $env:MODEL) { $env:MODEL = "sentiment_analyzer" }

python benchmarks/bench_stream.py | Out-File -FilePath bench_stream.json -Encoding utf8
python -c "import os;os.environ['MODEL']=os.environ.get('MODEL','sentiment_analyzer');os.environ['NQ']=os.environ.get('NQ','1000');os.environ['BATCH']='4';import benchmarks.bench_inference as b" | Out-Null
python benchmarks/bench_inference.py | Out-File -FilePath bench_infer.json -Encoding utf8

Write-Output "bench_stream.json:"; Get-Content bench_stream.json
Write-Output "bench_infer.json:"; Get-Content bench_infer.json 