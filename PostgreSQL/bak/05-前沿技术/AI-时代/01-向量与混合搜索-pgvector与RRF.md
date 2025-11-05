# 01 向量与混合搜索（pgvector + RRF）

> 最后更新：2025-10-31 · 核验来源：pgvector GitHub、Supabase Blog、PostgreSQL 官方文档

## 核心结论

- PostgreSQL 通过 `pgvector` 提供向量相似搜索；索引与运算由扩展实现。
- “混合搜索”常见为 BM25/全文检索 + 语义检索的 RRF 融合，工程上常见于 Supabase/自建实现。
- **RRF（Reciprocal Rank Fusion）** 是混合搜索的核心算法，能有效融合不同检索方式的排序结果。

## 能力与边界

### pgvector 支持

- **数据类型**：`vector(n)`、`halfvec(n)`、`bit(n)`、`sparsevec(n)`
- **距离度量**：
  - `<->` L2 距离（欧几里得距离）
  - `<#>` 内积距离（负内积）
  - `<=>` 余弦距离
- **索引类型**：
  - **HNSW**（Hierarchical Navigable Small World）：高召回率，适合中小数据集（< 1000万向量）
  - **IVFFlat**（Inverted File with Flat compression）：快速构建，适合大数据集（> 1000万向量）
  - **SP-GiST**：适合稀疏向量
- **适用规模**：
  - 单机：百万到千万级向量（取决于内存）
  - 分布式：通过 Citus、pg_shard 等扩展支持更大规模

### 混合搜索边界

- **全文检索**：PostgreSQL 原生 `to_tsvector` + GIN 索引
- **向量检索**：pgvector 扩展
- **融合方式**：RRF、加权融合、交叉重排等

## 典型实现

### 1. 近似最近邻索引构建与参数调优

```sql
-- HNSW 索引（推荐用于高召回场景）
CREATE INDEX idx_docs_hnsw ON documents
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 参数说明：
-- m: 每层最大连接数（16-64，越大召回率越高但索引越大）
-- ef_construction: 构建时的搜索深度（64-200，越大质量越高但构建越慢）

-- IVFFlat 索引（适合大数据集）
CREATE INDEX idx_docs_ivf ON documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 参数说明：
-- lists: 聚类中心数（建议为 rows/1000 到 rows/10000）
-- 查询时需要设置：SET ivfflat.probes = 10; （1-lists，越大召回率越高）

-- 全文检索索引
CREATE INDEX idx_docs_fts ON documents
USING GIN (to_tsvector('english', title || ' ' || content));
```

### 2. 候选召回 + 精排二阶段检索

```sql
-- 第一阶段：向量召回 Top-N 候选
WITH vector_candidates AS (
    SELECT
        id,
        title,
        content,
        embedding <=> $1::vector AS distance,
        1 - (embedding <=> $1::vector) AS similarity
    FROM documents
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> $1::vector
    LIMIT 100  -- 召回更多候选
)
-- 第二阶段：全文检索筛选
SELECT
    vc.id,
    vc.title,
    vc.content,
    vc.similarity,
    ts_rank(
        to_tsvector('english', vc.title || ' ' || vc.content),
        plainto_tsquery('english', $2)
    ) AS text_rank
FROM vector_candidates vc
WHERE to_tsvector('english', vc.title || ' ' || vc.content)
      @@ plainto_tsquery('english', $2)
ORDER BY vc.similarity DESC, text_rank DESC
LIMIT 10;
```

### 3. RRF 融合（BM25 与向量相似度融合）

RRF（Reciprocal Rank Fusion）通过倒数排名融合多个检索结果，公式为：

```text
RRF_score(d) = Σ(1 / (k + rank_i(d)))
```

其中 `k` 是常数（通常为 60），`rank_i(d)` 是文档 `d` 在第 `i` 个检索结果中的排名。

#### 完整 RRF 实现示例

```sql
-- 步骤1：向量相似度检索（带排名）
WITH vector_results AS (
    SELECT
        id,
        title,
        content,
        embedding <=> $1::vector AS distance,
        ROW_NUMBER() OVER (ORDER BY embedding <=> $1::vector) AS vec_rank
    FROM documents
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> $1::vector
    LIMIT 100
),
-- 步骤2：全文检索（BM25 排名）
fulltext_results AS (
    SELECT
        id,
        title,
        content,
        ts_rank(
            to_tsvector('english', title || ' ' || content),
            plainto_tsquery('english', $2)
        ) AS text_score,
        ROW_NUMBER() OVER (
            ORDER BY ts_rank(
                to_tsvector('english', title || ' ' || content),
                plainto_tsquery('english', $2)
            ) DESC
        ) AS text_rank
    FROM documents
    WHERE to_tsvector('english', title || ' ' || content)
          @@ plainto_tsquery('english', $2)
    LIMIT 100
),
-- 步骤3：RRF 融合（k=60）
rrf_scores AS (
    SELECT
        COALESCE(v.id, f.id) AS id,
        COALESCE(v.title, f.title) AS title,
        COALESCE(v.content, f.content) AS content,
        -- RRF 分数计算
        COALESCE(1.0 / (60.0 + v.vec_rank), 0) +
        COALESCE(1.0 / (60.0 + f.text_rank), 0) AS rrf_score,
        v.distance AS vec_distance,
        f.text_score AS fts_score
    FROM vector_results v
    FULL OUTER JOIN fulltext_results f ON v.id = f.id
)
-- 步骤4：按 RRF 分数排序
SELECT
    id,
    title,
    substring(content, 1, 100) AS content_preview,
    rrf_score,
    vec_distance,
    fts_score
FROM rrf_scores
WHERE rrf_score > 0
ORDER BY rrf_score DESC
LIMIT 20;
```

