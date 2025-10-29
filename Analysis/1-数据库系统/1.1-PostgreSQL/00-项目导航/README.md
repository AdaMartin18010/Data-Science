# 1.1-PostgreSQL 项目导航

## 目录速览

- runbook：运维执行手册
  - 01-性能调优-变更闭环.md
  - 02-监控与诊断-落地指南.md
  - 03-集群与高可用-演练SOP.md
  - 04-向量检索与混合查询-落地指南.md
  - 05-图数据库与Cypher-落地指南.md
  - 06-日志与可观测性-落地指南.md
  - README.md（索引）
- spec：规范与模板
  - 参数模板与负载画像.md
  - 变更票据模板.md
  - README.md（索引）
- sql：常用SQL脚本
  - diagnostics.sql
  - tuning_examples.sql
  - vector_examples.sql
  - graph_examples.sql
  - ha_monitoring.sql
  - README.md（索引）
- bench：压测模板
  - pgbench-模板.md
  - 混合查询-基准模板.md
  - 复制延迟-基准模板.md
  - README.md（索引）
- cases：案例库
  - 性能问题-案例库.md
  - README.md（索引）

## 交叉引用

- `04-部署运维/04.06-性能调优实践.md`
- `04-部署运维/04.04-监控与诊断.md`
- `04-部署运维/04.02-集群部署与高可用.md`
- `03-高级特性/*`

## PostgreSQL 知识体系 - 导航

## 项目概览

- 目标：结构清晰、去重整合、易于维护的PostgreSQL知识库
- 模块：01 核心基础 · 02 查询处理 · 03 高级特性 · 04 部署运维 · 05 前沿技术 · 06 形式化理论 · 07 应用实践 · 08 工具资源

## 快速开始

- 阅读本README了解整体
- 使用 INDEX 导航主题
- 按“学习路径指南”循序渐进

## 重要入口

- INDEX.md（完整索引）
- 学习路径指南.md
- 贡献指南.md
- INDEX-入口.md（统一入口）
- INDEX-重构版.md（重构中的结构索引）
- 对齐追踪矩阵.md（课程/Wiki/版本特性→文档映射）

## 状态

- 重构：进行中
- 去重整合：按模块推进
- 归档计划：见 `99-归档/归档计划与映射.md`

## 版本与日期

- 版本：v2.0（重构完成）
- 日期：2025-09-11
