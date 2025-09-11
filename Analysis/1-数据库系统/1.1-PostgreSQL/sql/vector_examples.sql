-- 向量与混合检索示例

CREATE EXTENSION IF NOT EXISTS vector;

-- 基础表
CREATE TABLE IF NOT EXISTS docs (
  id bigserial PRIMARY KEY,
  text text,
  embedding vector(768),
  created_at timestamptz DEFAULT now()
);

-- 索引
CREATE INDEX IF NOT EXISTS docs_hnsw ON docs USING hnsw (embedding vector_l2_ops) WITH (m=32, ef_construction=200);

-- 结构化 + 向量
WITH q AS (SELECT '[0.1,0.2,...]'::vector AS qv)
SELECT id, text FROM docs, q
WHERE created_at >= now() - interval '7 day'
ORDER BY embedding <-> q.qv
LIMIT 50;

-- 全文 + 向量融合
WITH s AS (
  SELECT id, ts_rank(to_tsvector('simple', text), plainto_tsquery('simple','postgres')) AS tr
  FROM docs
  WHERE to_tsvector('simple', text) @@ plainto_tsquery('simple','postgres')
  ORDER BY tr DESC LIMIT 500
), v AS (
  SELECT id, embedding <-> '[0.1,0.2,...]'::vector AS dist
  FROM docs WHERE id IN (SELECT id FROM s)
  ORDER BY dist ASC LIMIT 100
)
SELECT * FROM v ORDER BY dist ASC;


