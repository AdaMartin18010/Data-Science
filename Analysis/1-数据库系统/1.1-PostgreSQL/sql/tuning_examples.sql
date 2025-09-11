-- 调优示例SQL（与 04.06 对齐）

-- 扩展统计与 ANALYZE
ALTER TABLE t ALTER COLUMN c SET STATISTICS 2000;
CREATE STATISTICS s_t_multi (dependencies) ON c1, c2 FROM t;
ANALYZE t;

-- 表达式索引与谓词对齐
CREATE INDEX IF NOT EXISTS idx_t_lower_email ON t (lower(email));

-- 锁与等待排查
SELECT * FROM pg_locks l JOIN pg_stat_activity a USING(pid) WHERE NOT granted;

-- 膨胀处置
REINDEX TABLE CONCURRENTLY t;
VACUUM (VERBOSE, ANALYZE) t;


