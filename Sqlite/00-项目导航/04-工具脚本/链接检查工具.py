#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 知识库链接检查工具

> **工具类型**：链接检查
> **功能**：检查Markdown文档中的内部链接是否有效
"""

import os
import re
from pathlib import Path
from urllib.parse import unquote

def extract_links(content):
    """提取Markdown中的链接"""
    # 匹配 [text](link) 格式
    pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    links = re.findall(pattern, content)
    return links

def check_link(link, file_path, project_root):
    """检查链接是否有效"""
    # 跳过外部链接
    if link.startswith('http://') or link.startswith('https://'):
        return True, "外部链接"
    
    # 跳过锚点链接（只检查文件部分）
    if '#' in link:
        link = link.split('#')[0]
    
    # 处理相对路径
    if link.startswith('./') or link.startswith('../'):
        # 相对于当前文件
        current_dir = file_path.parent
        target_path = (current_dir / link).resolve()
    elif link.startswith('/'):
        # 相对于项目根目录
        target_path = project_root / link.lstrip('/')
    else:
        # 相对于当前文件
        current_dir = file_path.parent
        target_path = current_dir / link
    
    # 检查文件是否存在
    if target_path.exists():
        return True, "有效"
    else:
        return False, f"文件不存在: {target_path}"

def check_file_links(file_path, project_root):
    """检查文件中的所有链接"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        links = extract_links(content)
        issues = []
        
        for text, link in links:
            is_valid, message = check_link(link, file_path, project_root)
            if not is_valid:
                issues.append({
                    'link': link,
                    'text': text,
                    'message': message
                })
        
        return issues
    except Exception as e:
        return [{'link': '', 'text': '', 'message': f'读取文件错误: {e}'}]

def check_all_files(project_root):
    """检查所有Markdown文件"""
    print("=" * 60)
    print("SQLite 知识库链接检查")
    print("=" * 60)
    print()
    
    md_files = list(project_root.rglob('*.md'))
    total_issues = 0
    files_with_issues = []
    
    for md_file in md_files:
        # 跳过某些目录
        if '.git' in str(md_file) or '__pycache__' in str(md_file):
            continue
        
        issues = check_file_links(md_file, project_root)
        if issues:
            total_issues += len(issues)
            files_with_issues.append({
                'file': md_file.relative_to(project_root),
                'issues': issues
            })
    
    # 输出结果
    if files_with_issues:
        print(f"❌ 发现 {total_issues} 个链接问题，涉及 {len(files_with_issues)} 个文件：")
        print()
        for item in files_with_issues:
            print(f"  📄 {item['file']}")
            for issue in item['issues']:
                print(f"     - [{issue['text']}]({issue['link']}): {issue['message']}")
            print()
    else:
        print("✅ 所有链接检查通过！")
        print()
    
    print("=" * 60)
    print(f"检查完成：共检查 {len(md_files)} 个文件")
    print("=" * 60)

if __name__ == '__main__':
    project_root = Path(__file__).parent.parent.parent
    check_all_files(project_root)
