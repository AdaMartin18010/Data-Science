---
title: README
slug: README
tags: []
pg_version: 16
status: draft
last_review: 2025-09-12
owner: TBD
---

# Feature Benchmarks (PostgreSQL 17.x)

占位目录：记录针对 17.x 特性的微基准方法与观测要点。

建议条目：

- vacuum_memory_throughput.md
- in_clause_btree.md
- brin_parallel_build.md

观测建议：

- 记录配置（shared_buffers、work_mem、maintenance_work_mem、wal相关）、数据规模、版本信息。
- 使用 `EXPLAIN (ANALYZE, BUFFERS, WAL, SUMMARY)` 与 `pg_stat_io`/`pg_stat_statements` 做支撑。

## 运行指引（占位）

```bash
# 生成数据（示意）
psql -v ON_ERROR_STOP=1 -c "CREATE TABLE t(id bigint primary key, v int);"
psql -c "INSERT INTO t SELECT g, (random()*1000)::int FROM generate_series(1,1000000) g;"
psql -c "CREATE INDEX ON t(v);"

# 采集计划与指标
psql -c "EXPLAIN (ANALYZE, BUFFERS, WAL, SUMMARY) SELECT * FROM t WHERE v IN (1,2,3,4,5);"

# 采集 Top SQL（需启用 pg_stat_statements）
psql -c "SELECT queryid, calls, total_exec_time FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;"
```

## 结果记录模板（占位）

- 硬件/系统/版本：
- 配置差异：
- 数据规模与分布：
- 查询/操作：
- 关键指标（时延、吞吐、WAL、IO）：
- 结论与建议：