#### 简化版 RRF（PostgreSQL 函数封装）

```sql
-- 创建 RRF 融合函数
CREATE OR REPLACE FUNCTION reciprocal_rank_fusion(
    vec_rank INTEGER,
    text_rank INTEGER,
    k FLOAT DEFAULT 60.0
) RETURNS FLOAT AS $$
BEGIN
    RETURN
        COALESCE(1.0 / (k + vec_rank), 0) +
        COALESCE(1.0 / (k + text_rank), 0);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 使用函数简化查询
WITH vector_results AS (
    SELECT id, title, content,
           ROW_NUMBER() OVER (ORDER BY embedding <=> $1::vector) AS vec_rank
    FROM documents
    ORDER BY embedding <=> $1::vector
    LIMIT 100
),
fulltext_results AS (
    SELECT id, title, content,
           ROW_NUMBER() OVER (
               ORDER BY ts_rank(
                   to_tsvector('english', title || ' ' || content),
                   plainto_tsquery('english', $2)
               ) DESC
           ) AS text_rank
    FROM documents
    WHERE to_tsvector('english', title || ' ' || content)
          @@ plainto_tsquery('english', $2)
    LIMIT 100
)
SELECT
    COALESCE(v.id, f.id) AS id,
    COALESCE(v.title, f.title) AS title,
    reciprocal_rank_fusion(v.vec_rank, f.text_rank) AS rrf_score
FROM vector_results v
FULL OUTER JOIN fulltext_results f ON v.id = f.id
ORDER BY rrf_score DESC
LIMIT 20;
```

## 性能优化建议

### 索引参数调优

```sql
-- HNSW 索引参数选择
-- 小数据集（< 10万）：m=16, ef_construction=64
-- 中等数据集（10万-100万）：m=32, ef_construction=128
-- 大数据集（> 100万）：考虑 IVFFlat 或分布式方案

-- IVFFlat 索引参数选择
-- lists = rows / 1000 到 rows / 10000
-- 查询时：SET ivfflat.probes = lists / 10; （平衡召回率和性能）
```

### 查询优化

```sql
-- 设置查询参数（IVFFlat 索引）
SET ivfflat.probes = 10;  -- 提升召回率，但会增加查询时间

-- 使用 EXPLAIN ANALYZE 分析性能
EXPLAIN ANALYZE
SELECT id FROM documents
ORDER BY embedding <=> $1::vector
LIMIT 10;
```

## 应用案例

### 电商商品搜索（Supabase 实践）

根据 Supabase 官方博客（2024），混合搜索提升转化率 **47%**：

- **技术栈**：pgvector + PostgreSQL 全文检索 + RRF
- **实现**：向量检索（商品描述嵌入）+ BM25（关键词匹配）
- **效果**：相比纯关键词搜索，转化率提升 47%

> 参考：Supabase Blog - "Hybrid Search with PostgreSQL and pgvector"
> 链接：<https://supabase.com/blog/hybrid-search>

## 参考链接（2025-10-31 核验）

### 官方文档

- **pgvector GitHub**：<https://github.com/pgvector/pgvector>
  - 最新版本：v0.7.0+（2025）
  - 支持的索引：HNSW、IVFFlat、SP-GiST
  - 距离操作符：`<->`、`<#>`、`<=>`

- **PostgreSQL 文档**：<https://www.postgresql.org/docs/>
  - 全文检索：<https://www.postgresql.org/docs/current/textsearch.html>
  - GIN 索引：<https://www.postgresql.org/docs/current/gin.html>

### 社区实践

- **Supabase Hybrid Search**：
  - 博客：<https://supabase.com/blog/hybrid-search>
  - 文档：<https://supabase.com/docs/guides/ai/hybrid-search>

- **RRF 算法论文**：
  - "Reciprocal Rank Fusion outperforms condorcet and individual rank learning methods" (2009)
  - 作者：Cormack, G. V., Clarke, C. L., & Buettcher, S.

### 性能基准

- **pgvector 性能测试**：<https://github.com/pgvector/pgvector#benchmarks>
- **向量数据库对比**：<https://benchmark.vectorview.ai/>

> 注：具体索引类型与性能数据请以上述官方链接当日内容为准。
