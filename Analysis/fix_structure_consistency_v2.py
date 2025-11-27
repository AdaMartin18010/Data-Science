#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 Analysis 文件夹结构一致性问题（保留原有编号格式）
- 只修复真正的问题：重复编号、层级跳跃
- 不强制添加编号（保持原有格式）
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict
import shutil
from datetime import datetime

class StructureFixer:
    def __init__(self, root_dir: str, backup: bool = True):
        self.root_dir = Path(root_dir)
        self.backup = backup
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
                if file.endswith('.md') and not file.startswith('structure_') and file != 'check_structure_consistency.py' and file != 'fix_structure_consistency.py' and file != 'fix_structure_consistency_v2.py' and file != 'restore_from_backup.py':
                    md_files.append(Path(root) / file)
        return sorted(md_files)
    
    def backup_file(self, file_path: Path):
        """备份文件"""
        if self.backup:
            backup_dir = self.root_dir / '.structure_backup_v2' / file_path.relative_to(self.root_dir).parent
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / file_path.name
            shutil.copy2(file_path, backup_path)
    
    def extract_headings(self, content: str) -> List[Tuple[int, str, int]]:
        """提取所有标题"""
        headings = []
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append((level, text, i))
        return headings
    
    def fix_duplicate_numbering(self, content: str) -> str:
        """修复重复编号问题（如 ## 3. 1. -> ## 3.）"""
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            # 匹配标题行
            match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                
                # 检查是否有重复编号（如 "3. 1. " 或 "1. 1. "）
                duplicate_pattern = r'^(\d+)\s*\.\s+(\d+)\s*\.\s+'
                if re.match(duplicate_pattern, text):
                    # 移除重复的编号，只保留第一个
                    text = re.sub(duplicate_pattern, r'\1. ', text)
                    hashes = '#' * level
                    new_lines.append(f"{hashes} {text}")
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def fix_heading_level_jumps(self, content: str) -> str:
        """修复标题层级跳跃"""
        lines = content.split('\n')
        new_lines = []
        prev_level = 1
        
        for i, line in enumerate(lines):
            match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                
                if level > prev_level + 1:
                    new_level = min(level, prev_level + 1)
                    hashes = '#' * new_level
                    new_lines.append(f"{hashes} {text}")
                    prev_level = new_level
                else:
                    new_lines.append(line)
                    if level > 0:
                        prev_level = level
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def fix_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """修复单个文件"""
        try:
            self.backup_file(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            issues_fixed = []
            
            # 检查是否有重复编号
            if re.search(r'^##\s+\d+\s*\.\s+\d+\s*\.', content, re.MULTILINE):
                content = self.fix_duplicate_numbering(content)
                if content != original_content:
                    issues_fixed.append("修复重复编号")
            
            # 检查是否有层级跳跃
            headings = self.extract_headings(content)
            if headings:
                prev_level = headings[0][0]
                for level, text, line_num in headings[1:]:
                    if level > prev_level + 1:
                        content = self.fix_heading_level_jumps(content)
                        issues_fixed.append(f"修复层级跳跃（行{line_num}）")
                        break
                    if level > 0:
                        prev_level = level
            
            if not issues_fixed:
                return False, []
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True, issues_fixed
            
        except Exception as e:
            return False, [f"错误: {str(e)}"]
    
    def fix_all_files(self):
        """修复所有文件"""
        md_files = self.find_markdown_files()
        print(f"找到 {len(md_files)} 个 Markdown 文件\n")
        
        if self.backup:
            backup_dir = self.root_dir / '.structure_backup_v2'
            backup_dir.mkdir(exist_ok=True)
            print(f"备份目录: {backup_dir}\n")
        
        fixed_count = 0
        error_count = 0
        
        for i, file_path in enumerate(md_files, 1):
            rel_path = file_path.relative_to(self.root_dir)
            print(f"[{i}/{len(md_files)}] 处理: {rel_path}")
            
            success, issues = self.fix_file(file_path)
            
            if success:
                fixed_count += 1
                self.fixed_files.append({
                    'file': str(rel_path),
                    'issues': issues
                })
                print(f"  ✓ 已修复: {', '.join(issues)}")
            elif issues:
                error_count += 1
                self.errors.append({
                    'file': str(rel_path),
                    'error': issues[0]
                })
                print(f"  ✗ 错误: {issues[0]}")
            else:
                print(f"  - 无需修复")
        
        print(f"\n{'='*80}")
        print(f"修复完成!")
        print(f"  总文件数: {len(md_files)}")
        print(f"  已修复: {fixed_count}")
        print(f"  错误: {error_count}")
        print(f"  无需修复: {len(md_files) - fixed_count - error_count}")
        
        return {
            'total': len(md_files),
            'fixed': fixed_count,
            'errors': error_count,
            'fixed_files': self.fixed_files,
            'errors': self.errors
        }

def main():
    script_dir = Path(__file__).parent
    fixer = StructureFixer(script_dir, backup=True)
    
    print("="*80)
    print("Analysis 文件夹结构一致性修复工具 v2")
    print("（只修复重复编号和层级跳跃，保留原有编号格式）")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = fixer.fix_all_files()
    
    import json
    report_file = script_dir / 'structure_fix_report_v2.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n修复报告已保存到: {report_file}")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()
