# 第八部分：编程技巧与实践

> **状态**：✅ 已完成
> **优先级**：P0（最高）

---

## 📑 目录

- [第八部分：编程技巧与实践](#第八部分编程技巧与实践)
  - [📑 目录](#-目录)
  - [📋 内容概览](#-内容概览)
  - [📚 文档列表](#-文档列表)
  - [🎯 学习目标](#-学习目标)
  - [🔗 相关资源](#-相关资源)

---

## 📋 内容概览

本部分提供SQLite的编程技巧、最佳实践和代码示例。

---

## 📚 文档列表

- [08.01 连接管理](./08.01-连接管理.md) - ✅ 已完成
  - 单连接最佳实践
  - 多线程共享（SQLITE_OPEN_FULLMUTEX）
  - 连接池配置
  - 内存数据库（`:memory:`）

- [08.02 事务管理](./08.02-事务管理.md) - ✅ 已完成
  - BEGIN/COMMIT/ROLLBACK模式
  - SAVEPOINT嵌套事务
  - 批量操作优化
  - 事务边界设计

- [08.03 查询优化](./08.03-查询优化.md) - ✅ 已完成
  - 预编译语句（sqlite3_prepare_v2）
  - 参数化查询防注入
  - EXPLAIN QUERY PLAN分析
  - 索引使用技巧

- [08.04 PRAGMA配置](./08.04-PRAGMA配置.md) - ✅ 已完成
  - journal_mode（WAL/DELETE/MEMORY）
  - synchronous（FULL/NORMAL/OFF）
  - cache_size / temp_store
  - foreign_keys / integrity_check

- [08.05 错误处理](./08.05-错误处理.md) - ✅ 已完成
  - 错误码体系
  - 异常恢复策略
  - 崩溃恢复机制
  - 最佳实践

- [08.06 Python使用指南](./08.06-Python使用指南.md) - ✅ 已完成
  - 标准库sqlite3使用
  - 异步库aiosqlite
  - ORM框架SQLAlchemy
  - 高级特性和最佳实践

- [08.07 JavaScript/TypeScript使用指南](./08.07-JavaScript-TypeScript使用指南.md) - ✅ 已完成
  - better-sqlite3（推荐）
  - node-sqlite3（异步）
  - sql.js（浏览器/WebAssembly）
  - TypeScript支持和ORM框架

- [08.08 Go使用指南](./08.08-Go使用指南.md) - ✅ 已完成
  - database/sql + go-sqlite3
  - modernc.org/sqlite（纯Go）
  - crawshaw.io/sqlite（低级API）
  - GORM集成

- [08.09 Rust使用指南](./08.09-Rust使用指南.md) - ✅ 已完成
  - rusqlite（推荐）
  - sqlx（异步）
  - 高级特性和ORM框架

- [08.10 C/C++使用指南](./08.10-C-C++使用指南.md) - ✅ 已完成
  - C语言原生API
  - C++封装和RAII
  - 高级特性和性能优化

---

## 🎯 学习目标

完成本部分学习后，您将能够：

1. 正确管理数据库连接和事务
2. 编写高效的SQL查询
3. 配置PRAGMA参数优化性能
4. 处理错误和异常情况
5. 在您熟悉的编程语言中使用SQLite（Python、JavaScript/TypeScript、Go、Rust、C/C++）
6. 选择合适的库和ORM框架
7. 应用最佳实践优化性能

---

## 🔗 相关资源

- [代码示例库](../examples/) - 实际代码示例
- [性能优化](../03-性能优化/) - 性能调优指南
- [应用场景](../04-应用场景/) - 实战案例

---

**完成时间**：2025-11-13
