# 04 多模一体化（JSONB / 时序 / 图 / 向量）

> 最后更新：2025-10-31 · 核验来源：PostgreSQL Docs、Timescale、Apache AGE、pgvector

## 核心结论

- PostgreSQL 通过 JSONB、Timescale（时序）、Apache AGE（图）、pgvector（向量）形成“一库多模”。
- 统一 SQL/事务与权限模型，降低多库运维成本与跨库 ETL 复杂度。

## 能力与边界

- JSONB：灵活半结构化建模，PostgreSQL 18 对并行 text 处理有优化（以官方文档为准）。
- Timescale：分区/压缩/连续聚合；适合高吞吐时序写入与近实时分析。
- Apache AGE：图查询（OpenCypher 方言）；适合关系挖掘与路径分析。
- pgvector：ANN 检索（IVF/HNSW 视版本）；适合语义检索与向量关联。

## 组合建模

- 业务实体主表：结构化字段 + JSONB 扩展字段。
- 时序侧表：以设备/用户为分区键，与主表共享标识符。
- 向量表：对文本/图像/日志嵌入，存储向量与源主键；与主表/时序表 JOIN。
- 图侧：高价值关系（用户-设备-告警-事件）抽取为图边与点，实现反欺诈/溯源。

## 示例 SQL 片段（示意）

```sql
-- JSONB 属性查询
SELECT id FROM entity WHERE attrs ->> 'category' = 'premium';

-- 时序 + 向量联合
SELECT t.device_id
FROM metrics t
JOIN embeddings e ON e.device_id = t.device_id
WHERE e.embedding <-> $1 < 0.4 AND t.ts > now() - interval '15 min';
```

## 最佳实践

- 共分区/共簇策略：减少跨分区 JOIN；为混合查询设计复合索引。
- 明确冷热分层：热数据保留在主库，冷数据归档或外部表。

## 风险与缓解

- 资源竞争：混合负载需设置资源隔离与查询限流。
- 调优复杂：按查询模式回推索引策略，避免一库全能导致不可控。

## 参考链接（2025-10-31 核验）

- PostgreSQL 文档：`https://www.postgresql.org/docs/`
- Timescale（时序）：`https://docs.timescale.com/`
- Apache AGE（图）：`https://age.apache.org/`
- pgvector（向量）：`https://github.com/pgvector/pgvector`

# 04 多模一体化（JSONB / 时序 / 图 / 向量）

> 最后更新：2025-10-31 · 核验来源：PostgreSQL/Timescale/Apache AGE/pgvector 官方资源

## 能力地图

- JSONB：半结构化数据，索引与写入/查询权衡。
- 时序（TimescaleDB）：压缩、连续聚合、分区、保留策略。
- 图（Apache AGE）：图模型/查询语言（openCypher 方言）。
- 向量（pgvector）：相似度检索与混合查询。

## 组合场景

- 时序 + 向量：异常检测、设备画像检索。
- 图 + 向量：实体检索 + 近邻召回联合。
- JSONB + 向量：文档检索 + 结构化过滤。

## 参考链接

- PostgreSQL 文档：`https://www.postgresql.org/docs/`
- Timescale：`https://docs.timescale.com/`
- Apache AGE：`https://age.apache.org/`
- pgvector：`https://github.com/pgvector/pgvector`
