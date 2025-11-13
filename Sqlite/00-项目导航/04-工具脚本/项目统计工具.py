#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 知识库项目统计工具

> **工具类型**：项目统计
> **功能**：统计项目文档、代码示例、工具脚本等
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def count_files_by_type(directory, file_extensions):
    """统计指定扩展名的文件数量"""
    count = 0
    for root, dirs, files in os.walk(directory):
        # 跳过隐藏目录和特定目录
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if any(file.endswith(ext) for ext in file_extensions):
                count += 1
    return count

def count_lines_in_file(file_path):
    """统计文件行数"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except:
        return 0

def count_total_lines(directory, file_extensions):
    """统计总行数"""
    total = 0
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if any(file.endswith(ext) for ext in file_extensions):
                file_path = os.path.join(root, file)
                total += count_lines_in_file(file_path)
    return total

def analyze_project():
    """分析项目统计信息"""
    project_root = Path(__file__).parent.parent.parent
    
    print("=" * 60)
    print("SQLite 知识库项目统计")
    print("=" * 60)
    print()
    
    # 核心文档统计
    print("📚 核心文档统计")
    print("-" * 60)
    core_dirs = [
        '01-核心架构',
        '02-数据模型',
        '03-性能优化',
        '04-应用场景',
        '05-对比选型',
        '06-形式化理论',
        '07-标准对齐',
        '08-编程实践',
        '09-最新特性'
    ]
    
    total_docs = 0
    total_doc_lines = 0
    
    for dir_name in core_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            md_files = list(dir_path.glob('*.md'))
            # 排除README.md
            md_files = [f for f in md_files if f.name != 'README.md']
            doc_count = len(md_files)
            total_docs += doc_count
            
            doc_lines = sum(count_lines_in_file(str(f)) for f in md_files)
            total_doc_lines += doc_lines
            
            print(f"  {dir_name}: {doc_count} 个文档, {doc_lines:,} 行")
    
    print(f"  总计: {total_docs} 个文档, {total_doc_lines:,} 行")
    print()
    
    # 代码示例统计
    print("💻 代码示例统计")
    print("-" * 60)
    examples_dir = project_root / 'examples'
    if examples_dir.exists():
        py_files = list(examples_dir.rglob('*.py'))
        example_count = len(py_files)
        example_lines = sum(count_lines_in_file(str(f)) for f in py_files)
        print(f"  Python示例: {example_count} 个文件, {example_lines:,} 行")
    else:
        print("  Python示例: 0 个文件")
    print()
    
    # 工具脚本统计
    print("🛠️  工具脚本统计")
    print("-" * 60)
    tools_dir = project_root / 'tools'
    if tools_dir.exists():
        py_files = list(tools_dir.rglob('*.py'))
        tool_count = len(py_files)
        tool_lines = sum(count_lines_in_file(str(f)) for f in py_files)
        print(f"  Python工具: {tool_count} 个文件, {tool_lines:,} 行")
    else:
        print("  Python工具: 0 个文件")
    print()
    
    # 案例文档统计
    print("📖 案例文档统计")
    print("-" * 60)
    cases_dir = project_root / 'cases'
    if cases_dir.exists():
        md_files = list(cases_dir.glob('*.md'))
        md_files = [f for f in md_files if f.name != 'README.md']
        case_count = len(md_files)
        case_lines = sum(count_lines_in_file(str(f)) for f in md_files)
        print(f"  案例文档: {case_count} 个文件, {case_lines:,} 行")
    else:
        print("  案例文档: 0 个文件")
    print()
    
    # 项目报告统计
    print("📊 项目报告统计")
    print("-" * 60)
    reports_dir = project_root / '00-项目导航' / '02-项目报告'
    if reports_dir.exists():
        md_files = list(reports_dir.glob('*.md'))
        report_count = len(md_files)
        report_lines = sum(count_lines_in_file(str(f)) for f in md_files)
        print(f"  项目报告: {report_count} 个文件, {report_lines:,} 行")
    else:
        print("  项目报告: 0 个文件")
    print()
    
    # 总计
    print("=" * 60)
    print("📈 项目总计")
    print("=" * 60)
    total_files = total_docs + example_count + tool_count + case_count + report_count
    total_lines = total_doc_lines + example_lines + tool_lines + case_lines + report_lines
    
    print(f"  总文件数: {total_files} 个")
    print(f"  总代码行数: {total_lines:,} 行")
    print()
    
    # 文件类型分布
    print("📁 文件类型分布")
    print("-" * 60)
    all_md = count_files_by_type(str(project_root), ['.md'])
    all_py = count_files_by_type(str(project_root), ['.py'])
    print(f"  Markdown文件: {all_md} 个")
    print(f"  Python文件: {all_py} 个")
    print()

if __name__ == '__main__':
    analyze_project()
