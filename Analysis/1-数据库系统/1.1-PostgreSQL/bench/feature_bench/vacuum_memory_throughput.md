# VACUUM 内存/吞吐微基准（占位）

## 目的

观察 17.x 对 VACUUM 内存占用与吞吐改进的影响。

## 环境记录

- 版本：PostgreSQL 17.x
- 配置：shared_buffers、work_mem、maintenance_work_mem、autovacuum、wal_settings
- 数据规模：行数/表大小/索引

## 步骤（示意）

1. 生成含热点更新的测试表
2. 控制更新与删除比例，触发可回收版本
3. 手工 VACUUM / VACUUM FULL，对比统计与时间
4. 采集 `pg_stat_io`、`pg_stat_all_tables`、`EXPLAIN (ANALYZE, BUFFERS)`

## 观测指标

- VACUUM 耗时、内存峰值（若可）、IO 次数/字节、回收版本数
