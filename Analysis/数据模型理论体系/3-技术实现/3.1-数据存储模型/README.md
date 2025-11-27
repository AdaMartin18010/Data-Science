# 数据存储模型

## 1. 概述

数据存储模型关注数据在不同存储系统中的组织、管理与访问方式，是数据系统设计、性能优化和安全保障的基础。

## 2. 存储模型理论

- 数据持久化、结构化与非结构化存储
- 一致性、可用性、分区容错性（CAP理论）
- 数据冗余、分片、备份与恢复

## 3. 主流数据存储技术

### 3.1. 关系型数据库（RDBMS）

- 结构化数据、表结构、SQL查询
- 事务（ACID）、主外键、索引、视图
- 典型产品：MySQL、PostgreSQL、Oracle、SQL Server

#### 3.1.1. 关系型数据库建模示例

```python
import sqlite3
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE user (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)''')
cursor.execute('''INSERT INTO user (name, age) VALUES ('Alice', 30)''')
conn.commit()
```

### 3.2. NoSQL数据库

- 键值型、文档型、列族型、图数据库
- 弱一致性、灵活扩展、高可用
- 典型产品：Redis、MongoDB、Cassandra、Neo4j

#### 3.2.1. 文档型数据库建模示例

```python
from pymongo import MongoClient
client = MongoClient()
db = client['testdb']
db.user.insert_one({'name': 'Bob', 'age': 25})
```

### 3.3. 图数据库

- 节点、边、属性、图遍历
- 适用于社交网络、知识图谱、推荐系统
- 典型产品：Neo4j、JanusGraph

#### 3.3.1. 图数据库建模示例

```python
from py2neo import Graph, Node, Relationship
graph = Graph()
alice = Node('Person', name='Alice')
bob = Node('Person', name='Bob')
friend = Relationship(alice, 'FRIEND', bob)
graph.create(alice | bob | friend)
```

### 3.4. 时序数据库

- 时间序列数据、高效写入、压缩存储
- 适用于物联网、监控、金融行情
- 典型产品：InfluxDB、TimescaleDB、OpenTSDB

#### 3.4.1. 时序数据库建模示例

```python
from influxdb import InfluxDBClient
client = InfluxDBClient()
data = [{
    'measurement': 'temperature',
    'tags': {'location': 'room1'},
    'time': '2023-01-01T00:00:00Z',
    'fields': {'value': 22.5}
}]
client.write_points(data)
```

## 4. 数据存储架构设计

- 单体与分布式架构
- 数据分区、分片、复制
- 多模存储与数据湖

## 5. 工程实践与优化

- 存储性能调优（索引、缓存、分区）
- 数据一致性与高可用设计
- 数据备份、恢复与容灾

## 6. 最佳实践

- 选择合适的存储模型与技术
- 数据生命周期管理
- 存储安全与合规

## 7. 前沿发展

- 云原生数据库与Serverless存储
- 多模数据库与HTAP
- 数据湖与湖仓一体

## 8. 学习路径

1. 存储模型基础理论
2. 主流数据库技术
3. 存储架构设计与优化
4. 工程实践与案例
5. 前沿技术探索

## 9. 总结

数据存储模型为数据系统的高效管理、可靠存储和安全访问提供了理论基础和工程方法，是数据驱动应用的核心支撑。
