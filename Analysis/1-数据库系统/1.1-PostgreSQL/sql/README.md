# SQL 脚本索引

- diagnostics.sql：常用诊断
- tuning_examples.sql：调优示例
- vector_examples.sql：向量与混合检索示例
- graph_examples.sql：图与递归示例
- ha_monitoring.sql：复制与高可用监控
- security_examples.sql：安全与合规示例（RLS/审计/加密/GDPR/SOX/PCI）

## 执行说明（安全示例）

- 在会话中设置应用密钥（示例）：

```sql
SELECT set_config('app.encryption_key', 'ReplaceWithStrongKey', false);
```

- 加载必要扩展（如未启用）：

```sql
CREATE EXTENSION IF NOT EXISTS pgaudit;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

- 执行示例脚本：

```sql
\i security_examples.sql
```

注意：请在非生产环境验证，生产环境需结合密钥管理（KMS）、变更流程与审计策略。

## 统一执行与断言指引（沙箱/幂等/回滚）

### A. 沙箱 schema 与会话准备

```sql
-- 建议在沙箱中执行，避免污染业务对象
CREATE SCHEMA IF NOT EXISTS sandbox;
SET search_path = sandbox, public;

-- 强制异常中止，便于自动化断言
\set ON_ERROR_STOP on
```

### B. 幂等执行模式（推荐模板）

```sql
-- 对象创建：优先使用 IF NOT EXISTS / OR REPLACE
CREATE TABLE IF NOT EXISTS sandbox.events(id bigserial PRIMARY KEY);
CREATE OR REPLACE FUNCTION sandbox.f() RETURNS int LANGUAGE sql AS $$ SELECT 1 $$;

-- 变更/清理：使用 IF EXISTS，避免二次执行失败
DROP MATERIALIZED VIEW IF EXISTS sandbox.mv CASCADE;

-- 条件式DDL（需要复杂判断时）
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='sandbox' AND c.relname='idx_events_id'
  ) THEN
    EXECUTE 'CREATE INDEX idx_events_id ON sandbox.events(id)';
  END IF;
END$$;
```

### C. 最小化断言（快速校验）

```bash
psql -h localhost -U postgres -d postgres -v ON_ERROR_STOP=1 \
  -c "\\dn+ sandbox" \
  -c "\\dt+ sandbox.*" \
  -c "\\df+ sandbox.*" \
  -c "SELECT to_regclass('sandbox.events') IS NOT NULL AS has_events;"
```

### D. 一键执行（示例）

```bash
psql -h localhost -U postgres -d postgres -v ON_ERROR_STOP=1 -f "Analysis/1-数据库系统/1.1-PostgreSQL/sql/diagnostics.sql"
```

### E. 快速回滚（清理沙箱）

```sql
DROP SCHEMA IF EXISTS sandbox CASCADE;
```
