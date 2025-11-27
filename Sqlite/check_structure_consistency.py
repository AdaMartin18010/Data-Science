#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 Sqlite 文件夹下所有 Markdown 文件的结构一致性
基于 Analysis 文件夹的检查脚本
"""

import os
import re
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple, Optional

class StructureChecker:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.issues = []
        self.file_stats = {}
        
    def find_markdown_files(self) -> List[Path]:
        """查找所有 Markdown 文件"""
        md_files = []
        for root, dirs, files in os.walk(self.root_dir):
            # 跳过一些不需要检查的目录
            if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', '.structure_backup']):
                continue
            # 排除备份目录
            if '.structure_backup' in dirs:
                dirs.remove('.structure_backup')
            for file in files:
                if file.endswith('.md') and not file.startswith('structure_') and file != 'check_structure_consistency.py' and file != 'fix_structure_consistency.py':
                    md_files.append(Path(root) / file)
        return sorted(md_files)
    
    def extract_headings(self, content: str) -> List[Tuple[int, str, int]]:
        """提取所有标题，返回 (级别, 标题文本, 行号)"""
        headings = []
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # 匹配 Markdown 标题
            match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append((level, text, i))
        return headings
    
    def check_toc(self, content: str) -> Optional[Dict]:
        """检查是否有目录（TOC）"""
        toc_patterns = [
            r'^##?\s*目录\s*$',
            r'^##?\s*Table of Contents\s*$',
            r'^##?\s*TOC\s*$',
            r'^##?\s*内容\s*$',
            r'^##?\s*Contents\s*$',
        ]
        
        lines = content.split('\n')
        toc_found = False
        toc_start = None
        toc_end = None
        
        for i, line in enumerate(lines):
            for pattern in toc_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    toc_found = True
                    toc_start = i + 1
                    break
            if toc_found:
                # 查找目录结束位置（下一个二级标题）
                for j in range(i + 1, min(i + 100, len(lines))):
                    if re.match(r'^##\s+', lines[j]):
                        toc_end = j
                        break
                if toc_end is None:
                    toc_end = min(i + 100, len(lines))
                break
        
        return {
            'found': toc_found,
            'start': toc_start,
            'end': toc_end
        } if toc_found else None
    
    def check_numbering_consistency(self, headings: List[Tuple[int, str, int]]) -> List[str]:
        """检查标题编号一致性"""
        issues = []
        
        # 检查是否有编号
        has_numbering = False
        no_numbering = False
        
        for level, text, line_num in headings:
            # 跳过H1（文件标题）
            if level == 1:
                continue
            # 检查是否有数字编号（如 "1. 标题" 或 "1.1 标题"）或中文编号（一、二、三）
            numbered_pattern = r'^(\d+(\.\d+)*|[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341]+)[\s\.、]'
            if re.match(numbered_pattern, text):
                has_numbering = True
            else:
                # 排除emoji和特殊符号开头的标题
                if not re.match(r'^[📖🏗️🔬💡🚀📚🎯⚙️🔧✅❌⚠️💻🌐🔒📊🎨🔍💾🌍🔐📈📉🎓💼🏆🌟✨🎪🎭🎬🎲🎰🎱🎳🎴🎵🎶🎸🎹🎺🎻🥁🎤🎧📋📑]', text):
                    no_numbering = True
        
        # 如果同时存在编号和未编号的标题，记录问题
        if has_numbering and no_numbering:
            issues.append("文件中同时存在编号和未编号的标题")
        elif has_numbering:
            # 检查编号是否连续
            issues.extend(self._check_numbering_sequence(headings))
        
        return issues
    
    def _check_numbering_sequence(self, headings: List[Tuple[int, str, int]]) -> List[str]:
        """检查编号序列是否连续"""
        issues = []
        level_numbers = {2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        prev_level = 1
        
        for level, text, line_num in headings:
            # 跳过H1（文件标题）
            if level == 1:
                continue
            
            # 检查数字编号或中文编号
            match = re.match(r'^(\d+(?:\.\d+)*|[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341]+)[\s\.、]', text)
            if match:
                number_str = match.group(1)
                
                # 如果是中文编号，转换为数字
                chinese_to_num = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
                if number_str in chinese_to_num:
                    numbers = [chinese_to_num[number_str]]
                else:
                    numbers = [int(n) for n in number_str.split('.')]
                
                # 如果层级下降，重置更深层级的编号
                if level <= prev_level:
                    for l in range(level + 1, 7):
                        level_numbers[l] = 0
                
                # 检查编号是否正确（简化检查，主要检查H2层级）
                if level == 2:
                    level_numbers[2] += 1
                    if numbers[0] != level_numbers[2]:
                        # 允许中文编号，不强制检查
                        if not any(c in number_str for c in chinese_to_num.keys()):
                            issues.append(
                                f"行 {line_num}: H2标题编号不连续。"
                                f"期望 {level_numbers[2]}，实际 {numbers[0]}"
                            )
                            level_numbers[2] = numbers[0]
                
                prev_level = level
            else:
                # 未编号的标题，重置该层级及更深层级的期望值
                for l in range(level, 7):
                    level_numbers[l] = 0
                prev_level = level
        
        return issues
    
    def check_heading_structure(self, headings: List[Tuple[int, str, int]]) -> List[str]:
        """检查标题结构（层级是否合理）"""
        issues = []
        
        if not headings:
            return issues
        
        prev_level = headings[0][0]
        
        for i, (level, text, line_num) in enumerate(headings[1:], 1):
            # 检查层级跳跃（不能跳过层级，如从 h2 直接到 h4）
            if level > prev_level + 1:
                issues.append(
                    f"行 {line_num}: 标题层级跳跃过大。"
                    f"从 h{prev_level} 跳到 h{level}"
                )
            prev_level = level
        
        return issues
    
    def analyze_file(self, file_path: Path) -> Dict:
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {
                'error': str(e),
                'headings': [],
                'toc': None,
                'issues': [f"无法读取文件: {e}"]
            }
        
        headings = self.extract_headings(content)
        toc = self.check_toc(content)
        
        issues = []
        issues.extend(self.check_numbering_consistency(headings))
        issues.extend(self.check_heading_structure(headings))
        
        return {
            'headings': headings,
            'toc': toc,
            'issues': issues,
            'has_numbering': any(re.match(r'^(\d+(\.\d+)*|[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341]+)[\s\.、]', h[1]) for h in headings if h[0] > 1),
            'heading_count': len(headings)
        }
    
    def check_all_files(self):
        """检查所有文件"""
        md_files = self.find_markdown_files()
        print(f"找到 {len(md_files)} 个 Markdown 文件\n")
        
        total_issues = 0
        files_with_issues = 0
        numbering_stats = {'numbered': 0, 'unnumbered': 0, 'mixed': 0}
        toc_stats = {'with_toc': 0, 'without_toc': 0}
        
        for file_path in md_files:
            rel_path = file_path.relative_to(self.root_dir)
            result = self.analyze_file(file_path)
            
            self.file_stats[str(rel_path)] = result
            
            if result.get('issues'):
                files_with_issues += 1
                total_issues += len(result['issues'])
                self.issues.append({
                    'file': str(rel_path),
                    'issues': result['issues']
                })
            
            # 统计编号情况
            if result.get('has_numbering'):
                if any(not re.match(r'^(\d+(\.\d+)*|[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341]+)[\s\.、]', h[1]) for h in result.get('headings', []) if h[0] > 1):
                    numbering_stats['mixed'] += 1
                else:
                    numbering_stats['numbered'] += 1
            else:
                numbering_stats['unnumbered'] += 1
            
            # 统计目录情况
            if result.get('toc') and result['toc'].get('found'):
                toc_stats['with_toc'] += 1
            else:
                toc_stats['without_toc'] += 1
        
        # 打印统计信息
        print("=" * 80)
        print("结构检查统计")
        print("=" * 80)
        print(f"\n总文件数: {len(md_files)}")
        print(f"有问题的文件: {files_with_issues}")
        print(f"总问题数: {total_issues}")
        
        print(f"\n标题编号统计:")
        print(f"  - 全部编号: {numbering_stats['numbered']}")
        print(f"  - 全部未编号: {numbering_stats['unnumbered']}")
        print(f"  - 混合编号: {numbering_stats['mixed']}")
        
        print(f"\n目录统计:")
        print(f"  - 有目录: {toc_stats['with_toc']}")
        print(f"  - 无目录: {toc_stats['without_toc']}")
        
        # 打印问题详情
        if self.issues:
            print("\n" + "=" * 80)
            print("问题详情（前20个）")
            print("=" * 80)
            for item in self.issues[:20]:
                print(f"\n文件: {item['file']}")
                for issue in item['issues']:
                    print(f"  - {issue}")
            if len(self.issues) > 20:
                print(f"\n... 还有 {len(self.issues) - 20} 个文件有问题")
        
        return {
            'total_files': len(md_files),
            'files_with_issues': files_with_issues,
            'total_issues': total_issues,
            'numbering_stats': numbering_stats,
            'toc_stats': toc_stats,
            'issues': self.issues
        }

def main():
    # 获取脚本所在目录
    script_dir = Path(__file__).parent
    checker = StructureChecker(script_dir)
    results = checker.check_all_files()
    
    # 保存结果到文件
    import json
    output_file = script_dir / 'structure_check_report.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n详细报告已保存到: {output_file}")

if __name__ == '__main__':
    main()
