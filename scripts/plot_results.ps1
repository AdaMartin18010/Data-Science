Param(
  [string[]]$Inputs
)
if (-not $Inputs -or $Inputs.Count -eq 0) {
  $Inputs = @('bench_stream.json','bench_infer.json')
}
if (-not (Test-Path results)) { New-Item -Path results -ItemType Directory | Out-Null }
python benchmarks/aggregate_results.py results/all.csv @Inputs
python benchmarks/plot_results.py @Inputs
Write-Output "Wrote results/all.csv and Plotly html charts (p50_ms.html, p95_ms.html, p99_ms.html, avg_ms.html, throughput_qps.html)" 