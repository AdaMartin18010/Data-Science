# 01 向量与混合搜索（pgvector + RRF）

> 最后更新：2025-10-31 · 核验来源：pgvector GitHub、Supabase Blog

## 核心结论

- PostgreSQL 通过 `pgvector` 提供向量相似搜索；索引与运算由扩展实现。
- “混合搜索”常见为 BM25/全文检索 + 语义检索的 RRF 融合，工程上常见于 Supabase/自建实现。

## 能力与边界

- 支持的数据类型与距离：L2、内积、余弦等（以 `pgvector` 官方为准）。
- 支持的索引：常见为 IVF/（HNSW 取决于版本与实现），以官方发布为准。
- 适用规模：单机/分布式（Citus 等）下的工程边界与注意事项。

## 典型实现

- 近似最近邻索引构建与参数调优
- 候选召回 + 精排二阶段检索
- RRF 融合（BM25 与向量相似度融合）

## 示例 SQL

```sql
-- 示例：向量相似 Top-k（以 pgvector 官方示例为准）
SELECT id
FROM items
ORDER BY embedding <-> $1
LIMIT 10;
```

## 参考链接（2025-10-31 核验）

- pgvector（GitHub）：`https://github.com/pgvector/pgvector`
- Supabase Hybrid Search/RRF：`https://supabase.com/blog`
- PostgreSQL 文档：`https://www.postgresql.org/docs/`

> 注：具体索引类型与性能数据请以上述官方链接当日内容为准。
