# 数据库架构设计实战：SQL与SQLite整合应用

> **创建日期**：2025-12-04
> **难度**：⭐⭐⭐⭐⭐
> **前置知识**：SQL标准、SQLite核心机制、系统架构设计
> **适用对象**：架构师、高级开发者

---

## 📋 文档说明

本文档展示如何在实际系统架构中整合使用PostgreSQL和SQLite，充分发挥各自优势。

---

## 📑 目录

- [数据库架构设计实战：SQL与SQLite整合应用](#数据库架构设计实战sql与sqlite整合应用)
  - [📋 文档说明](#-文档说明)
  - [📑 目录](#-目录)
  - [一、混合架构设计模式](#一混合架构设计模式)
    - [1.1 中心化+边缘化架构](#11-中心化边缘化架构)
    - [1.2 读写分离架构](#12-读写分离架构)
    - [1.3 缓存层架构](#13-缓存层架构)
  - [二、典型场景架构方案](#二典型场景架构方案)
    - [2.1 移动应用架构（在线+离线）](#21-移动应用架构在线离线)
    - [2.2 IoT边缘计算架构](#22-iot边缘计算架构)
    - [2.3 分布式系统本地缓存](#23-分布式系统本地缓存)
  - [三、数据同步策略](#三数据同步策略)
    - [3.1 全量同步](#31-全量同步)
    - [3.2 增量同步](#32-增量同步)
    - [3.3 冲突解决](#33-冲突解决)
  - [四、性能优化策略](#四性能优化策略)
    - [4.1 查询路由](#41-查询路由)
    - [4.2 缓存策略](#42-缓存策略)
  - [五、完整实现案例](#五完整实现案例)
    - [5.1 新闻App架构](#51-新闻app架构)
    - [5.2 协同办公系统](#52-协同办公系统)

---

## 一、混合架构设计模式

### 1.1 中心化+边缘化架构

```text
中心化+边缘化混合架构
══════════════════════════════════════════════════════════════════════════════

                    中心数据库（PostgreSQL 18）
                    ┌─────────────────────────┐
                    │  • 主数据存储           │
                    │  • MVCC并发控制         │
                    │  • 事务一致性保证       │
                    │  • 复杂查询分析         │
                    └───────────┬─────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                    ▼           ▼           ▼
            ┌──────────┐  ┌──────────┐  ┌──────────┐
            │ 移动端1  │  │ 移动端2  │  │ 移动端N  │
            │ SQLite   │  │ SQLite   │  │ SQLite   │
            │          │  │          │  │          │
            │ • 本地数据│  │ • 本地数据│  │ • 本地数据│
            │ • 离线支持│  │ • 离线支持│  │ • 离线支持│
            │ • 快速响应│  │ • 快速响应│  │ • 快速响应│
            └──────────┘  └──────────┘  └──────────┘

数据流：
• 下行（Server → Client）：PostgreSQL导出 → SQLite导入
• 上行（Client → Server）：SQLite收集 → PostgreSQL合并
• 冲突解决：时间戳/版本号/Last-Write-Wins

优势：
✅ 中心端强一致性（PostgreSQL ACID + MVCC）
✅ 边缘端高可用性（SQLite离线工作）
✅ 网络中断容忍
✅ 降低中心数据库压力
```

### 1.2 读写分离架构

```text
读写分离架构
══════════════════════════════════════════════════════════════════════════════

                        应用服务器
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
        ┌──────────────┐          ┌──────────────┐
        │ PostgreSQL   │          │ SQLite       │
        │ (Master)     │────复制─>│ (Read Replica)│
        │              │          │              │
        │ 写操作       │          │ 读操作       │
        │ • INSERT     │          │ • SELECT     │
        │ • UPDATE     │          │ • 报表查询   │
        │ • DELETE     │          │ • 数据导出   │
        └──────────────┘          └──────────────┘
              │                          ▲
              │ 定期导出                 │
              └──────────────────────────┘

实现方案：

-- PostgreSQL写入
BEGIN;
INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');
COMMIT;

-- 定期导出到SQLite（增量）
pg_dump --data-only --inserts \
        --table=users \
        --where="updated_at >= '2025-12-04 00:00:00'" \
        | sqlite3 replica.db

-- 应用层读取（从SQLite）
SELECT * FROM users WHERE id = ?;
-- 零网络延迟，极快响应

优势：
✅ 写操作集中到PostgreSQL（MVCC并发优势）
✅ 读操作分流到SQLite（减轻主库压力）
✅ 报表查询本地化（不影响主库性能）
✅ 成本低（SQLite无需额外服务器）
```

### 1.3 缓存层架构

```text
SQLite作为缓存层
══════════════════════════════════════════════════════════════════════════════

                        应用程序
                             │
                             ▼
                    ┌─────────────────┐
                    │  缓存查询逻辑   │
                    └────────┬────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
            在内存？      在SQLite？    在PostgreSQL？
                │            │            │
              YES           YES           YES
                │            │            │
                ▼            ▼            ▼
            返回结果    返回结果+更新   查询+写SQLite+返回
                         内存缓存

数据层次：
L1缓存（内存）: 热点数据，TTL=1分钟
L2缓存（SQLite）: 常用数据，TTL=1小时
L3持久化（PostgreSQL）: 全量数据

-- Python实现
class HybridCache:
    def __init__(self):
        self.memory_cache = {}  # L1
        self.sqlite_conn = sqlite3.connect(':memory:')  # L2
        self.pg_conn = psycopg2.connect(...)  # L3

    def get_user(self, user_id):
        # L1: 内存缓存
        if user_id in self.memory_cache:
            return self.memory_cache[user_id]

        # L2: SQLite缓存
        row = self.sqlite_conn.execute(
            "SELECT * FROM users WHERE id=?", (user_id,)
        ).fetchone()
        if row:
            self.memory_cache[user_id] = row  # 写回L1
            return row

        # L3: PostgreSQL主库
        cursor = self.pg_conn.execute(
            "SELECT * FROM users WHERE id=%s", (user_id,)
        )
        row = cursor.fetchone()
        if row:
            # 写回L2
            self.sqlite_conn.execute(
                "INSERT OR REPLACE INTO users VALUES (?,?,?)", row
            )
            # 写回L1
            self.memory_cache[user_id] = row

        return row

性能对比：
• L1命中: ~0.1ms
• L2命中: ~1ms
• L3命中: ~5-10ms（网络）
• 命中率: L1(60%) + L2(35%) + L3(5%)
• 平均延迟: 0.1*0.6 + 1*0.35 + 7*0.05 = 0.76ms
```

---

## 二、典型场景架构方案

### 2.1 移动应用架构（在线+离线）

```text
移动App混合架构
══════════════════════════════════════════════════════════════════════════════

手机App（Flutter/React Native）
├── 本地SQLite数据库
│   ├── 用户个人数据（profiles.db）
│   ├── 离线内容缓存（cache.db）
│   └── 待同步操作队列（sync_queue.db）
│
├── 网络层
│   ├── HTTP API客户端
│   └── WebSocket（实时通知）
│
└── 云端PostgreSQL
    ├── 中心用户数据库
    ├── 内容管理系统
    └── 分析数据仓库

数据流向：

1. 启动时全量同步（首次）
   PostgreSQL → JSON API → 解析 → SQLite批量INSERT

2. 运行时增量同步（后台）
   SQLite查询last_sync_timestamp
   → API请求WHERE updated_at > last_sync
   → SQLite UPSERT

3. 离线操作队列
   用户修改 → INSERT INTO sync_queue
   → 网络恢复时批量上传 → PostgreSQL处理
   → 清理sync_queue

4. 实时推送
   PostgreSQL触发器 → 通知服务 → WebSocket → App更新SQLite
```

**完整实现（Flutter + Python）**：

```dart
// Flutter客户端
class DatabaseService {
  late Database _db;

  Future<void> init() async {
    _db = await openDatabase(
      'app.db',
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            synced INTEGER DEFAULT 0
          )
        ''');
        await db.execute('''
          CREATE TABLE sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            operation TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL,
            synced INTEGER DEFAULT 0
          )
        ''');

        // 配置WAL模式
        await db.execute('PRAGMA journal_mode=WAL');
        await db.execute('PRAGMA synchronous=NORMAL');
      },
    );
  }

  // 离线操作：加入同步队列
  Future<void> updateUserOffline(int id, String name) async {
    await _db.transaction((txn) async {
      // 更新本地数据
      await txn.update('users', {'name': name}, where: 'id = ?', whereArgs: [id]);

      // 加入同步队列
      await txn.insert('sync_queue', {
        'table_name': 'users',
        'operation': 'UPDATE',
        'data': json.encode({'id': id, 'name': name}),
        'created_at': DateTime.now().toIso8601String(),
      });
    });
  }

  // 后台同步
  Future<void> syncToServer() async {
    if (!await isOnline()) return;

    // 获取待同步操作
    final pending = await _db.query(
      'sync_queue',
      where: 'synced = 0',
      orderBy: 'id ASC',
    );

    for (final op in pending) {
      try {
        // HTTP请求到服务器
        await api.syncOperation(
          op['table_name'],
          op['operation'],
          json.decode(op['data']),
        );

        // 标记已同步
        await _db.update(
          'sync_queue',
          {'synced': 1},
          where: 'id = ?',
          whereArgs: [op['id']],
        );
      } catch (e) {
        print('同步失败: $e');
        break;  // 停止同步，等待下次重试
      }
    }

    // 清理已同步记录（保留7天）
    await _db.delete(
      'sync_queue',
      where: 'synced = 1 AND created_at < ?',
      whereArgs: [DateTime.now().subtract(Duration(days: 7)).toIso8601String()],
    );
  }
}
```

```python
# Python服务端（FastAPI）
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import psycopg2

app = FastAPI()

# PostgreSQL连接
pg_engine = create_engine('postgresql://user:pass@localhost/mydb')

@app.post("/sync/pull")
async def pull_sync(last_sync: str, user_id: int):
    """客户端拉取更新"""
    with Session(pg_engine) as session:
        # 查询自last_sync以来的更新
        users = session.execute("""
            SELECT id, name, email, updated_at
            FROM users
            WHERE user_id = :user_id
                AND updated_at > :last_sync
            ORDER BY updated_at
        """, {"user_id": user_id, "last_sync": last_sync}).fetchall()

        return {"users": [dict(u) for u in users]}

@app.post("/sync/push")
async def push_sync(operations: list):
    """客户端推送更新"""
    with Session(pg_engine) as session:
        try:
            for op in operations:
                if op['operation'] == 'UPDATE':
                    session.execute("""
                        UPDATE users
                        SET name = :name, updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                    """, op['data'])
                elif op['operation'] == 'INSERT':
                    session.execute("""
                        INSERT INTO users (id, name, email)
                        VALUES (:id, :name, :email)
                        ON CONFLICT (id) DO UPDATE
                        SET name = EXCLUDED.name,
                            updated_at = CURRENT_TIMESTAMP
                    """, op['data'])

            session.commit()
            return {"status": "success"}
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
```

### 2.2 IoT边缘计算架构

```text
IoT边缘计算混合架构
══════════════════════════════════════════════════════════════════════════════

云端（PostgreSQL + TimescaleDB）
├── 历史数据存储
├── 大数据分析
└── 机器学习模型训练

        ↕ 互联网/4G/5G

边缘网关（Raspberry Pi + SQLite）
├── 本地SQLite数据库
│   ├── 传感器数据缓存（最近7天）
│   ├── 设备状态（实时）
│   └── 告警规则（本地处理）
├── 边缘计算
│   ├── 实时数据处理
│   ├── 本地告警检测
│   └── 数据预聚合
└── 定时同步
    ├── 上传聚合数据到云端
    └── 下载规则更新

        ↕ Zigbee/BLE/WiFi

终端设备（传感器）
└── 温度、湿度、运动等传感器
```

**边缘网关SQLite Schema**：

```sql
-- SQLite边缘数据库设计

-- 传感器原始数据
CREATE TABLE sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id INTEGER NOT NULL,
    sensor_type TEXT NOT NULL,  -- 'temperature', 'humidity', etc.
    value REAL NOT NULL,
    timestamp TEXT NOT NULL,
    synced INTEGER DEFAULT 0,

    CHECK (timestamp = datetime(timestamp))  -- 确保ISO8601格式
) STRICT;

CREATE INDEX idx_sensor_timestamp ON sensor_data(sensor_id, timestamp DESC);
CREATE INDEX idx_sensor_synced ON sensor_data(synced) WHERE synced = 0;

-- 预聚合数据（5分钟粒度）
CREATE TABLE sensor_aggregates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id INTEGER NOT NULL,
    time_bucket TEXT NOT NULL,  -- '2025-12-04 10:00:00'
    avg_value REAL NOT NULL,
    min_value REAL NOT NULL,
    max_value REAL NOT NULL,
    count INTEGER NOT NULL,
    synced INTEGER DEFAULT 0,

    UNIQUE(sensor_id, time_bucket)
) STRICT;

-- 触发器：自动聚合
CREATE TRIGGER auto_aggregate AFTER INSERT ON sensor_data
BEGIN
    INSERT INTO sensor_aggregates (
        sensor_id, time_bucket, avg_value, min_value, max_value, count
    )
    SELECT
        NEW.sensor_id,
        datetime(NEW.timestamp, 'start of hour',
                 '+' || (CAST(strftime('%M', NEW.timestamp) AS INT) / 5) * 5 || ' minutes'),
        NEW.value, NEW.value, NEW.value, 1
    ON CONFLICT (sensor_id, time_bucket) DO UPDATE SET
        avg_value = (avg_value * count + NEW.value) / (count + 1),
        min_value = MIN(min_value, NEW.value),
        max_value = MAX(max_value, NEW.value),
        count = count + 1;
END;

-- 本地告警检测
CREATE VIEW sensor_alerts AS
SELECT
    s.sensor_id,
    s.sensor_type,
    s.value,
    s.timestamp,
    CASE
        WHEN s.sensor_type = 'temperature' AND s.value > 35 THEN 'HIGH_TEMP'
        WHEN s.sensor_type = 'humidity' AND s.value < 30 THEN 'LOW_HUMIDITY'
        ELSE NULL
    END AS alert_type
FROM sensor_data s
WHERE timestamp >= datetime('now', '-1 hour')
HAVING alert_type IS NOT NULL;
```

**边缘计算Python代码**：

```python
import sqlite3
import time
from datetime import datetime, timedelta

class EdgeGateway:
    def __init__(self):
        self.conn = sqlite3.connect('edge.db')
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")

    def process_sensor_data(self, sensor_id, sensor_type, value):
        """处理传感器数据"""
        # 1. 存储原始数据
        self.conn.execute("""
            INSERT INTO sensor_data (sensor_id, sensor_type, value, timestamp)
            VALUES (?, ?, ?, ?)
        """, (sensor_id, sensor_type, value, datetime.now().isoformat()))
        self.conn.commit()

        # 2. 检查告警（触发器已自动聚合）
        alerts = self.conn.execute("""
            SELECT sensor_id, sensor_type, value, alert_type
            FROM sensor_alerts
            WHERE sensor_id = ?
        """, (sensor_id,)).fetchall()

        for alert in alerts:
            self.send_local_alert(alert)

    def sync_to_cloud(self, api_endpoint):
        """同步数据到云端"""
        # 1. 上传聚合数据（而非原始数据，节省带宽）
        aggregates = self.conn.execute("""
            SELECT sensor_id, time_bucket, avg_value, min_value, max_value, count
            FROM sensor_aggregates
            WHERE synced = 0
            ORDER BY time_bucket
            LIMIT 1000
        """).fetchall()

        if not aggregates:
            return

        try:
            # HTTP POST到云端
            response = requests.post(f"{api_endpoint}/ingest", json={
                'aggregates': [dict(zip(['sensor_id', 'time_bucket', 'avg', 'min', 'max', 'count'], row))
                              for row in aggregates]
            })

            if response.status_code == 200:
                # 标记已同步
                ids = [row[0] for row in aggregates]
                placeholders = ','.join('?' * len(ids))
                self.conn.execute(f"""
                    UPDATE sensor_aggregates
                    SET synced = 1
                    WHERE id IN ({placeholders})
                """, ids)
                self.conn.commit()

        except Exception as e:
            print(f"同步失败: {e}")

    def cleanup_old_data(self):
        """清理超过7天的原始数据"""
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        self.conn.execute("""
            DELETE FROM sensor_data
            WHERE timestamp < ? AND synced = 1
        """, (cutoff,))
        self.conn.commit()
```

### 2.3 分布式系统本地缓存

```text
微服务架构中的SQLite应用
══════════════════════════════════════════════════════════════════════════════

              ┌─────────────────────────────────────┐
              │         API Gateway                 │
              └───────────────┬─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ 服务A        │      │ 服务B        │      │ 服务C        │
│ + SQLite缓存 │      │ + SQLite缓存 │      │ + SQLite缓存 │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
        ┌──────────────┐          ┌──────────────┐
        │ PostgreSQL   │          │ Redis        │
        │ (主数据库)   │          │ (分布式缓存) │
        └──────────────┘          └──────────────┘

每个微服务的SQLite缓存：
• 缓存该服务常用的数据
• 减少数据库查询压力
• 降低服务间调用
• 提高响应速度

优势：
✅ 服务独立性（缓存失效不影响其他服务）
✅ 零配置（SQLite无需额外部署）
✅ 成本低（无需Redis集群）
✅ 故障隔离（数据库宕机仍可用缓存数据）
```

---

## 三、数据同步策略

### 3.1 全量同步

```python
def full_sync_postgres_to_sqlite():
    """全量同步：PostgreSQL → SQLite"""
    pg_conn = psycopg2.connect(...)
    sqlite_conn = sqlite3.connect('local.db')

    # 1. 清空SQLite
    sqlite_conn.execute("DELETE FROM users")

    # 2. 从PostgreSQL导出
    pg_cursor = pg_conn.cursor('server_cursor')  # 服务端游标，避免内存溢出
    pg_cursor.execute("SELECT id, name, email, updated_at FROM users")

    # 3. 批量插入SQLite
    batch_size = 1000
    batch = []

    for row in pg_cursor:
        batch.append(row)
        if len(batch) >= batch_size:
            sqlite_conn.executemany(
                "INSERT INTO users VALUES (?, ?, ?, ?)", batch
            )
            sqlite_conn.commit()
            batch = []

    if batch:
        sqlite_conn.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", batch)
        sqlite_conn.commit()

    # 4. 记录同步时间
    sqlite_conn.execute("""
        INSERT OR REPLACE INTO sync_metadata (key, value)
        VALUES ('last_full_sync', ?)
    """, (datetime.now().isoformat(),))
    sqlite_conn.commit()
```

### 3.2 增量同步

```python
def incremental_sync():
    """增量同步：只同步变更数据"""
    sqlite_conn = sqlite3.connect('local.db')
    pg_conn = psycopg2.connect(...)

    # 1. 获取上次同步时间
    last_sync = sqlite_conn.execute("""
        SELECT value FROM sync_metadata WHERE key = 'last_sync'
    """).fetchone()

    last_sync_time = last_sync[0] if last_sync else '1970-01-01'

    # 2. 查询PostgreSQL变更数据
    pg_cursor = pg_conn.cursor()
    pg_cursor.execute("""
        SELECT id, name, email, updated_at, deleted
        FROM users
        WHERE updated_at > %s
        ORDER BY updated_at
    """, (last_sync_time,))

    # 3. 应用变更到SQLite
    for row in pg_cursor:
        if row[4]:  # deleted=True
            sqlite_conn.execute("DELETE FROM users WHERE id = ?", (row[0],))
        else:
            sqlite_conn.execute("""
                INSERT OR REPLACE INTO users (id, name, email, updated_at)
                VALUES (?, ?, ?, ?)
            """, row[:4])

    sqlite_conn.execute("""
        INSERT OR REPLACE INTO sync_metadata (key, value)
        VALUES ('last_sync', ?)
    """, (datetime.now().isoformat(),))

    sqlite_conn.commit()
```

### 3.3 冲突解决

```sql
-- 冲突解决策略

-- 策略1: Last-Write-Wins（最后写入胜出）
INSERT OR REPLACE INTO users (id, name, updated_at)
VALUES (?, ?, ?)
WHERE updated_at < ?;  -- 只有更新的数据才覆盖

-- 策略2: 版本号冲突检测
UPDATE users
SET name = ?, version = version + 1
WHERE id = ? AND version = ?;
-- 如果version不匹配，更新失败，需要合并

-- 策略3: 字段级合并
UPDATE users
SET
    name = CASE WHEN ? > name_updated_at THEN ? ELSE name END,
    email = CASE WHEN ? > email_updated_at THEN ? ELSE email END,
    name_updated_at = ?,
    email_updated_at = ?
WHERE id = ?;
```

---

## 四、性能优化策略

### 4.1 查询路由

```python
class SmartQueryRouter:
    """智能查询路由"""

    def __init__(self):
        self.pg_pool = create_pg_pool()  # PostgreSQL连接池
        self.sqlite_conn = sqlite3.connect('cache.db')

    def query(self, sql, params, force_master=False):
        """根据查询类型路由到不同数据库"""

        # 1. 写操作→PostgreSQL
        if sql.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
            return self._query_postgres(sql, params)

        # 2. 强制主库查询
        if force_master:
            return self._query_postgres(sql, params)

        # 3. 简单SELECT→SQLite缓存
        if self._is_cacheable(sql):
            # 先查SQLite
            result = self._query_sqlite(sql, params)
            if result:
                return result

            # SQLite未命中，查PostgreSQL并缓存
            result = self._query_postgres(sql, params)
            self._cache_result(sql, params, result)
            return result

        # 4. 复杂查询→PostgreSQL
        return self._query_postgres(sql, params)

    def _is_cacheable(self, sql):
        """判断查询是否可缓存"""
        # 简单SELECT + 主键/索引查询
        return ('SELECT' in sql.upper() and
                'WHERE' in sql.upper() and
                'JOIN' not in sql.upper())
```

### 4.2 缓存策略

```text
多级缓存策略
══════════════════════════════════════════════════════════════════════════════

L1: 应用内存缓存（进程级）
├── 容量: 100MB
├── TTL: 1分钟
├── 命中率: 60%
└── 延迟: 0.1ms

L2: SQLite进程缓存（机器级）
├── 容量: 1GB
├── TTL: 1小时
├── 命中率: 35%
└── 延迟: 1ms

L3: PostgreSQL主库（集群级）
├── 容量: 无限
├── TTL: 永久
├── 命中率: 5%
└── 延迟: 5-10ms

缓存更新策略：
• Write-Through: 写入时同步更新所有缓存层
• Write-Back: 写入缓存，异步刷新数据库
• Cache-Aside: 应用负责缓存失效和更新
```

---

## 五、完整实现案例

### 5.1 新闻App架构

```python
# 新闻App完整架构实现

class NewsApp:
    def __init__(self):
        # 本地SQLite（WAL模式）
        self.local_db = sqlite3.connect('news.db')
        self.local_db.execute("PRAGMA journal_mode=WAL")
        self.local_db.execute("PRAGMA synchronous=NORMAL")
        self.setup_local_schema()

        # 云端PostgreSQL
        self.cloud_db = psycopg2.connect(
            "postgresql://user:pass@cloud-db/news"
        )

    def setup_local_schema(self):
        """设置本地数据库Schema"""
        self.local_db.executescript("""
            -- 文章缓存
            CREATE TABLE IF NOT EXISTS articles (
                article_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                author TEXT NOT NULL,
                published_at TEXT NOT NULL,
                cached_at TEXT NOT NULL,
                read_count INTEGER DEFAULT 0
            ) STRICT;

            -- 用户阅读历史
            CREATE TABLE IF NOT EXISTS reading_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                read_at TEXT NOT NULL,
                duration_seconds INTEGER,
                synced INTEGER DEFAULT 0
            ) STRICT;

            -- 离线收藏
            CREATE TABLE IF NOT EXISTS bookmarks (
                article_id INTEGER PRIMARY KEY,
                bookmarked_at TEXT NOT NULL,
                synced INTEGER DEFAULT 0
            ) STRICT;

            CREATE INDEX idx_reading_history_synced
            ON reading_history(synced) WHERE synced = 0;
        """)

    def fetch_articles(self, limit=20):
        """获取文章列表（离线优先）"""
        # 1. 先查本地缓存
        articles = self.local_db.execute("""
            SELECT article_id, title, author, published_at
            FROM articles
            WHERE cached_at >= datetime('now', '-1 day')
            ORDER BY published_at DESC
            LIMIT ?
        """, (limit,)).fetchall()

        if len(articles) >= limit:
            return articles  # 缓存充足，直接返回

        # 2. 缓存不足，从云端拉取
        if self.is_online():
            cursor = self.cloud_db.cursor()
            cursor.execute("""
                SELECT article_id, title, content, author, published_at
                FROM articles
                ORDER BY published_at DESC
                LIMIT %s
            """, (limit,))

            cloud_articles = cursor.fetchall()

            # 3. 写入本地缓存
            self.local_db.executemany("""
                INSERT OR REPLACE INTO articles
                (article_id, title, content, author, published_at, cached_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [(row[0], row[1], row[2], row[3], row[4], datetime.now().isoformat())
                  for row in cloud_articles])
            self.local_db.commit()

            return cloud_articles

        return articles  # 离线状态，返回缓存数据

    def record_reading(self, article_id, duration):
        """记录阅读行为"""
        self.local_db.execute("""
            INSERT INTO reading_history (article_id, read_at, duration_seconds)
            VALUES (?, ?, ?)
        """, (article_id, datetime.now().isoformat(), duration))

        # 更新本地阅读计数
        self.local_db.execute("""
            UPDATE articles SET read_count = read_count + 1
            WHERE article_id = ?
        """, (article_id,))

        self.local_db.commit()

    def sync_reading_history(self):
        """同步阅读历史到云端"""
        if not self.is_online():
            return

        # 获取未同步的阅读记录
        records = self.local_db.execute("""
            SELECT id, article_id, read_at, duration_seconds
            FROM reading_history
            WHERE synced = 0
            LIMIT 100
        """).fetchall()

        if not records:
            return

        try:
            cursor = self.cloud_db.cursor()
            # PostgreSQL批量插入
            cursor.executemany("""
                INSERT INTO reading_history (article_id, user_id, read_at, duration_seconds)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (article_id, user_id, read_at) DO NOTHING
            """, [(r[1], self.user_id, r[2], r[3]) for r in records])

            self.cloud_db.commit()

            # 标记SQLite中已同步
            ids = [r[0] for r in records]
            placeholders = ','.join('?' * len(ids))
            self.local_db.execute(f"""
                UPDATE reading_history
                SET synced = 1
                WHERE id IN ({placeholders})
            """, ids)
            self.local_db.commit()

        except Exception as e:
            self.cloud_db.rollback()
            print(f"同步失败: {e}")
```

### 5.2 协同办公系统

```text
协同办公混合架构
══════════════════════════════════════════════════════════════════════════════

云端PostgreSQL:
• 文档主版本（authoritative）
• 实时协作（多人编辑）
• 版本历史（完整审计）

本地SQLite:
• 文档草稿（离线编辑）
• 快速搜索索引
• 附件缓存

数据一致性保证：
• 操作转换（Operational Transformation）
• CRDT（Conflict-free Replicated Data Type）
• 版本向量（Vector Clock）
```

```sql
-- PostgreSQL: 文档版本表

CREATE TABLE documents (
    doc_id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_by BIGINT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    vector_clock JSONB NOT NULL DEFAULT '{}'::jsonb  -- 向量时钟
);

CREATE TABLE document_operations (
    op_id BIGSERIAL PRIMARY KEY,
    doc_id BIGINT NOT NULL REFERENCES documents(doc_id),
    operation JSONB NOT NULL,  -- {type: 'insert', pos: 10, text: 'hello'}
    user_id BIGINT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    vector_clock JSONB NOT NULL
);

-- SQLite: 本地草稿

CREATE TABLE local_drafts (
    doc_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    local_version INTEGER NOT NULL DEFAULT 1,
    server_version INTEGER NOT NULL,  -- 基于哪个服务器版本
    pending_ops TEXT NOT NULL DEFAULT '[]',  -- JSON数组
    last_sync_at TEXT
) STRICT;
```

---

**架构设计完成！**

本文档展示了：

- ✅ 3种混合架构设计模式
- ✅ 3种典型场景完整方案（移动App/IoT/微服务）
- ✅ 完整的数据同步策略（全量/增量/冲突解决）
- ✅ 多级缓存优化策略
- ✅ 2个端到端实现案例（新闻App/协同办公）

---

**文档版本**: v1.0.0
**最后更新**: 2025-12-04
**维护者**: Data-Science Architecture Team
