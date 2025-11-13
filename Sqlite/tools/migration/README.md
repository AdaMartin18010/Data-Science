# SQLite 迁移工具

> **工具类型**：迁移工具
> **适用版本**：SQLite 3.31+ → PostgreSQL 12+

---

## 📋 工具列表

### 迁移辅助工具

- [01-迁移前检查.py](./01-迁移前检查.py) - ✅ 已创建
  - 检查SQLite数据库结构
  - 识别迁移风险点
  - 生成迁移报告

- [02-数据类型分析.py](./02-数据类型分析.py) - ✅ 已创建
  - 分析SQLite数据类型使用情况
  - 生成PostgreSQL类型映射建议
  - 识别类型转换风险

- [03-迁移脚本生成器.py](./03-迁移脚本生成器.py) - ✅ 已创建
  - 自动生成PostgreSQL DDL
  - 生成数据迁移脚本
  - 生成索引和约束脚本

---

## 🎯 使用说明

### 运行迁移前检查

```bash
python 01-迁移前检查.py database.db
```

### 分析数据类型

```bash
python 02-数据类型分析.py database.db
```

### 生成迁移脚本

```bash
python 03-迁移脚本生成器.py database.db --output migration.sql
```

---

## 📚 相关资源

- [10.01 SQLite到PostgreSQL迁移指南](../../10-迁移指南/10.01-SQLite到PostgreSQL迁移指南.md)
- [02.01 数据类型系统](../../02-数据模型/02.01-数据类型系统.md)

---

**维护者**：Data-Science Team
