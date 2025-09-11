-- 复制/高可用监控SQL

-- 复制状态与延迟
SELECT application_name, state, sync_state,
       pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS byte_lag,
       write_lag, flush_lag, replay_lag
FROM pg_stat_replication;

-- 复制槽
SELECT slot_name, plugin, slot_type, active, restart_lsn, confirmed_flush_lsn
FROM pg_replication_slots;

-- WAL 产生速率（需结合时间窗口统计）
SELECT now() AS ts, pg_current_wal_lsn();

-- 冲突与取消（只读副本）
SELECT confl_tablespace, confl_lock, confl_snapshot, confl_bufferpin, confl_deadlock
FROM pg_stat_database_conflicts;


