#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化修复 Sqlite 文件夹下所有 Markdown 文件的结构一致性问题
支持中文编号和 emoji 格式
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict
import shutil
from datetime import datetime

class StructureFixer:
    def __init__(self, root_dir: str, backup: bool = True, keep_chinese_numbering: bool = True, keep_emoji: bool = True):
        self.root_dir = Path(root_dir)
        self.backup = backup
        self.keep_chinese_numbering = keep_chinese_numbering
        self.keep_emoji = keep_emoji
        self.fixed_files = []
        self.errors = []
        
        # 中文数字映射
        self.chinese_to_num = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
        self.num_to_chinese = {v: k for k, v in self.chinese_to_num.items()}
        
    def find_markdown_files(self) -> List[Path]:
        """查找所有 Markdown 文件"""
        md_files = []
        for root, dirs, files in os.walk(self.root_dir):
            if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', '.structure_backup']):
                continue
            if '.structure_backup' in dirs:
                dirs.remove('.structure_backup')
            for file in files:
                if file.endswith('.md') and not file.startswith('structure_') and file != 'check_structure_consistency.py' and file != 'fix_structure_consistency.py':
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
        """移除标题开头的emoji（如果keep_emoji为False）"""
        if self.keep_emoji:
            return text
        emoji_pattern = r'^[📖🏗️🔬💡🚀📚🎯⚙️🔧✅❌⚠️💻🌐🔒📊🎨🔍💾🌍🔐📈📉🎓💼🏆🌟✨🎪🎭🎬🎲🎰🎱🎳🎴🎵🎶🎸🎹🎺🎻🥁🎤🎧📋📑]\s*'
        text = re.sub(emoji_pattern, '', text)
        return text.strip()
    
    def normalize_heading_numbering(self, headings: List[Tuple[int, str, int]], content: str) -> str:
        """标准化标题编号"""
        lines = content.split('\n')
        new_lines = lines.copy()
        
        level_numbers = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        prev_level = 1
        use_chinese = False  # 检测是否使用中文编号
        
        # 先检测是否使用中文编号
        for level, text, _ in headings:
            if level > 1:
                if re.match(r'^[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341]+[\s\.、]', text):
                    use_chinese = True
                    break
        
        for level, text, line_num in headings:
            if level == 1:
                cleaned_text = self.remove_emoji_from_heading(text)
                new_lines[line_num - 1] = f"# {cleaned_text}"
                continue
            
            cleaned_text = self.remove_emoji_from_heading(text)
            
            # 移除现有编号（数字或中文）
            cleaned_text = re.sub(r'^(\d+(\.\d+)*|[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341]+)[\s\.、]+', '', cleaned_text)
            cleaned_text = cleaned_text.strip()
            
            if level <= prev_level:
                for l in range(level + 1, 7):
                    level_numbers[l] = 0
            
            level_numbers[level] += 1
            
            # 生成编号
            if level == 2:
                if self.keep_chinese_numbering and use_chinese:
                    number = self.num_to_chinese.get(level_numbers[2], str(level_numbers[2]))
                    separator = '、' if use_chinese else '.'
                else:
                    number = str(level_numbers[2])
                    separator = '.'
            elif level == 3:
                if self.keep_chinese_numbering and use_chinese:
                    num2 = self.num_to_chinese.get(level_numbers[2], str(level_numbers[2]))
                    num3 = str(level_numbers[3])
                    number = f"{num2}.{num3}"
                    separator = '.'
                else:
                    number = f"{level_numbers[2]}.{level_numbers[3]}"
                    separator = '.'
            elif level == 4:
                number = f"{level_numbers[2]}.{level_numbers[3]}.{level_numbers[4]}"
                separator = '.'
            else:
                number = ""
                separator = ""
            
            hashes = '#' * level
            if number:
                new_lines[line_num - 1] = f"{hashes} {number}{separator} {cleaned_text}"
            else:
                new_lines[line_num - 1] = f"{hashes} {cleaned_text}"
            
            prev_level = level
        
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
            
            issues_fixed = []
            headings = self.extract_headings(content)
            
            if not headings:
                return False, ["文件没有标题"]
            
            needs_fix = False
            
            # 检查混合编号
            numbered_count = 0
            unnumbered_count = 0
            for h in headings:
                if h[0] > 1:
                    text = h[1]
                    if re.match(r'^(\d+(\.\d+)*|[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341]+)[\s\.、]', text):
                        numbered_count += 1
                    elif not re.match(r'^[📖🏗️🔬💡🚀📚🎯⚙️🔧✅❌⚠️💻🌐🔒📊🎨🔍💾🌍🔐📈📉🎓💼🏆🌟✨🎪🎭🎬🎲🎰🎱🎳🎴🎵🎶🎸🎹🎺🎻🥁🎤🎧📋📑]', text):
                        unnumbered_count += 1
            
            if numbered_count > 0 and unnumbered_count > 0:
                needs_fix = True
                issues_fixed.append("修复混合编号")
            
            # 检查层级跳跃
            prev_level = headings[0][0]
            for level, text, line_num in headings[1:]:
                if level > prev_level + 1:
                    needs_fix = True
                    issues_fixed.append(f"修复层级跳跃（行{line_num}）")
                    break
                if level > 0:
                    prev_level = level
            
            # 检查emoji（如果keep_emoji为False）
            if not self.keep_emoji:
                has_emoji = any(re.match(r'^[📖🏗️🔬💡🚀📚🎯⚙️🔧✅❌⚠️💻🌐🔒📊🎨🔍💾🌍🔐📈📉🎓💼🏆🌟✨🎪🎭🎬🎲🎰🎱🎳🎴🎵🎶🎸🎹🎺🎻🥁🎤🎧📋📑]', h[1]) for h in headings)
                if has_emoji:
                    needs_fix = True
                    issues_fixed.append("移除标题中的emoji")
            
            if not needs_fix:
                return False, []
            
            # 执行修复
            content = self.fix_heading_level_jumps(content)
            headings = self.extract_headings(content)
            content = self.normalize_heading_numbering(headings, content)
            
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
    script_dir = Path(__file__).parent
    # 保留中文编号和emoji
    fixer = StructureFixer(script_dir, backup=True, keep_chinese_numbering=True, keep_emoji=True)
    
    print("="*80)
    print("Sqlite 文件夹结构一致性修复工具")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = fixer.fix_all_files()
    
    import json
    report_file = script_dir / 'structure_fix_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n修复报告已保存到: {report_file}")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()
