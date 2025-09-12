---
title: brin_parallel_build
slug: brin_parallel_build
tags: []
pg_version: 16
status: draft
last_review: 2025-09-12
owner: TBD
---

# BRIN 并行构建微基准（占位）

## 目的

对比串行/并行构建 BRIN 索引的时间与资源使用。

## 环境记录

- 版本：PostgreSQL 17.x
- 分区：按时间/范围分区的大表

## 步骤（示意）

1. 生成宽表含时间列，规模≥数十 GB
2. 分区后构建 BRIN（pages_per_range 不同设置），记录 `maintenance_work_mem`
3. 打开并行构建并记录并行度变化

## 观测指标

- 索引构建时间、IO、CPU、并行度与锁等待
