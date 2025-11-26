#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 基础操作示例：基本查询

> **难度**：⭐ 入门级
> **适用版本**：SQLite 3.31+ 至 3.47.x
> **最后更新**：2025-01-15
"""

import sqlite3
import os

def setup_test_data(conn):
    """设置测试数据"""
    # 创建表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT,
            salary REAL,
            hire_date TEXT
        )
    ''')
    
    # 清空数据
    conn.execute('DELETE FROM employees')
    
    # 插入测试数据
    employees = [
        ('Alice', 'Engineering', 75000, '2020-01-15'),
        ('Bob', 'Engineering', 80000, '2019-03-20'),
        ('Charlie', 'Sales', 60000, '2021-06-10'),
        ('David', 'Sales', 65000, '2020-11-05'),
        ('Eve', 'Marketing', 70000, '2021-02-28'),
        ('Frank', 'Engineering', 90000, '2018-09-12'),
    ]
    
    conn.executemany(
        'INSERT INTO employees (name, department, salary, hire_date) VALUES (?, ?, ?, ?)',
        employees
    )
    conn.commit()

def example_01_basic_select():
    """示例1：基本SELECT查询"""
    print("=" * 50)
    print("示例1：基本SELECT查询")
    print("=" * 50)
    
    db_path = 'example.db'
    
    with sqlite3.connect(db_path) as conn:
        setup_test_data(conn)
        
        # 查询所有数据
        print("\n所有员工：")
        cursor = conn.execute("SELECT * FROM employees")
        for row in cursor:
            print(f"  {row}")
        
        # 查询特定列
        print("\n员工姓名和部门：")
        cursor = conn.execute("SELECT name, department FROM employees")
        for row in cursor:
            print(f"  {row[0]} - {row[1]}")
    
    print()


def example_02_where_clause():
    """示例2：WHERE子句"""
    print("=" * 50)
    print("示例2：WHERE子句")
    print("=" * 50)
    
    db_path = 'example.db'
    
    with sqlite3.connect(db_path) as conn:
        setup_test_data(conn)
        
        # 条件查询
        print("\nEngineering部门的员工：")
        cursor = conn.execute(
            "SELECT name, salary FROM employees WHERE department = ?",
            ('Engineering',)
        )
        for row in cursor:
            print(f"  {row[0]}: ${row[1]:,.0f}")
        
        # 范围查询
        print("\n薪资大于70000的员工：")
        cursor = conn.execute(
            "SELECT name, salary FROM employees WHERE salary > ?",
            (70000,)
        )
        for row in cursor:
            print(f"  {row[0]}: ${row[1]:,.0f}")
    
    print()


def example_03_order_by():
    """示例3：ORDER BY排序"""
    print("=" * 50)
    print("示例3：ORDER BY排序")
    print("=" * 50)
    
    db_path = 'example.db'
    
    with sqlite3.connect(db_path) as conn:
        setup_test_data(conn)
        
        # 按薪资降序排序
        print("\n按薪资降序排序：")
        cursor = conn.execute(
            "SELECT name, salary FROM employees ORDER BY salary DESC"
        )
        for row in cursor:
            print(f"  {row[0]}: ${row[1]:,.0f}")
        
        # 多列排序
        print("\n按部门和薪资排序：")
        cursor = conn.execute(
            "SELECT name, department, salary FROM employees ORDER BY department, salary DESC"
        )
        for row in cursor:
            print(f"  {row[0]} ({row[1]}): ${row[2]:,.0f}")
    
    print()


def example_04_aggregate_functions():
    """示例4：聚合函数"""
    print("=" * 50)
    print("示例4：聚合函数")
    print("=" * 50)
    
    db_path = 'example.db'
    
    with sqlite3.connect(db_path) as conn:
        setup_test_data(conn)
        
        # COUNT
        count = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        print(f"员工总数：{count}")
        
        # AVG
        avg_salary = conn.execute("SELECT AVG(salary) FROM employees").fetchone()[0]
        print(f"平均薪资：${avg_salary:,.0f}")
        
        # MAX
        max_salary = conn.execute("SELECT MAX(salary) FROM employees").fetchone()[0]
        print(f"最高薪资：${max_salary:,.0f}")
        
        # MIN
        min_salary = conn.execute("SELECT MIN(salary) FROM employees").fetchone()[0]
        print(f"最低薪资：${min_salary:,.0f}")
        
        # SUM
        total_salary = conn.execute("SELECT SUM(salary) FROM employees").fetchone()[0]
        print(f"薪资总额：${total_salary:,.0f}")
    
    print()


def example_05_group_by():
    """示例5：GROUP BY分组"""
    print("=" * 50)
    print("示例5：GROUP BY分组")
    print("=" * 50)
    
    db_path = 'example.db'
    
    with sqlite3.connect(db_path) as conn:
        setup_test_data(conn)
        
        # 按部门分组统计
        print("\n各部门统计：")
        cursor = conn.execute('''
            SELECT 
                department,
                COUNT(*) as count,
                AVG(salary) as avg_salary,
                MAX(salary) as max_salary
            FROM employees
            GROUP BY department
        ''')
        for row in cursor:
            print(f"  {row[0]}: {row[1]}人, 平均薪资${row[2]:,.0f}, 最高薪资${row[3]:,.0f}")
    
    print()


def example_06_join():
    """示例6：JOIN连接"""
    print("=" * 50)
    print("示例6：JOIN连接")
    print("=" * 50)
    
    db_path = 'example.db'
    
    with sqlite3.connect(db_path) as conn:
        # 创建部门表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                name TEXT PRIMARY KEY,
                location TEXT,
                budget REAL
            )
        ''')
        
        conn.execute('DELETE FROM departments')
        conn.executemany(
            'INSERT INTO departments VALUES (?, ?, ?)',
            [
                ('Engineering', 'Building A', 500000),
                ('Sales', 'Building B', 300000),
                ('Marketing', 'Building C', 200000)
            ]
        )
        conn.commit()
        
        setup_test_data(conn)
        
        # INNER JOIN
        print("\n员工和部门信息（JOIN）：")
        cursor = conn.execute('''
            SELECT 
                e.name,
                e.department,
                e.salary,
                d.location
            FROM employees e
            JOIN departments d ON e.department = d.name
        ''')
        for row in cursor:
            print(f"  {row[0]} ({row[1]}, {row[3]}): ${row[2]:,.0f}")
    
    print()


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("SQLite 基础操作示例：基本查询")
    print("=" * 50 + "\n")
    
    # 清理旧数据库
    if os.path.exists('example.db'):
        os.remove('example.db')
    
    # 运行示例
    example_01_basic_select()
    example_02_where_clause()
    example_03_order_by()
    example_04_aggregate_functions()
    example_05_group_by()
    example_06_join()
    
    # 清理
    if os.path.exists('example.db'):
        os.remove('example.db')
        print("✅ 示例数据库已清理\n")
    
    print("=" * 50)
    print("所有示例执行完成！")
    print("=" * 50)
