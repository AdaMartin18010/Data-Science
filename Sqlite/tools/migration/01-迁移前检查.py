#!/usr/bin/env python3
"""
SQLite到PostgreSQL迁移前检查工具

功能：
- 检查SQLite数据库结构
- 识别迁移风险点
- 生成迁移报告
- 评估兼容性

使用方法：
    python 01-迁移前检查.py database.db [--output report.json]
"""

import sqlite3
import json
import sys
import argparse
from typing import Dict, List, Any
from collections import defaultdict


class MigrationPreCheck:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.report = {
            'database': db_path,
            'tables': [],
            'risks': [],
            'warnings': [],
            'recommendations': [],
            'compatibility_score': 0
        }
    
    def check_database(self):
        """执行完整的迁移前检查"""
        print("🔍 开始迁移前检查...")
        
        # 检查数据库基本信息
        self._check_basic_info()
        
        # 检查表结构
        self._check_tables()
        
        # 检查数据类型
        self._check_data_types()
        
        # 检查约束
        self._check_constraints()
        
        # 检查外键
        self._check_foreign_keys()
        
        # 检查索引
        self._check_indexes()
        
        # 检查触发器
        self._check_triggers()
        
        # 检查视图
        self._check_views()
        
        # 计算兼容性评分
        self._calculate_compatibility_score()
        
        print("✅ 检查完成")
        return self.report
    
    def _check_basic_info(self):
        """检查数据库基本信息"""
        cursor = self.conn.cursor()
        
        # 检查SQLite版本
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        self.report['sqlite_version'] = version
        
        # 检查数据库大小
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        size = cursor.fetchone()[0]
        self.report['database_size'] = size
        
        # 检查编码
        cursor.execute("PRAGMA encoding")
        encoding = cursor.fetchone()[0]
        self.report['encoding'] = encoding
        
        print(f"  📊 SQLite版本: {version}")
        print(f"  📊 数据库大小: {size / 1024 / 1024:.2f} MB")
        print(f"  📊 编码: {encoding}")
    
    def _check_tables(self):
        """检查表结构"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table_name in tables:
            table_info = {
                'name': table_name,
                'columns': [],
                'row_count': 0,
                'risks': [],
                'warnings': []
            }
            
            # 获取表信息
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # 获取行数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            table_info['row_count'] = cursor.fetchone()[0]
            
            # 分析列
            for col in columns:
                col_info = {
                    'name': col[1],
                    'type': col[2],
                    'not_null': col[3],
                    'default_value': col[4],
                    'primary_key': col[5]
                }
                table_info['columns'].append(col_info)
                
                # 检查类型风险
                if col[2] and 'NUMERIC' in col[2].upper():
                    table_info['warnings'].append(
                        f"列 {col[1]} 使用NUMERIC类型，需要分析实际存储类型"
                    )
            
            self.report['tables'].append(table_info)
        
        print(f"  📋 发现 {len(tables)} 个表")
    
    def _check_data_types(self):
        """检查数据类型兼容性"""
        type_risks = defaultdict(list)
        
        for table in self.report['tables']:
            for col in table['columns']:
                col_type = col['type'] or ''
                col_type_upper = col_type.upper()
                
                # 检查动态类型风险
                if 'NUMERIC' in col_type_upper or 'TEXT' in col_type_upper:
                    type_risks['dynamic_type'].append({
                        'table': table['name'],
                        'column': col['name'],
                        'type': col_type
                    })
                
                # 检查INTEGER范围风险
                if 'INTEGER' in col_type_upper and col['primary_key']:
                    if table['row_count'] > 2147483647:
                        type_risks['integer_range'].append({
                            'table': table['name'],
                            'column': col['name'],
                            'row_count': table['row_count']
                        })
        
        # 添加到报告
        if type_risks['dynamic_type']:
            self.report['risks'].append({
                'type': 'dynamic_type',
                'severity': 'medium',
                'message': '发现动态类型列，需要分析实际存储类型',
                'details': type_risks['dynamic_type']
            })
        
        if type_risks['integer_range']:
            self.report['risks'].append({
                'type': 'integer_range',
                'severity': 'high',
                'message': '发现可能超出INTEGER范围的表',
                'details': type_risks['integer_range']
            })
    
    def _check_constraints(self):
        """检查约束"""
        constraint_issues = []
        
        for table in self.report['tables']:
            cursor = self.conn.cursor()
            
            # 检查CHECK约束
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table['name']}'")
            create_sql = cursor.fetchone()[0]
            
            if create_sql and 'CHECK' in create_sql.upper():
                # SQLite的CHECK约束在运行时检查，PostgreSQL在编译时检查
                constraint_issues.append({
                    'table': table['name'],
                    'type': 'CHECK',
                    'note': 'CHECK约束需要验证语义等价性'
                })
        
        if constraint_issues:
            self.report['warnings'].append({
                'type': 'constraint',
                'message': '发现CHECK约束，需要验证语义',
                'details': constraint_issues
            })
    
    def _check_foreign_keys(self):
        """检查外键"""
        cursor = self.conn.cursor()
        
        # 检查外键是否启用
        cursor.execute("PRAGMA foreign_keys")
        fk_enabled = cursor.fetchone()[0]
        
        if not fk_enabled:
            self.report['warnings'].append({
                'type': 'foreign_keys',
                'message': '外键约束未启用，需要检查应用层约束',
                'severity': 'medium'
            })
        
        # 检查外键定义
        fk_count = 0
        for table in self.report['tables']:
            cursor.execute(f"PRAGMA foreign_key_list({table['name']})")
            fks = cursor.fetchall()
            fk_count += len(fks)
        
        if fk_count > 0:
            self.report['recommendations'].append({
                'type': 'foreign_keys',
                'message': f'发现 {fk_count} 个外键约束，PostgreSQL将强制检查',
                'action': '确保所有外键数据有效'
            })
    
    def _check_indexes(self):
        """检查索引"""
        cursor = self.conn.cursor()
        index_count = 0
        
        for table in self.report['tables']:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='{table['name']}'")
            indexes = cursor.fetchall()
            index_count += len(indexes)
        
        self.report['index_count'] = index_count
        print(f"  📑 发现 {index_count} 个索引")
    
    def _check_triggers(self):
        """检查触发器"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
        triggers = cursor.fetchall()
        
        if triggers:
            self.report['warnings'].append({
                'type': 'triggers',
                'message': f'发现 {len(triggers)} 个触发器，需要手动转换',
                'severity': 'medium',
                'details': [t[0] for t in triggers]
            })
    
    def _check_views(self):
        """检查视图"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = cursor.fetchall()
        
        if views:
            self.report['warnings'].append({
                'type': 'views',
                'message': f'发现 {len(views)} 个视图，需要验证SQL兼容性',
                'severity': 'low',
                'details': [v[0] for v in views]
            })
    
    def _calculate_compatibility_score(self):
        """计算兼容性评分"""
        score = 100
        risk_count = len(self.report['risks'])
        warning_count = len(self.report['warnings'])
        
        # 根据风险和警告扣分
        score -= risk_count * 10  # 每个风险扣10分
        score -= warning_count * 5  # 每个警告扣5分
        
        # 确保分数在0-100之间
        score = max(0, min(100, score))
        
        self.report['compatibility_score'] = score
        
        # 评级
        if score >= 90:
            rating = '优秀'
        elif score >= 70:
            rating = '良好'
        elif score >= 50:
            rating = '中等'
        else:
            rating = '需要关注'
        
        self.report['compatibility_rating'] = rating
    
    def print_report(self):
        """打印检查报告"""
        print("\n" + "="*60)
        print("📊 迁移前检查报告")
        print("="*60)
        
        print(f"\n📋 基本信息:")
        print(f"  - 数据库: {self.report['database']}")
        print(f"  - SQLite版本: {self.report['sqlite_version']}")
        print(f"  - 表数量: {len(self.report['tables'])}")
        print(f"  - 索引数量: {self.report.get('index_count', 0)}")
        
        print(f"\n🎯 兼容性评分: {self.report['compatibility_score']}/100 ({self.report['compatibility_rating']})")
        
        if self.report['risks']:
            print(f"\n⚠️  风险点 ({len(self.report['risks'])}):")
            for risk in self.report['risks']:
                print(f"  - [{risk['severity'].upper()}] {risk['message']}")
                if 'details' in risk and len(risk['details']) <= 3:
                    for detail in risk['details']:
                        if isinstance(detail, dict):
                            print(f"    * {detail.get('table', '')}.{detail.get('column', '')}")
        
        if self.report['warnings']:
            print(f"\n⚠️  警告 ({len(self.report['warnings'])}):")
            for warning in self.report['warnings']:
                print(f"  - {warning['message']}")
        
        if self.report['recommendations']:
            print(f"\n💡 建议 ({len(self.report['recommendations'])}):")
            for rec in self.report['recommendations']:
                print(f"  - {rec['message']}")
        
        print("\n" + "="*60)
    
    def save_report(self, output_path: str):
        """保存报告到JSON文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        print(f"\n💾 报告已保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='SQLite到PostgreSQL迁移前检查工具')
    parser.add_argument('database', help='SQLite数据库文件路径')
    parser.add_argument('--output', '-o', help='输出JSON报告文件路径')
    
    args = parser.parse_args()
    
    try:
        checker = MigrationPreCheck(args.database)
        report = checker.check_database()
        checker.print_report()
        
        if args.output:
            checker.save_report(args.output)
    
    except FileNotFoundError:
        print(f"❌ 错误: 找不到数据库文件 {args.database}")
        sys.exit(1)
    except sqlite3.Error as e:
        print(f"❌ SQLite错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
