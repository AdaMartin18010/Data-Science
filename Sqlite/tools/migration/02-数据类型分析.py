#!/usr/bin/env python3
"""
SQLite数据类型分析工具

功能：
- 分析SQLite数据类型使用情况
- 生成PostgreSQL类型映射建议
- 识别类型转换风险
- 分析实际存储类型

使用方法：
    python 02-数据类型分析.py database.db [--table TABLE_NAME] [--output report.json]
"""

import sqlite3
import json
import sys
import argparse
from typing import Dict, List, Any, Set
from collections import defaultdict


class DataTypeAnalyzer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.report = {
            'database': db_path,
            'tables': [],
            'type_mapping': {},
            'risks': [],
            'recommendations': []
        }
    
    def analyze(self, table_name: str = None):
        """执行数据类型分析"""
        print("🔍 开始数据类型分析...")
        
        # 获取所有表
        cursor = self.conn.cursor()
        if table_name:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            print("❌ 未找到表")
            return self.report
        
        # 分析每个表
        for table in tables:
            self._analyze_table(table)
        
        # 生成类型映射建议
        self._generate_type_mapping()
        
        # 识别风险
        self._identify_risks()
        
        print("✅ 分析完成")
        return self.report
    
    def _analyze_table(self, table_name: str):
        """分析单个表的数据类型"""
        cursor = self.conn.cursor()
        
        table_info = {
            'name': table_name,
            'columns': [],
            'row_count': 0,
            'sample_data': {}
        }
        
        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # 获取行数
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        table_info['row_count'] = cursor.fetchone()[0]
        
        # 分析每列
        for col in columns:
            col_name = col[1]
            declared_type = col[2] or ''
            not_null = col[3]
            default_value = col[4]
            primary_key = col[5]
            
            col_info = {
                'name': col_name,
                'declared_type': declared_type,
                'type_affinity': self._get_type_affinity(declared_type),
                'not_null': bool(not_null),
                'default_value': default_value,
                'primary_key': bool(primary_key),
                'actual_types': {},
                'sample_values': []
            }
            
            # 分析实际存储类型
            if table_info['row_count'] > 0:
                self._analyze_actual_types(cursor, table_name, col_name, col_info)
            
            table_info['columns'].append(col_info)
        
        self.report['tables'].append(table_info)
        print(f"  📋 分析表: {table_name} ({table_info['row_count']} 行)")
    
    def _get_type_affinity(self, declared_type: str) -> str:
        """获取类型亲和性"""
        if not declared_type:
            return 'NUMERIC'
        
        declared_type_upper = declared_type.upper()
        
        if 'INT' in declared_type_upper:
            return 'INTEGER'
        elif 'CHAR' in declared_type_upper or 'CLOB' in declared_type_upper or 'TEXT' in declared_type_upper:
            return 'TEXT'
        elif 'BLOB' in declared_type_upper or not declared_type_upper:
            return 'BLOB'
        elif 'REAL' in declared_type_upper or 'FLOA' in declared_type_upper or 'DOUB' in declared_type_upper:
            return 'REAL'
        else:
            return 'NUMERIC'
    
    def _analyze_actual_types(self, cursor, table_name: str, col_name: str, col_info: Dict):
        """分析实际存储类型"""
        # 采样分析（最多1000行）
        cursor.execute(f"SELECT {col_name} FROM {table_name} LIMIT 1000")
        rows = cursor.fetchall()
        
        type_counts = defaultdict(int)
        sample_values = []
        
        for row in rows:
            value = row[0]
            
            if value is None:
                type_counts['NULL'] += 1
            elif isinstance(value, int):
                type_counts['INTEGER'] += 1
                if len(sample_values) < 5:
                    sample_values.append(value)
            elif isinstance(value, float):
                type_counts['REAL'] += 1
                if len(sample_values) < 5:
                    sample_values.append(value)
            elif isinstance(value, str):
                type_counts['TEXT'] += 1
                if len(sample_values) < 5:
                    sample_values.append(value[:50])  # 截断长文本
            elif isinstance(value, bytes):
                type_counts['BLOB'] += 1
                if len(sample_values) < 5:
                    sample_values.append(f"<BLOB {len(value)} bytes>")
        
        col_info['actual_types'] = dict(type_counts)
        col_info['sample_values'] = sample_values
        
        # 检查类型一致性
        if len(type_counts) > 1 and 'NULL' not in type_counts:
            col_info['type_inconsistent'] = True
        elif len(type_counts) > 2:
            col_info['type_inconsistent'] = True
    
    def _generate_type_mapping(self):
        """生成PostgreSQL类型映射建议"""
        type_mapping = {}
        
        for table in self.report['tables']:
            for col in table['columns']:
                col_name = f"{table['name']}.{col['name']}"
                affinity = col['type_affinity']
                actual_types = col.get('actual_types', {})
                
                # 基于实际类型生成映射建议
                if not actual_types or 'NULL' in actual_types and len(actual_types) == 1:
                    # 全NULL列
                    mapping = {
                        'recommended_type': 'TEXT',
                        'reason': '列全为NULL，建议使用TEXT',
                        'confidence': 'low'
                    }
                elif 'INTEGER' in actual_types and len(actual_types) == 1:
                    # 纯整数
                    # 检查范围
                    max_value = max([v for v in col.get('sample_values', []) if isinstance(v, int)], default=0)
                    if max_value > 2147483647:
                        mapping = {
                            'recommended_type': 'BIGINT',
                            'reason': '值超出INTEGER范围',
                            'confidence': 'high'
                        }
                    else:
                        mapping = {
                            'recommended_type': 'INTEGER',
                            'reason': '整数类型',
                            'confidence': 'high'
                        }
                elif 'REAL' in actual_types and len(actual_types) == 1:
                    # 纯浮点数
                    mapping = {
                        'recommended_type': 'DOUBLE PRECISION',
                        'reason': '浮点数类型',
                        'confidence': 'high'
                    }
                elif 'TEXT' in actual_types and len(actual_types) == 1:
                    # 纯文本
                    # 检查长度
                    max_length = max([len(str(v)) for v in col.get('sample_values', [])], default=0)
                    if max_length > 255:
                        mapping = {
                            'recommended_type': 'TEXT',
                            'reason': f'文本长度超过255（最大{max_length}）',
                            'confidence': 'high'
                        }
                    else:
                        mapping = {
                            'recommended_type': f'VARCHAR({max(255, max_length + 10)})',
                            'reason': f'文本类型，建议长度{max(255, max_length + 10)}',
                            'confidence': 'medium'
                        }
                elif 'BLOB' in actual_types:
                    mapping = {
                        'recommended_type': 'BYTEA',
                        'reason': '二进制数据',
                        'confidence': 'high'
                    }
                else:
                    # 混合类型
                    mapping = {
                        'recommended_type': 'TEXT',
                        'reason': '混合类型，建议转换为TEXT',
                        'confidence': 'low'
                    }
                
                type_mapping[col_name] = mapping
                col['pg_type_mapping'] = mapping
        
        self.report['type_mapping'] = type_mapping
    
    def _identify_risks(self):
        """识别类型转换风险"""
        risks = []
        
        for table in self.report['tables']:
            for col in table['columns']:
                # 检查类型不一致
                if col.get('type_inconsistent'):
                    risks.append({
                        'table': table['name'],
                        'column': col['name'],
                        'type': 'type_inconsistent',
                        'severity': 'medium',
                        'message': f"列 {col['name']} 存储了多种类型的数据",
                        'actual_types': col.get('actual_types', {})
                    })
                
                # 检查NUMERIC亲和性
                if col['type_affinity'] == 'NUMERIC' and col.get('actual_types'):
                    if len(col['actual_types']) > 2:
                        risks.append({
                            'table': table['name'],
                            'column': col['name'],
                            'type': 'numeric_affinity',
                            'severity': 'high',
                            'message': f"列 {col['name']} 使用NUMERIC亲和性，存储了多种类型",
                            'actual_types': col.get('actual_types', {})
                        })
                
                # 检查INTEGER范围
                if col['type_affinity'] == 'INTEGER':
                    sample_ints = [v for v in col.get('sample_values', []) if isinstance(v, int)]
                    if sample_ints:
                        max_val = max(sample_ints)
                        if max_val > 2147483647:
                            risks.append({
                                'table': table['name'],
                                'column': col['name'],
                                'type': 'integer_range',
                                'severity': 'high',
                                'message': f"列 {col['name']} 的值 {max_val} 超出INTEGER范围",
                                'max_value': max_val
                            })
        
        self.report['risks'] = risks
    
    def print_report(self):
        """打印分析报告"""
        print("\n" + "="*60)
        print("📊 数据类型分析报告")
        print("="*60)
        
        for table in self.report['tables']:
            print(f"\n📋 表: {table['name']}")
            print(f"  行数: {table['row_count']}")
            
            for col in table['columns']:
                print(f"\n  🔹 列: {col['name']}")
                print(f"    声明类型: {col['declared_type'] or '(无)'}")
                print(f"    类型亲和性: {col['type_affinity']}")
                
                if col.get('actual_types'):
                    print(f"    实际类型分布:")
                    for type_name, count in col['actual_types'].items():
                        print(f"      - {type_name}: {count}")
                
                if col.get('pg_type_mapping'):
                    mapping = col['pg_type_mapping']
                    print(f"    PostgreSQL建议: {mapping['recommended_type']}")
                    print(f"      原因: {mapping['reason']}")
                    print(f"      置信度: {mapping['confidence']}")
        
        if self.report['risks']:
            print(f"\n⚠️  风险点 ({len(self.report['risks'])}):")
            for risk in self.report['risks']:
                print(f"  - [{risk['severity'].upper()}] {risk['message']}")
        
        print("\n" + "="*60)
    
    def save_report(self, output_path: str):
        """保存报告到JSON文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n💾 报告已保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='SQLite数据类型分析工具')
    parser.add_argument('database', help='SQLite数据库文件路径')
    parser.add_argument('--table', '-t', help='指定要分析的表名（可选）')
    parser.add_argument('--output', '-o', help='输出JSON报告文件路径')
    
    args = parser.parse_args()
    
    try:
        analyzer = DataTypeAnalyzer(args.database)
        report = analyzer.analyze(args.table)
        analyzer.print_report()
        
        if args.output:
            analyzer.save_report(args.output)
    
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
