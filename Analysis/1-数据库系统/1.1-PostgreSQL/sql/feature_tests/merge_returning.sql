-- PostgreSQL 17.x MERGE RETURNING 示例（占位）

CREATE TEMP TABLE inv (sku text primary key, qty int);
INSERT INTO inv VALUES ('A', 5), ('B', 0);

CREATE TEMP TABLE patch (sku text, delta int);
INSERT INTO patch VALUES ('A', 1), ('C', 2);

-- 示例：MERGE ... RETURNING 受影响行（具体语法以 17.x 实际实现为准）
-- MERGE INTO inv USING patch ON (inv.sku = patch.sku)
-- WHEN MATCHED THEN UPDATE SET qty = inv.qty + patch.delta
-- WHEN NOT MATCHED THEN INSERT (sku, qty) VALUES (patch.sku, patch.delta)
-- RETURNING *;

-- 兼容性回退（可直接运行）：
INSERT INTO inv AS t (sku, qty)
SELECT sku, delta FROM patch
ON CONFLICT (sku) DO UPDATE SET qty = t.qty + EXCLUDED.qty
RETURNING *;


