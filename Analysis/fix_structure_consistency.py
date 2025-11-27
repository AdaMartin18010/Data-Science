#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化修复 Analysis 文件夹下所有 Markdown 文件的结构一致性问题
- 统一标题编号格式
- 修复标题层级跳跃
- 确保编号连续性
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
            # 跳过一些不需要检查的目录
            if any(skip in root for skip in ['.git', '__pycache__', 'node_modules']):
                continue
            for file in files:
                if file.endswith('.md') and not file.startswith('structure_') and file != 'check_structure_consistency.py':
                    md_files.append(Path(root) / file)
        return sorted(md_files)
    
    def backup_file(self, file_path: Path):
        """备份文件"""
        if self.backup:
            backup_dir = self.root_dir / '.structure_backup' / file_path.relative_to(self.root_dir).parent
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
    
    def remove_emoji_from_heading(self, text: str) -> str:
        """移除标题开头的emoji"""
        # 移除常见的emoji
        emoji_pattern = r'^[📖🏗️🔬💡🚀📚🎯⚙️🔧✅❌⚠️💻🌐🔒📊🎨🔍💾🌍🔐📈📉🎓💼🏆🌟✨🎪🎭🎬🎲🎰🎱🎳🎴🎵🎶🎸🎹🎺🎻🥁🎤🎧]\s*'
        text = re.sub(emoji_pattern, '', text)
        return text.strip()
    
    def normalize_heading_numbering(self, headings: List[Tuple[int, str, int]], content: str) -> str:
        """标准化标题编号"""
        lines = content.split('\n')
        new_lines = lines.copy()
        
        # 跟踪每个层级的当前编号
        level_numbers = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        prev_level = 1  # H1是文件标题
        
        # 从前向后处理
        for level, text, line_num in headings:
            # 处理H1（文件标题）
            if level == 1:
                # 清理H1标题，移除emoji
                cleaned_text = self.remove_emoji_from_heading(text)
                new_lines[line_num - 1] = f"# {cleaned_text}"
                continue
            
            # 移除emoji
            cleaned_text = self.remove_emoji_from_heading(text)
            
            # 移除现有编号（包括重复编号，如 "3. 1." -> ""）
            # 先移除所有可能的编号模式（包括重复编号）
            cleaned_text = re.sub(r'^(\d+\s*\.\s*)+', '', cleaned_text)  # 移除重复编号如 "3. 1. " 或 "1. 1. "
            cleaned_text = re.sub(r'^\d+(\.\d+)*\s*\.?\s*', '', cleaned_text)  # 移除标准编号如 "1. " 或 "1.1. "
            cleaned_text = cleaned_text.strip()
            
            # 确定应该使用的编号
            if level <= prev_level:
                # 重置更深层级的编号
                for l in range(level + 1, 7):
                    level_numbers[l] = 0
            
            # 增加当前层级编号
            level_numbers[level] += 1
            
            # 生成编号字符串
            if level == 2:
                number = str(level_numbers[2])
            elif level == 3:
                number = f"{level_numbers[2]}.{level_numbers[3]}"
            elif level == 4:
                number = f"{level_numbers[2]}.{level_numbers[3]}.{level_numbers[4]}"
            elif level == 5:
                number = f"{level_numbers[2]}.{level_numbers[3]}.{level_numbers[4]}.{level_numbers[5]}"
            elif level == 6:
                number = f"{level_numbers[2]}.{level_numbers[3]}.{level_numbers[4]}.{level_numbers[5]}.{level_numbers[6]}"
            else:
                number = ""
            
            # 构建新的标题行
            hashes = '#' * level
            new_lines[line_num - 1] = f"{hashes} {number}. {cleaned_text}" if number else f"{hashes} {cleaned_text}"
            
            prev_level = level
        
        return '\n'.join(new_lines)
    
    def fix_heading_level_jumps(self, content: str) -> str:
        """修复标题层级跳跃"""
        lines = content.split('\n')
        new_lines = []
        prev_level = 1  # H1是文件标题
        
        for i, line in enumerate(lines):
            match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                
                # 检查层级跳跃
                if level > prev_level + 1:
                    # 需要插入中间层级
                    # 但为了安全，我们只调整当前标题的层级，不插入新内容
                    # 将跳跃的标题降级到合理的层级
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
            # 备份文件
            self.backup_file(file_path)
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            issues_fixed = []
            
            # 提取标题
            headings = self.extract_headings(content)
            
            if not headings:
                return False, ["文件没有标题"]
            
            # 检查是否需要修复
            needs_fix = False
            
            # 检查是否有混合编号（更严格的检查）
            numbered_count = 0
            unnumbered_count = 0
            has_duplicate_numbering = False
            for h in headings:
                if h[0] > 1:  # 跳过H1
                    text = h[1]
                    # 检查是否有重复编号（如 "1. 1. " 或 "3. 1. "）
                    if re.match(r'^(\d+\s*\.\s*){2,}', text):
                        has_duplicate_numbering = True
                        numbered_count += 1
                    # 检查是否有标准编号
                    elif re.match(r'^\d+(\.\d+)*\s*\.?\s+', text):
                        numbered_count += 1
                    elif not re.match(r'^[📖🏗️🔬💡🚀📚🎯⚙️🔧✅❌⚠️💻🌐🔒📊🎨🔍💾🌍🔐📈📉🎓💼🏆🌟✨🎪🎭🎬🎲🎰🎱🎳🎴🎵🎶🎸🎹🎺🎻🥁🎤🎧]', text):
                        unnumbered_count += 1
            
            # 如果有编号和未编号的标题，或者编号顺序不对，都需要修复
            if has_duplicate_numbering:
                needs_fix = True
                issues_fixed.append("修复重复编号")
            if numbered_count > 0 and unnumbered_count > 0:
                needs_fix = True
                issues_fixed.append("修复混合编号")
            elif numbered_count > 0:
                # 检查编号顺序是否正确
                prev_numbers = {}
                for level, text, line_num in headings:
                    if level > 1:
                        match = re.match(r'^(\d+(?:\.\d+)*)\s*\.?\s+', text)
                        if match:
                            numbers = [int(n) for n in match.group(1).split('.')]
                            # 检查编号是否连续
                            if level in prev_numbers:
                                expected = prev_numbers[level] + 1
                                if numbers[0] != expected:
                                    needs_fix = True
                                    issues_fixed.append("修复编号顺序")
                                    break
                            prev_numbers[level] = numbers[0]
                            # 重置更深层级的编号
                            for l in range(level + 1, 7):
                                if l in prev_numbers:
                                    del prev_numbers[l]
            
            # 检查是否有层级跳跃
            prev_level = headings[0][0]
            for level, text, line_num in headings[1:]:
                if level > prev_level + 1:
                    needs_fix = True
                    issues_fixed.append(f"修复层级跳跃（行{line_num}）")
                    break
                if level > 0:
                    prev_level = level
            
            # 检查是否有emoji
            has_emoji = any(re.match(r'^[📖🏗️🔬💡🚀📚🎯⚙️🔧✅❌⚠️💻🌐🔒📊🎨🔍💾🌍🔐📈📉🎓💼🏆🌟✨🎪🎭🎬🎲🎰🎱🎳🎴🎵🎶🎸🎹🎺🎻🥁🎤🎧]', h[1]) for h in headings)
            if has_emoji:
                needs_fix = True
                issues_fixed.append("移除标题中的emoji")
            
            if not needs_fix:
                return False, []
            
            # 执行修复
            # 1. 先修复层级跳跃
            content = self.fix_heading_level_jumps(content)
            
            # 2. 重新提取标题（因为层级可能已改变）
            headings = self.extract_headings(content)
            
            # 3. 标准化编号
            content = self.normalize_heading_numbering(headings, content)
            
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
            backup_dir = self.root_dir / '.structure_backup'
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
    # 获取脚本所在目录
    script_dir = Path(__file__).parent
    fixer = StructureFixer(script_dir, backup=True)
    
    print("="*80)
    print("Analysis 文件夹结构一致性修复工具")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = fixer.fix_all_files()
    
    # 保存修复报告
    import json
    report_file = script_dir / 'structure_fix_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n修复报告已保存到: {report_file}")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()
