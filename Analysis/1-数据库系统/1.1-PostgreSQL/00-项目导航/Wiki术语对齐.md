---
title: Wiki术语对齐
slug: Wiki术语对齐
tags: []
pg_version: 16
status: draft
last_review: 2025-09-12
owner: TBD
---

# Wiki 术语与条目对齐（占位）

## 术语规范

| 英文 | 中文 | 备注 |
|---|---|---|
| MVCC | 多版本并发控制 | 与隔离级别术语统一 |
| WAL | 预写式日志 | 与 ARIES 关系表述统一 |
| Logical Replication | 逻辑复制 | 与订阅/发布、复制槽一致 |
| Partition Pruning | 分区裁剪 | 与等价性与代价模型术语一致 |
| SQL/JSON | SQL/JSON | 引用标准功能名（JSON_TABLE等） |
| RLS | 行级安全 | 策略与不可逃逸性一致 |

## 条目→文档映射

| 条目 | 仓内映射 | 缺口 | 状态 |
|---|---|---|---|
| SQL/JSON（JSON_TABLE） | `1.1.98`、`1.1.21` | 示例 SQL 与等价性讨论 | 待办 |
| MERGE（RETURNING/可更新视图） | `1.1.144` | 示例 SQL 与与触发器交互 | 待办 |
| MVCC/隔离级别 | `1.1.47`、`1.1.61` | 17.x 行为核对 | 进行中 |
| 逻辑复制 | `1.1.65` | 订阅/槽 改进与一致性不变式 | 待办 |
| 分区与裁剪 | `1.1.59` | 基准与观测 | 待办 |

### 行动项（占位）

- 统一术语：按术语表固化英文/中文与缩写使用（MVCC/WAL/SSI/RLS）
- 示例与反例：为 SQL/JSON 与 MERGE 增补等价/非等价示例与解释
- 可观测映射：将 Wiki 条目的运维侧观测指标绑定到 Runbook
