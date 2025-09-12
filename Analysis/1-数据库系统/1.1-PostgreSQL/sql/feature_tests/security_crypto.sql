-- Crypto Feature Test (pgcrypto symmetric encryption)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$ BEGIN PERFORM set_config('app.encryption_key', 'ReplaceWithStrongKey', false); END $$;

CREATE SCHEMA IF NOT EXISTS ft_sec;
SET search_path TO ft_sec, public;

DROP TABLE IF EXISTS enc_users CASCADE;
CREATE TABLE enc_users (
  id BIGSERIAL PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  encrypted_email BYTEA NOT NULL
);

CREATE OR REPLACE FUNCTION enc(v TEXT)
RETURNS BYTEA AS $$
DECLARE k TEXT := current_setting('app.encryption_key', true); BEGIN
  IF k IS NULL THEN RAISE EXCEPTION 'app.encryption_key 未设置'; END IF;
  RETURN pgp_sym_encrypt(v, k);
END;$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION dec(v BYTEA)
RETURNS TEXT AS $$
DECLARE k TEXT := current_setting('app.encryption_key', true); BEGIN
  IF k IS NULL THEN RAISE EXCEPTION 'app.encryption_key 未设置'; END IF;
  RETURN pgp_sym_decrypt(v, k);
END;$$ LANGUAGE plpgsql;

INSERT INTO enc_users(username, encrypted_email)
VALUES ('alice', enc('alice@example.com')),
       ('bob',   enc('bob@example.com'));

SELECT id, username, dec(encrypted_email) AS email FROM enc_users ORDER BY id;

