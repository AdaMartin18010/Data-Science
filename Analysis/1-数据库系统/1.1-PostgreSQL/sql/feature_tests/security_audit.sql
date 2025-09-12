-- Audit Feature Test (pgaudit + trigger)
CREATE EXTENSION IF NOT EXISTS pgaudit;

CREATE SCHEMA IF NOT EXISTS ft_sec;
SET search_path TO ft_sec, public;

CREATE TABLE IF NOT EXISTS audit_log (
  id BIGSERIAL PRIMARY KEY,
  event_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  user_name TEXT,
  statement TEXT
);

CREATE OR REPLACE FUNCTION ft_audit_trg()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO audit_log(user_name, statement)
  VALUES (current_user, current_query());
  RETURN NEW;
END;$$ LANGUAGE plpgsql;

DROP TABLE IF EXISTS t CASCADE;
CREATE TABLE t(id BIGSERIAL PRIMARY KEY, v INT);
CREATE TRIGGER tr_audit AFTER INSERT OR UPDATE OR DELETE ON t
FOR EACH ROW EXECUTE FUNCTION ft_audit_trg();

INSERT INTO t(v) VALUES (1),(2);
UPDATE t SET v = v + 1 WHERE v = 1;
DELETE FROM t WHERE v = 3;

SELECT * FROM audit_log ORDER BY id;

