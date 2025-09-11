-- PostgreSQL 17.x SQL/JSON: JSON_TABLE 示例（占位）
-- 目标：演示 JSON_TABLE 抽取与列投影、类型与路径映射。

-- 准备数据
CREATE TEMP TABLE jt_src (id int, payload jsonb);
INSERT INTO jt_src VALUES
  (1, '{"items":[{"sku":"A","qty":2},{"sku":"B","qty":3}]}'),
  (2, '{"items":[{"sku":"C","qty":1}]}');

-- 示例占位（具体语法以 17.x 实际实现为准）：
-- 兼容性回退：若当前版本不支持 JSON_TABLE，可使用 jsonb_path_query/jsonb_to_recordset 替代。
-- 参考回退示例（可直接运行）：
SELECT (j->>'sku') AS sku, (j->>'qty')::int AS qty
FROM (
  SELECT jsonb_array_elements(payload->'items') AS j FROM jt_src
) AS t
ORDER BY sku;

-- 预期：输出 sku 与 qty 行展开结果，用于与传统 jsonb_path_query 对比。


