-- 常用诊断SQL清单（与 04.04/04.06 对齐）

-- 活跃会话
SELECT pid, usename, application_name, wait_event_type, wait_event, state, query
FROM pg_stat_activity WHERE state <> 'idle' ORDER BY query_start;

-- 锁与等待
SELECT locktype, relation::regclass, mode, granted, pid
FROM pg_locks WHERE NOT granted;

-- 表扫描/索引使用
SELECT schemaname, relname, seq_scan, idx_scan, n_tup_ins, n_tup_upd, n_tup_del
FROM pg_stat_user_tables ORDER BY (seq_scan+idx_scan) DESC;

-- I/O 命中
SELECT schemaname, relname,
       heap_blks_read, heap_blks_hit,
       round(100.0*heap_blks_hit/nullif(heap_blks_hit+heap_blks_read,0),2) AS hit_ratio
FROM pg_statio_user_tables ORDER BY hit_ratio ASC NULLS LAST;

-- 慢查询（需 pg_stat_statements）
SELECT query, calls, total_time, mean_time, rows,
       round(100.0*shared_blks_hit/nullif(shared_blks_hit+shared_blks_read,0),2) AS hit_percent
FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 20;


