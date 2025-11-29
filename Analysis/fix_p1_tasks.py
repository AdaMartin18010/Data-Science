#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复Analysis项目P1任务：
1. 修复高优先级文件的结构问题
2. 统一标题编号格式
3. 修复标题层级跳跃
4. 为文件添加标准目录
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import json
from datetime import datetime

class P1TaskFixer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.fixed_files = []
        self.errors = []
        
    def find_markdown_files(self) -> List[Path]:
        """查找所有 Markdown 文件"""
        md_files = []
        for root, dirs, files in os.walk(self.root_dir):
            if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', '.structure_backup']):
                continue
            if '.structure_backup' in dirs:
                dirs.remove('.structure_backup')
            for file in files:
                if file.endswith('.md') and not file.startswith('structure_') and file not in ['check_structure_consistency.py', 'fix_structure_consistency.py', 'fix_structure_consistency_v2.py', 'restore_from_backup.py', 'fix_p1_tasks.py']:
                    md_files.append(Path(root) / file)
        return sorted(md_files)
    
    def extract_headings(self, content: str) -> List[Tuple[int, str, int, Optional[str]]]:
        """提取所有标题，返回 (级别, 标题文本, 行号, 编号)，排除代码块中的标题"""
        headings = []
        lines = content.split('\n')
        in_code_block = False
        code_block_pattern = re.compile(r'^```')
        
        for i, line in enumerate(lines, 1):
            # 检查是否进入或退出代码块
            if code_block_pattern.match(line.strip()):
                in_code_block = not in_code_block
                continue
            
            # 跳过代码块中的内容
            if in_code_block:
                continue
            
            # 匹配标题（不在代码块中）
            match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                # 提取编号（如果有）
                num_match = re.match(r'^(\d+(?:\.\d+)*)\.?\s+(.+)$', text)
                if num_match:
                    numbering = num_match.group(1)
                    title = num_match.group(2)
                else:
                    numbering = None
                    title = text
                headings.append((level, title, i, numbering))
        return headings
    
    def generate_toc(self, headings: List[Tuple[int, str, int, Optional[str]]], max_level: int = 3) -> str:
        """生成目录"""
        if not headings:
            return ""
        
        toc_lines = ["## 📑 目录", ""]
        indent_stack = [0]  # 跟踪缩进层级
        
        for level, title, line_num, numbering in headings:
            if level > max_level:
                continue
            
            # 生成链接锚点（兼容中文和特殊字符）
            # 移除编号部分（如果存在）
            clean_title = title
            if numbering:
                clean_title = re.sub(r'^\d+(?:\.\d+)*\.?\s*', '', title)
            
            # 生成锚点：转换为小写，替换空格为连字符，移除特殊字符
            # GitHub风格的锚点生成：保留中文、英文、数字、连字符
            anchor = clean_title.lower()
            # 替换空格为连字符
            anchor = re.sub(r'\s+', '-', anchor)
            # 移除特殊字符，保留中文、英文、数字、连字符
            anchor = re.sub(r'[^\w\u4e00-\u9fff-]', '', anchor)
            # 移除多余的连字符
            anchor = re.sub(r'-+', '-', anchor)
            anchor = anchor.strip('-')
            
            # 计算缩进
            while len(indent_stack) > level:
                indent_stack.pop()
            
            indent = "  " * (level - 1)
            link_text = title
            if numbering:
                link_text = f"{numbering}. {title}"
            
            toc_lines.append(f"{indent}- [{link_text}](#{anchor})")
            indent_stack.append(level)
        
        return "\n".join(toc_lines) + "\n\n---\n"
    
    def fix_heading_level_jumps(self, content: str) -> Tuple[str, List[str]]:
        """修复标题层级跳跃问题，排除代码块中的标题"""
        lines = content.split('\n')
        new_lines = []
        issues_fixed = []
        prev_level = 0
        in_code_block = False
        code_block_pattern = re.compile(r'^```')
        
        for i, line in enumerate(lines):
            # 检查是否进入或退出代码块
            if code_block_pattern.match(line.strip()):
                in_code_block = not in_code_block
                new_lines.append(line)
                continue
            
            # 跳过代码块中的内容（不处理）
            if in_code_block:
                new_lines.append(line)
                continue
            
            # 匹配标题（不在代码块中）
            match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                
                # 检查层级跳跃
                if prev_level > 0 and level > prev_level + 1:
                    # 需要插入中间层级
                    new_level = prev_level + 1
                    # 调整当前标题层级
                    new_line = '#' * new_level + ' ' + text
                    new_lines.append(new_line)
                    issues_fixed.append(f"行{i+1}: 修复层级跳跃 (h{level} -> h{new_level})")
                    prev_level = new_level
                else:
                    new_lines.append(line)
                    if level > 0:
                        prev_level = level
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines), issues_fixed
    
    def add_toc_to_file(self, file_path: Path, max_level: int = 3) -> Tuple[bool, List[str]]:
        """为文件添加目录"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已有目录
            if re.search(r'^##\s*[📑目录|目录|Table of Contents]', content, re.MULTILINE | re.IGNORECASE):
                return False, ["已有目录"]
            
            # 提取标题
            headings = self.extract_headings(content)
            if not headings:
                return False, ["无标题"]
            
            # 生成目录
            toc = self.generate_toc(headings, max_level)
            
            # 找到插入位置（在第一个标题之后）
            lines = content.split('\n')
            insert_pos = 0
            for i, line in enumerate(lines):
                if re.match(r'^#\s+', line):
                    insert_pos = i + 1
                    break
            
            # 插入目录
            new_lines = lines[:insert_pos] + [toc] + lines[insert_pos:]
            new_content = '\n'.join(new_lines)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True, ["已添加目录"]
            
        except Exception as e:
            return False, [f"错误: {str(e)}"]
    
    def fix_high_priority_files(self):
        """修复高优先级文件"""
        high_priority_files = [
            "1-数据库系统/1.2-MySQL/MySQL国际化Wiki标准与知识规范对齐指南.md",
            "1-数据库系统/1.3-NoSQL/1.3.1-MongoDB概念定义国际化标准示例.md",
            "1-数据库系统/1.3-NoSQL/1.3.2-Cassandra概念定义国际化标准示例.md",
            "1-数据库系统/1.3-NoSQL/1.3.3-Neo4j概念定义国际化标准示例.md",
            "3-数据模型与算法/3.1-数据科学基础理论/3.1.22-数据科学与机器学习理论体系.md",
            "4-软件架构与工程/4.1-架构设计/4.1.13-微服务架构设计.md",
            "4-软件架构与工程/4.1-架构设计/4.1.14-云原生架构实践.md",
            "4-软件架构与工程/4.1-架构设计/4.1.15-DevOps与CI-CD.md",
            "8-形式理论深化/8.3-Petri网理论深化/8.3.4-Petri网应用场景深化.md",
            "8-形式理论深化/8.7-博弈论深化/8.7.2-机制设计理论深化.md",
        ]
        
        results = []
        for rel_path in high_priority_files:
            file_path = self.root_dir / rel_path
            if not file_path.exists():
                results.append({
                    "file": rel_path,
                    "status": "not_found",
                    "issues": []
                })
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 修复层级跳跃
                new_content, issues = self.fix_heading_level_jumps(content)
                
                # 添加目录（如果没有）
                has_toc = re.search(r'^##\s*[📑目录|目录|Table of Contents]', content, re.MULTILINE | re.IGNORECASE)
                if not has_toc:
                    headings = self.extract_headings(new_content)
                    if headings:
                        toc = self.generate_toc(headings)
                        lines = new_content.split('\n')
                        insert_pos = 0
                        for i, line in enumerate(lines):
                            if re.match(r'^#\s+', line):
                                insert_pos = i + 1
                                break
                        new_lines = lines[:insert_pos] + [toc] + lines[insert_pos:]
                        new_content = '\n'.join(new_lines)
                        issues.append("已添加目录")
                
                # 写入文件
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    results.append({
                        "file": rel_path,
                        "status": "fixed",
                        "issues": issues
                    })
                    self.fixed_files.append(rel_path)
                else:
                    results.append({
                        "file": rel_path,
                        "status": "no_changes",
                        "issues": []
                    })
                    
            except Exception as e:
                results.append({
                    "file": rel_path,
                    "status": "error",
                    "issues": [f"错误: {str(e)}"]
                })
                self.errors.append(f"{rel_path}: {str(e)}")
        
        return results
    
    def add_toc_to_all_files(self, max_level: int = 3):
        """为所有文件添加目录"""
        md_files = self.find_markdown_files()
        results = []
        
        for file_path in md_files:
            rel_path = str(file_path.relative_to(self.root_dir))
            
            # 跳过已有目录的文件
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if re.search(r'^##\s*[📑目录|目录|Table of Contents]', content, re.MULTILINE | re.IGNORECASE):
                    continue
                
                success, issues = self.add_toc_to_file(file_path, max_level)
                if success:
                    results.append({
                        "file": rel_path,
                        "status": "added_toc",
                        "issues": issues
                    })
                    self.fixed_files.append(rel_path)
                    
            except Exception as e:
                results.append({
                    "file": rel_path,
                    "status": "error",
                    "issues": [f"错误: {str(e)}"]
                })
                self.errors.append(f"{rel_path}: {str(e)}")
        
        return results

def main():
    script_dir = Path(__file__).parent
    fixer = P1TaskFixer(script_dir)
    
    print("="*80)
    print("Analysis项目P1任务批量修复工具")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 任务1: 修复高优先级文件
    print("任务1: 修复高优先级文件的结构问题...")
    high_priority_results = fixer.fix_high_priority_files()
    print(f"  处理了 {len(high_priority_results)} 个文件")
    fixed_count = sum(1 for r in high_priority_results if r['status'] == 'fixed')
    print(f"  修复了 {fixed_count} 个文件\n")
    
    # 任务2: 为所有文件添加目录
    print("任务2: 为所有文件添加目录...")
    toc_results = fixer.add_toc_to_all_files()
    print(f"  为 {len(toc_results)} 个文件添加了目录\n")
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "high_priority_files": high_priority_results,
        "toc_added": toc_results,
        "summary": {
            "total_fixed": len(fixer.fixed_files),
            "total_errors": len(fixer.errors)
        }
    }
    
    report_file = script_dir / 'p1_tasks_fix_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"修复报告已保存到: {report_file}")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n总计修复: {len(fixer.fixed_files)} 个文件")
    print(f"错误: {len(fixer.errors)} 个")

if __name__ == '__main__':
    main()
