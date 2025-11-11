# pgbench 压测模板

## 1. 初始化

```bash
pgbench -i -s 10 postgres
```

## 2. 基线压测

```bash
pgbench -c 32 -j 32 -T 300 postgres
```

## 3. 自定义脚本（示例）

```sql
-- script.sql
\set aid random(1, 1000000)
SELECT * FROM pgbench_accounts WHERE aid = :aid;
```

```bash
pgbench -c 32 -j 32 -T 300 -f script.sql postgres
```

## 4. 记录与对比

- 保留 TPS/P95、系统资源（sar/iostat）、PG 指标面板截图；
- 变更前/后同条件对比。
