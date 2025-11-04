# 03 Serverless 与分支（Neon / Supabase）

> 最后更新：2025-10-31 · 核验来源：Neon Docs、Supabase Docs

## 核心结论

- Serverless 架构提供按量计费与自动缩扩容，适合 AI 应用的突发实验与并行任务。
- Branching（分支）用于数据版本管理，常与 RAG 语料/Embedding 实验绑定，实现“数据 Git”。

## 能力与边界

- 自动休眠/唤醒（Scale-to-Zero），需关注冷启动延迟与并发抖动。
- 分支复制与合并适合读多写少与离线批量合并；高并发强写场景需谨慎评估。

## 典型架构

- RAG 语料分支：每次 Embedding 或清洗策略变更即建分支，离线评估后再合并为主分支。
- Agent 实验分支：多 Agent/提示词/系统提示并行试验，隔离副作用，统一回滚策略。

## 建模与流程

- 以“项目/场景”为维度划分数据库或分支命名；对齐 Git 分支命名规范。
- 元数据表记录分支来源、Embedding 模型版本、清洗规则、评测指标等。

## 示例（伪 SQL/流程）

```text
neon branch create rag-emb-v3
# 运行数据导入与向量索引构建
neon branch diff rag-emb-v3 main
neon branch merge rag-emb-v3 main
```

## 最佳实践

- 将冷启动影响纳入 SLO，使用连接池与预热策略。
- 明确分支生命周期：创建-评估-合并/归档；避免无限分叉。

## 风险与缓解

- 冷启动与性能抖动：对交互式路径使用常驻实例或预热。
- 分支合并冲突：统一变更票据与合并窗口，严控写路径。

## 参考链接（2025-10-31 核验）

- Neon Docs（Serverless/Branching）：`https://neon.tech/docs`
- Supabase Docs（Database/Branching）：`https://supabase.com/docs`
- PostgreSQL 文档：`https://www.postgresql.org/docs/`

## 03 Serverless 与分支（Neon 与 Supabase）

> 最后更新：2025-10-31 · 核验来源：Neon Docs、Supabase Docs/Blog

## 能力概览

- Serverless：按需计费、自动伸缩、冷启动权衡。
- Branching（分支）：从某个时间点/快照创建可独立读写的分支，用于测试/A-B 实验/CI。

## AI/RAG 场景价值

- 数据/嵌入分支试验：不同切分/embedding/检索策略的 A/B 测试。
- 低成本实验：按需启动/销毁，搭配变更模板与回滚策略。

## 风险与边界

- 冷启动延迟与并发性能抖动。
- 分支合并与数据一致性流程设计。

## 参考链接

- Neon 文档：`https://neon.tech/docs`
- Supabase 文档/博客：`https://supabase.com/docs`, `https://supabase.com/blog`
