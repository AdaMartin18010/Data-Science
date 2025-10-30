# IN 子句 + B-Tree 优化微基准（占位）

## 目的

评估 17.x 对 B-Tree 上 IN 子句查询的优化收益。

## 环境记录

- 版本：PostgreSQL 17.x
- 索引：B-Tree on int/bigint，数据分布：均匀/Zipf 对比

## 步骤（示意）

1. 生成 1e7 规模主表，建 B-Tree 索引
2. 随机/热点 key 列表 size=10/100/1000 的 IN 查询
3. 对比不同 enable_*、work_mem、bitmap 开关下的执行

## 观测指标

- 执行时间、buffers 命中、WAL、计划形态
