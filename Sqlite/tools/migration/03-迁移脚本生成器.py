#!/usr/bin/env python3
"""
SQLite到PostgreSQL迁移脚本生成器

功能：
- 自动生成PostgreSQL DDL
- 生成数据迁移脚本
- 生成索引和约束脚本
- 支持类型映射配置

使用方法：
    python 03-迁移脚本生成器.py database.db --output migration.sql [--config config.json]
"""

import sqlite3
import json
import sys
import argparse
from typing import Dict, List, Any, Optional


class MigrationScriptGenerator:
    def __init__(self, db_path: str, type_mapping: Optional[Dict] = None):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.type_mapping = type_mapping or {}
        self.scripts = {
            'ddl': [],
            'data_migration': [],
            'indexes': [],
            'constraints': [],
            'comments': []
        }
    
    def generate(self):
        """生成所有迁移脚本"""
        print("🔧 开始生成迁移脚本...")
        
        # 获取所有表
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        # 生成表结构
        for table_name in tables:
            self._generate_table_ddl(table_name)
            self._generate_data_migration(table_name)
            self._generate_indexes(table_name)
            self._generate_constraints(table_name)
        
        print("✅ 脚本生成完成")
        return self.scripts
    
    def _generate_table_ddl(self, table_name: str):
        """生成表DDL"""
        cursor = self.conn.cursor()
        
        # 获取表信息
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # 获取CREATE TABLE语句
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        create_sql = cursor.fetchone()[0]
        
        # 生成PostgreSQL DDL
        pg_ddl = f"CREATE TABLE {table_name} (\n"
        
        col_definitions = []
        primary_keys = []
        
        for col in columns:
            col_name = col[1]
            col_type = col[2] or ''
            not_null = col[3]
            default_value = col[4]
            primary_key = col[5]
            
            # 类型映射
            pg_type = self._map_type(col_type, table_name, col_name)
            
            # 列定义
            col_def = f"    {col_name} {pg_type}"
            
            # NOT NULL
            if not_null or primary_key:
                col_def += " NOT NULL"
            
            # DEFAULT
            if default_value is not None:
                pg_default = self._map_default(default_value, pg_type)
                col_def += f" DEFAULT {pg_default}"
            
            # SERIAL for primary key
            if primary_key and 'INTEGER' in col_type.upper():
                col_def = col_def.replace('INTEGER', 'SERIAL').replace(' BIGINT', ' BIGSERIAL')
            
            col_definitions.append(col_def)
            
            if primary_key:
                primary_keys.append(col_name)
        
        pg_ddl += ",\n".join(col_definitions)
        
        # 主键约束
        if primary_keys:
            pg_ddl += f",\n    PRIMARY KEY ({', '.join(primary_keys)})"
        
        pg_ddl += "\n);"
        
        self.scripts['ddl'].append({
            'table': table_name,
            'sql': pg_ddl
        })
        
        print(f"  📋 生成表DDL: {table_name}")
    
    def _map_type(self, sqlite_type: str, table_name: str, col_name: str) -> str:
        """映射SQLite类型到PostgreSQL类型"""
        # 检查自定义映射
        key = f"{table_name}.{col_name}"
        if key in self.type_mapping:
            return self.type_mapping[key]
        
        if not sqlite_type:
            return 'TEXT'
        
        sqlite_type_upper = sqlite_type.upper()
        
        # 基本类型映射
        if 'INT' in sqlite_type_upper:
            return 'INTEGER'
        elif 'CHAR' in sqlite_type_upper or 'TEXT' in sqlite_type_upper or 'CLOB' in sqlite_type_upper:
            return 'TEXT'
        elif 'BLOB' in sqlite_type_upper:
            return 'BYTEA'
        elif 'REAL' in sqlite_type_upper or 'FLOA' in sqlite_type_upper or 'DOUB' in sqlite_type_upper:
            return 'DOUBLE PRECISION'
        elif 'NUMERIC' in sqlite_type_upper or 'DECIMAL' in sqlite_type_upper:
            return 'NUMERIC'
        else:
            return 'TEXT'
    
    def _map_default(self, default_value: Any, pg_type: str) -> str:
        """映射默认值"""
        if isinstance(default_value, str):
            # 检查是否是函数调用
            if default_value.upper().startswith(('CURRENT_', 'NOW()', 'DATETIME', 'DATE')):
                if 'TIMESTAMP' in pg_type.upper():
                    return 'CURRENT_TIMESTAMP'
                elif 'DATE' in pg_type.upper():
                    return 'CURRENT_DATE'
                else:
                    return f"'{default_value}'"
            else:
                return f"'{default_value}'"
        elif isinstance(default_value, (int, float)):
            return str(default_value)
        else:
            return f"'{default_value}'"
    
    def _generate_data_migration(self, table_name: str):
        """生成数据迁移脚本"""
        cursor = self.conn.cursor()
        
        # 获取列信息
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # 生成COPY命令（推荐方式）
        copy_sql = f"""
-- 数据迁移: {table_name}
-- 使用COPY命令（最快）
COPY {table_name} ({', '.join(columns)}) FROM STDIN WITH CSV;
"""
        
        # 或者生成INSERT语句（备用方式）
        placeholders = ', '.join(['%s'] * len(columns))
        insert_sql = f"""
-- 备用方式: 使用INSERT语句
-- INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders});
"""
        
        self.scripts['data_migration'].append({
            'table': table_name,
            'copy_sql': copy_sql,
            'insert_sql': insert_sql
        })
    
    def _generate_indexes(self, table_name: str):
        """生成索引脚本"""
        cursor = self.conn.cursor()
        
        cursor.execute(f"SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='{table_name}'")
        indexes = cursor.fetchall()
        
        for idx_name, idx_sql in indexes:
            if idx_sql:
                # 转换SQLite索引语法到PostgreSQL
                pg_sql = idx_sql.replace('CREATE INDEX', 'CREATE INDEX IF NOT EXISTS')
                pg_sql = pg_sql.replace('CREATE UNIQUE INDEX', 'CREATE UNIQUE INDEX IF NOT EXISTS')
                
                # 移除SQLite特定语法
                pg_sql = pg_sql.replace('ON "', 'ON ').replace('"', '')
                
                self.scripts['indexes'].append({
                    'table': table_name,
                    'name': idx_name,
                    'sql': pg_sql
                })
    
    def _generate_constraints(self, table_name: str):
        """生成约束脚本"""
        cursor = self.conn.cursor()
        
        # 外键约束
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        foreign_keys = cursor.fetchall()
        
        for fk in foreign_keys:
            fk_sql = f"""
ALTER TABLE {table_name}
    ADD CONSTRAINT fk_{table_name}_{fk[3]}
    FOREIGN KEY ({fk[3]}) REFERENCES {fk[2]}({fk[4]});
"""
            self.scripts['constraints'].append({
                'table': table_name,
                'type': 'foreign_key',
                'sql': fk_sql
            })
    
    def save_scripts(self, output_path: str):
        """保存脚本到文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("-- SQLite to PostgreSQL Migration Script\n")
            f.write(f"-- Generated from: {self.db_path}\n")
            f.write("-- \n")
            f.write("-- Usage:\n")
            f.write("--   1. Review and adjust type mappings\n")
            f.write("--   2. Execute DDL scripts to create tables\n")
            f.write("--   3. Migrate data using COPY or INSERT\n")
            f.write("--   4. Create indexes\n")
            f.write("--   5. Add constraints\n")
            f.write("\n")
            f.write("BEGIN;\n\n")
            
            # DDL
            f.write("-- ============================================\n")
            f.write("-- Table Definitions (DDL)\n")
            f.write("-- ============================================\n\n")
            for ddl in self.scripts['ddl']:
                f.write(f"-- Table: {ddl['table']}\n")
                f.write(ddl['sql'])
                f.write("\n\n")
            
            # Data Migration
            f.write("-- ============================================\n")
            f.write("-- Data Migration\n")
            f.write("-- ============================================\n\n")
            for migration in self.scripts['data_migration']:
                f.write(migration['copy_sql'])
                f.write(migration['insert_sql'])
                f.write("\n")
            
            # Indexes
            f.write("-- ============================================\n")
            f.write("-- Indexes\n")
            f.write("-- ============================================\n\n")
            for idx in self.scripts['indexes']:
                f.write(f"-- Index: {idx['name']} on {idx['table']}\n")
                f.write(idx['sql'])
                f.write("\n\n")
            
            # Constraints
            f.write("-- ============================================\n")
            f.write("-- Constraints\n")
            f.write("-- ============================================\n\n")
            for constraint in self.scripts['constraints']:
                f.write(constraint['sql'])
                f.write("\n")
            
            f.write("COMMIT;\n")
        
        print(f"💾 脚本已保存到: {output_path}")


def load_config(config_path: str) -> Dict:
    """加载类型映射配置"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('type_mapping', {})
    except FileNotFoundError:
        print(f"⚠️  配置文件不存在: {config_path}")
        return {}
    except json.JSONDecodeError:
        print(f"⚠️  配置文件格式错误: {config_path}")
        return {}


def main():
    parser = argparse.ArgumentParser(description='SQLite到PostgreSQL迁移脚本生成器')
    parser.add_argument('database', help='SQLite数据库文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出SQL脚本文件路径')
    parser.add_argument('--config', '-c', help='类型映射配置文件路径（JSON格式）')
    
    args = parser.parse_args()
    
    try:
        # 加载配置
        type_mapping = {}
        if args.config:
            type_mapping = load_config(args.config)
        
        # 生成脚本
        generator = MigrationScriptGenerator(args.database, type_mapping)
        scripts = generator.generate()
        generator.save_scripts(args.output)
        
        print(f"\n✅ 成功生成迁移脚本")
        print(f"   - DDL: {len(scripts['ddl'])} 个表")
        print(f"   - 索引: {len(scripts['indexes'])} 个")
        print(f"   - 约束: {len(scripts['constraints'])} 个")
    
    except FileNotFoundError:
        print(f"❌ 错误: 找不到数据库文件 {args.database}")
        sys.exit(1)
    except sqlite3.Error as e:
        print(f"❌ SQLite错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
