-- PostgreSQL 17.x 逻辑复制改进：订阅/复制槽/故障切换（占位）

-- 注意：以下为演示脚本骨架，请根据实际环境调整连接与权限。

-- 发布端
-- CREATE PUBLICATION pub_all FOR ALL TABLES;

-- 订阅端（支持新版创建体验）
-- SELECT pg_create_logical_replication_slot('slot_app', 'pgoutput');
-- CREATE SUBSCRIPTION sub_app
--   CONNECTION 'host=... dbname=... user=... password=...'
--   PUBLICATION pub_all
--   WITH (copy_data = true);

-- 故障切换与重建（示意，17.x 提升了流程顺畅度）
-- ALTER SUBSCRIPTION sub_app ENABLE;
-- ALTER SUBSCRIPTION sub_app REFRESH PUBLICATION;


