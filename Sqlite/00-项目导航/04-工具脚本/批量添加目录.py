#!/usr/bin/env python3
"""
批量为SQLite知识库文档添加目录
使用方法：python 批量添加目录.py
"""

import os
import re
from pathlib import Path

def extract_headings(content):
    """提取文档中的所有标题"""
    headings = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        # 匹配一级标题（## 一、...）
        if re.match(r'^## [一二三四五六七八九十]+、', line):
            level = 1
            text = line.replace('## ', '').strip()
            headings.append((level, text, i))
        # 匹配二级标题（### 1.1 ...）
        elif re.match(r'^### \d+\.\d+', line):
            level = 2
            text = line.replace('### ', '').strip()
            headings.append((level, text, i))
        # 匹配三级标题（#### 1.1.1 ...）
        elif re.match(r'^#### \d+\.\d+\.\d+', line):
            level = 3
            text = line.replace('#### ', '').strip()
            headings.append((level, text, i))
    
    return headings

def generate_toc(headings):
    """生成目录"""
    if not headings:
        return ""
    
    toc_lines = ["## 📑 目录", ""]
    indent = "  "
    
    for level, text, _ in headings:
        # 生成锚点
        anchor = text.lower()
        anchor = re.sub(r'[^\w\s-]', '', anchor)
        anchor = re.sub(r'\s+', '-', anchor)
        anchor = anchor.strip('-')
        
        # 根据层级缩进
        prefix = indent * (level - 1)
        toc_lines.append(f"{prefix}- [{text}](#{anchor})")
    
    toc_lines.append("")
    toc_lines.append("---")
    toc_lines.append("")
    
    return "\n".join(toc_lines)

def add_toc_to_file(file_path):
    """为文件添加目录"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已有目录
        if '## 📑 目录' in content:
            print(f"跳过 {file_path}（已有目录）")
            return False
        
        # 查找概述部分的位置
        overview_match = re.search(r'## 📋 概述\n\n.*?\n\n---', content, re.DOTALL)
        if not overview_match:
            print(f"跳过 {file_path}（未找到概述部分）")
            return False
        
        # 提取标题
        headings = extract_headings(content)
        if not headings:
            print(f"跳过 {file_path}（未找到标题）")
            return False
        
        # 生成目录
        toc = generate_toc(headings)
        
        # 插入目录（在概述部分之后）
        overview_end = overview_match.end()
        new_content = content[:overview_end] + "\n\n" + toc + content[overview_end:]
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 已为 {file_path} 添加目录（{len(headings)}个标题）")
        return True
    
    except Exception as e:
        print(f"❌ 处理 {file_path} 时出错：{e}")
        return False

def main():
    """主函数"""
    base_dir = Path(__file__).parent.parent.parent
    
    # 查找所有.md文件（排除README和导航文件）
    md_files = []
    for pattern in ['**/*.md']:
        for file_path in base_dir.rglob(pattern):
            # 排除特定文件
            if any(exclude in str(file_path) for exclude in [
                'README.md', 'INDEX.md', 'NAVIGATION', '规范模板', '工具脚本'
            ]):
                continue
            # 只处理编号文档（如 01.01-xxx.md）
            if re.match(r'.*\d+\.\d+-', file_path.name):
                md_files.append(file_path)
    
    print(f"找到 {len(md_files)} 个文档文件\n")
    
    success_count = 0
    for file_path in sorted(md_files):
        if add_toc_to_file(file_path):
            success_count += 1
    
    print(f"\n完成！成功处理 {success_count}/{len(md_files)} 个文件")

if __name__ == '__main__':
    main()
