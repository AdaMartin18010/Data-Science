# SQLite术语标准化词典

> **创建日期**: 2025-12-05
> **版本**: v1.0
> **用途**: 统一SQLite知识库的术语使用

---

## 一、 📋 目录

- [SQLite术语标准化词典](#sqlite术语标准化词典)
  - [一、 📋 目录](#一--目录)
  - [SQLite核心术语](#sqlite核心术语)
    - [架构组件术语](#架构组件术语)
    - [数据模型术语](#数据模型术语)
    - [事务与并发术语](#事务与并发术语)
    - [配置与优化术语](#配置与优化术语)
  - [SQLite特有术语](#sqlite特有术语)
    - [模式与特性](#模式与特性)
    - [扩展与模块](#扩展与模块)
  - [易混淆术语辨析](#易混淆术语辨析)
    - [WAL vs Rollback Journal](#wal-vs-rollback-journal)
    - [Page vs Cell](#page-vs-cell)
    - [Database Lock vs Table Lock](#database-lock-vs-table-lock)
  - [版本相关术语](#版本相关术语)
    - [SQLite版本术语](#sqlite版本术语)
  - [性能术语](#性能术语)
    - [性能指标](#性能指标)
    - [优化术语](#优化术语)
  - [编程术语](#编程术语)
    - [API术语](#api术语)
    - [错误术语](#错误术语)
  - [缩写规范](#缩写规范)
  - [中英文对照表](#中英文对照表)
    - [A-E](#a-e)
    - [F-Z](#f-z)

## SQLite核心术语

### 架构组件术语

| 英文 | 标准中文 | 缩写 | 避免使用 | 说明 |
|------|---------|------|---------|------|
| VDBE | 虚拟数据库引擎 | - | 虚拟机 | Virtual Database Engine |
| Pager | 页面管理器 | - | 分页器 | 管理页面缓存和IO |
| VFS | 虚拟文件系统 | - | 文件系统 | Virtual File System |
| B-Tree | B树 | - | B+树 | SQLite使用B-Tree（非B+Tree） |
| WAL | 预写日志 | - | 写前日志 | Write-Ahead Logging |
| Rollback Journal | 回滚日志 | - | 撤销日志 | 回滚模式日志 |
| Shared Memory | 共享内存 | - | 共享缓存 | WAL模式下的共享内存 |
| Checkpoint | 检查点 | - | 存盘点 | WAL同步到数据库 |

### 数据模型术语

| 英文 | 标准中文 | 避免 | 说明 |
|------|---------|------|------|
| Page | 页 | 页面 | 存储基本单位（默认4KB） |
| Cell | 单元格 | 单元 | B-Tree中的数据单元 |
| Overflow Page | 溢出页 | 溢出页面 | 存储大数据的额外页 |
| Freeblock | 空闲块 | 自由块 | 页面中的空闲空间 |
| Freelist | 空闲列表 | 自由列表 | 跟踪空闲页的链表 |

### 事务与并发术语

| 英文 | 标准中文 | 避免 | 说明 |
|------|---------|------|------|
| Database Lock | 数据库锁 | 文件锁 | 保护整个数据库的锁 |
| Shared Lock | 共享锁 | 读锁 | 允许多个读操作 |
| Reserved Lock | 保留锁 | 预留锁 | 准备写入的锁 |
| Pending Lock | 挂起锁 | 等待锁 | 等待升级的锁 |
| Exclusive Lock | 排他锁 | 写锁 | 独占写入的锁 |
| Snapshot Isolation | 快照隔离 | 快照 | WAL模式提供的隔离级别 |
| Read Uncommitted | 读未提交 | 未提交读 | 最低隔离级别（SQLite不支持） |

### 配置与优化术语

| 英文 | 标准中文 | 避免 | 说明 |
|------|---------|------|------|
| PRAGMA | 编译指示 | 配置 | SQLite配置命令 |
| Cache Size | 缓存大小 | 缓冲大小 | 页面缓存大小 |
| Page Size | 页面大小 | 页大小 | 数据库页面大小 |
| Journal Mode | 日志模式 | 日志类型 | WAL/Rollback Journal |
| Synchronous | 同步模式 | 同步级别 | 文件同步策略 |
| Auto Vacuum | 自动清理 | 自动压缩 | 自动回收空间 |

---

## SQLite特有术语

### 模式与特性

| 术语 | 中文 | 说明 |
|------|-----|------|
| In-Memory Database | 内存数据库 | `:memory:` 数据库 |
| Attached Database | 附加数据库 | ATTACH DATABASE |
| Temporary Table | 临时表 | 会话级临时表 |
| Virtual Table | 虚拟表 | FTS/RTREE等扩展表 |
| WITHOUT ROWID | 无行ID表 | 聚簇索引表 |
| STRICT Tables | 严格表 | SQLite 3.37+类型严格模式 |

### 扩展与模块

| 术语 | 中文 | 说明 |
|------|-----|------|
| FTS | 全文搜索 | Full-Text Search |
| RTREE | R树索引 | 空间索引 |
| JSON1 | JSON扩展 | JSON函数支持 |
| RBU | 增量备份 | Rebuild Utility |
| SQLAR | SQL归档 | SQL Archive |

---

## 易混淆术语辨析

### WAL vs Rollback Journal

```text
WAL vs Rollback Journal辨析
══════════════════════════════════════════════════════════════════════════════

WAL (Write-Ahead Logging):
• 预写日志模式
• 写入WAL文件，后同步到数据库
• 支持并发读
• SQLite 3.7.0+默认推荐

Rollback Journal:
• 回滚日志模式
• 写入前备份，失败时回滚
• 单写模式
• 传统模式，兼容性好

使用场景:
• 现代应用 → WAL
• 旧系统兼容 → Rollback Journal
• 高并发读 → WAL（必需）
• 单写场景 → 两者皆可
```

### Page vs Cell

```text
Page vs Cell辨析
══════════════════════════════════════════════════════════════════════════════

Page（页）:
• 存储基本单位
• 默认4KB
• 包含页面头+Cell指针数组+Cell内容
• 由Pager管理

Cell（单元格）:
• B-Tree中的数据单元
• 存储在页面内
• 包含键值+数据载荷
• 可能溢出到溢出页

关系:
• 1个Page包含多个Cell
• Cell是逻辑单元，Page是物理单元
• 大Cell可能跨多个Page（溢出）
```

### Database Lock vs Table Lock

```text
锁粒度辨析
══════════════════════════════════════════════════════════════════════════════

SQLite锁机制:
• 只有数据库级锁（Database Lock）
• 没有表级锁（Table Lock）
• 没有行级锁（Row Lock）

锁类型:
• SHARED: 读锁（多个读）
• RESERVED: 保留锁（准备写）
• PENDING: 挂起锁（等待升级）
• EXCLUSIVE: 排他锁（独占写）

为什么只有数据库锁？
• 简化设计
• 单写保证
• 避免死锁
• 性能权衡
```

---

## 版本相关术语

### SQLite版本术语

| 版本 | 发布日期 | 关键特性 |
|------|---------|---------|
| SQLite 3.0 | 2004-06 | 现代架构 |
| SQLite 3.7.0 | 2010-07 | WAL模式 |
| SQLite 3.8.0 | 2013-08 | 无行ID表 |
| SQLite 3.9.0 | 2015-10 | 部分索引 |
| SQLite 3.24.0 | 2018-06 | UPSERT |
| SQLite 3.31.0 | 2020-01 | 生成列 |
| SQLite 3.35.0 | 2021-03 | RETURNING子句 |
| SQLite 3.37.0 | 2021-11 | STRICT表 |
| SQLite 3.38.0 | 2022-02 | JSON函数增强 |
| SQLite 3.45.0 | 2024-01 | STRICT表增强 |
| SQLite 3.46.0 | 2024-05 | PRAGMA optimize增强、json_pretty() |
| SQLite 3.46.1 | 2024-08 | 最新稳定版（修复3.46.0问题） |

---

## 性能术语

### 性能指标

| 英文 | 中文 | 单位 | 说明 |
|------|-----|------|------|
| Query Time | 查询时间 | ms | 单次查询耗时 |
| Transaction Throughput | 事务吞吐量 | TPS | 每秒事务数 |
| Cache Hit Rate | 缓存命中率 | % | 页面缓存命中比例 |
| Write Amplification | 写入放大 | 倍数 | WAL写入放大 |
| Checkpoint Frequency | 检查点频率 | 次/秒 | WAL检查点频率 |

### 优化术语

| 英文 | 中文 | 说明 |
|------|-----|------|
| Query Plan | 查询计划 | EXPLAIN QUERY PLAN输出 |
| Sequential Scan | 顺序扫描 | 全表扫描 |
| Index Scan | 索引扫描 | 通过索引访问 |
| Index-Only Scan | 索引覆盖扫描 | 无需回表 |
| Temporary B-Tree | 临时B树 | 排序/分组临时结构 |

---

## 编程术语

### API术语

| 英文 | 中文 | 说明 |
|------|-----|------|
| Connection | 连接 | 数据库连接对象 |
| Statement | 语句 | 预编译SQL语句 |
| Cursor | 游标 | 查询结果游标 |
| Prepared Statement | 预编译语句 | 参数化查询 |
| Binding | 绑定 | 绑定参数值 |

### 错误术语

| 英文 | 中文 | 错误码 | 说明 |
|------|-----|--------|------|
| SQLITE_OK | 成功 | 0 | 操作成功 |
| SQLITE_BUSY | 忙 | 5 | 数据库被锁定 |
| SQLITE_LOCKED | 锁定 | 6 | 表被锁定 |
| SQLITE_CORRUPT | 损坏 | 11 | 数据库文件损坏 |
| SQLITE_FULL | 已满 | 13 | 磁盘空间不足 |
| SQLITE_CONSTRAINT | 约束 | 19 | 违反约束 |

---

## 缩写规范

```text
SQLite标准缩写
══════════════════════════════════════════════════════════════════════════════

核心组件:
• VDBE: Virtual Database Engine
• VFS: Virtual File System
• WAL: Write-Ahead Logging

日志模式:
• WAL: Write-Ahead Logging
• DELETE: Rollback Journal (DELETE模式)
• TRUNCATE: Rollback Journal (TRUNCATE模式)
• PERSIST: Rollback Journal (PERSIST模式)
• MEMORY: Rollback Journal (MEMORY模式)
• OFF: 无日志

同步模式:
• OFF: 不同步（危险）
• NORMAL: 正常同步（WAL推荐）
• FULL: 完全同步（安全）

索引类型:
• B-Tree: 标准B树索引
• FTS: Full-Text Search
• RTREE: 空间索引

扩展:
• FTS3/FTS4/FTS5: 全文搜索版本
• JSON1: JSON函数扩展
• RBU: Rebuild Utility
```

---

## 中英文对照表

### A-E

| English | 中文 | 语境 |
|---------|-----|------|
| Attach | 附加 | ATTACH DATABASE |
| Auto Vacuum | 自动清理 | PRAGMA auto_vacuum |
| B-Tree | B树 | 索引结构 |
| Binding | 绑定 | 参数绑定 |
| Cache | 缓存 | 页面缓存 |
| Cell | 单元格 | B-Tree数据单元 |
| Checkpoint | 检查点 | WAL检查点 |
| Connection | 连接 | 数据库连接 |
| Cursor | 游标 | 查询游标 |
| Database Lock | 数据库锁 | 并发控制 |
| Exclusive Lock | 排他锁 | 写锁 |
| FTS | 全文搜索 | Full-Text Search |

### F-Z

| English | 中文 | 语境 |
|---------|-----|------|
| Freeblock | 空闲块 | 页面空闲空间 |
| Freelist | 空闲列表 | 空闲页列表 |
| In-Memory | 内存 | 内存数据库 |
| Journal | 日志 | 事务日志 |
| MVCC | 多版本并发控制 | 并发机制 |
| Overflow Page | 溢出页 | 大数据存储 |
| Page | 页 | 存储单位 |
| Pager | 页面管理器 | 页面管理 |
| PRAGMA | 编译指示 | 配置命令 |
| Prepared Statement | 预编译语句 | 参数化查询 |
| Reserved Lock | 保留锁 | 准备写入 |
| Rollback Journal | 回滚日志 | 传统日志模式 |
| Shared Lock | 共享锁 | 读锁 |
| Snapshot Isolation | 快照隔离 | 隔离级别 |
| VDBE | 虚拟数据库引擎 | 执行引擎 |
| VFS | 虚拟文件系统 | 文件抽象 |
| WAL | 预写日志 | WAL模式 |
| WITHOUT ROWID | 无行ID | 聚簇索引表 |

---

**文档版本**: v1.0
**最后更新**: 2025-12-05
**术语总数**: 150+
