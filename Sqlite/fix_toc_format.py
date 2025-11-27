#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复Markdown文件的目录格式
将中文数字编号转换为阿拉伯数字编号，修复缩进问题
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# 中文数字到阿拉伯数字的映射
CHINESE_TO_ARABIC = {
    '一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
    '六': '6', '七': '7', '八': '8', '九': '9', '十': '10',
    '十一': '11', '十二': '12', '十三': '13', '十四': '14', '十五': '15',
    '十六': '16', '十七': '17', '十八': '18', '十九': '19', '二十': '20',
    '二十一': '21', '二十二': '22', '二十三': '23', '二十四': '24', '二十五': '25',
    '二十六': '26', '二十七': '27', '二十八': '28', '二十九': '29', '三十': '30'
}

def chinese_to_arabic(chinese_num: str) -> str:
    """将中文数字转换为阿拉伯数字"""
    # 处理带"十"的数字
    if chinese_num.startswith('十') and len(chinese_num) == 1:
        return '10'
    elif chinese_num.startswith('十') and len(chinese_num) > 1:
        # 如"十一"、"十二"
        return CHINESE_TO_ARABIC.get(chinese_num, chinese_num)
    else:
        return CHINESE_TO_ARABIC.get(chinese_num, chinese_num)

def fix_toc_title(line: str) -> str:
    """修复目录标题格式：## 二、 📑 目录 -> ## 1. 📑 目录"""
    # 匹配：## 二、 📑 目录 或 ## 一、 📑 目录
    pattern = r'^##\s+([一二三四五六七八九十]+)、\s+📑\s+目录'
    match = re.match(pattern, line)
    if match:
        # 目录标题始终应该是 1.
        return '## 1. 📑 目录'
    return line

def fix_toc_item(line: str, expected_indent: int = None) -> Tuple[str, int]:
    """
    修复目录项格式
    返回：(修复后的行, 实际缩进级别)
    """
    original_line = line
    leading_spaces = len(line) - len(line.lstrip())
    
    # 如果不是列表项，直接返回
    if not re.match(r'^\s*-\s+\[', line):
        return line, leading_spaces
    
    # 修复缩进问题（6个空格改为4个空格）
    if leading_spaces == 6:
        line = '    ' + line[6:]
        leading_spaces = 4
    elif leading_spaces == 8:
        line = '      ' + line[8:]  # 保持8个空格（三级子项）
        leading_spaces = 8
    
        # 修复一级子项（2个空格缩进）：- [一、 ...] ->   - [1. ...]
        # 匹配格式：- [一、 ...] 或   - [一、 ...]
        pattern1 = r'^(\s{0,2})-\s+\[([一二三四五六七八九十]+)、\s*(.+?)\]\(#(.+?)\)'
        match1 = re.match(pattern1, line)
        if match1:
            indent = match1.group(1)
            chinese_num = match1.group(2)
            title = match1.group(3)
            anchor = match1.group(4)
            arabic_num = chinese_to_arabic(chinese_num)
            # 确保是2个空格缩进
            return f'  - [{arabic_num}. {title}](#{anchor})', 2
        
        # 修复一级子项（无编号但有中文数字）：- [一、...] ->   - [1. ...]
        pattern1b = r'^(\s{0,2})-\s+\[([一二三四五六七八九十]+)、(.+?)\]\(#(.+?)\)'
        match1b = re.match(pattern1b, line)
        if match1b:
            indent = match1b.group(1)
            chinese_num = match1b.group(2)
            title = match1b.group(3)
            anchor = match1b.group(4)
            arabic_num = chinese_to_arabic(chinese_num)
            # 确保是2个空格缩进
            return f'  - [{arabic_num}. {title}](#{anchor})', 2
    
    # 修复二级子项（4个空格缩进）：    - [四.1. ...] ->     - [4.1. ...]
    pattern2 = r'^(\s{4,})-\s+\[([一二三四五六七八九十]+)\.(\d+)\.\s+(.+?)\]\(#(.+?)\)'
    match2 = re.match(pattern2, line)
    if match2:
        indent = match2.group(1)
        chinese_num = match2.group(2)
        sub_num = match2.group(3)
        title = match2.group(4)
        anchor = match2.group(5)
        arabic_num = chinese_to_arabic(chinese_num)
        # 确保是4个空格缩进
        return f'    - [{arabic_num}.{sub_num}. {title}](#{anchor})', 4
    
    # 修复二级子项（中文数字.中文数字格式）：    - [四.一. ...] ->     - [4.1. ...]
    pattern3 = r'^(\s{4,})-\s+\[([一二三四五六七八九十]+)\.([一二三四五六七八九十]+)\.\s+(.+?)\]\(#(.+?)\)'
    match3 = re.match(pattern3, line)
    if match3:
        indent = match3.group(1)
        chinese_num1 = match3.group(2)
        chinese_num2 = match3.group(3)
        title = match3.group(4)
        anchor = match3.group(5)
        arabic_num1 = chinese_to_arabic(chinese_num1)
        arabic_num2 = chinese_to_arabic(chinese_num2)
        # 确保是4个空格缩进
        return f'    - [{arabic_num1}.{arabic_num2}. {title}](#{anchor})', 4
    
    # 修复三级子项（6个空格缩进）：      - [9.2.1. ...] ->       - [9.2.1. ...]（保持6个空格，但修复中文数字）
    pattern4 = r'^(\s{6,})-\s+\[([一二三四五六七八九十]+)\.(\d+)\.(\d+)\.\s+(.+?)\]\(#(.+?)\)'
    match4 = re.match(pattern4, line)
    if match4:
        indent = match4.group(1)
        chinese_num = match4.group(2)
        sub_num1 = match4.group(3)
        sub_num2 = match4.group(4)
        title = match4.group(5)
        anchor = match4.group(6)
        arabic_num = chinese_to_arabic(chinese_num)
        # 保持6个空格缩进
        return f'      - [{arabic_num}.{sub_num1}.{sub_num2}. {title}](#{anchor})', 6
    
    return line, leading_spaces

def fix_file(file_path: Path) -> dict:
    """修复单个文件的目录格式"""
    result = {
        'file': str(file_path),
        'fixed': False,
        'changes': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        result['error'] = str(e)
        return result
    
    new_lines = []
    in_toc = False
    toc_start = None
    changes_made = False
    
    for i, line in enumerate(lines):
        original_line = line
        new_line = line
        
        # 检查是否进入目录章节
        if re.match(r'^##\s+[一二三四五六七八九十]+、\s+📑\s+目录', line):
            in_toc = True
            toc_start = i
            new_line = fix_toc_title(line.rstrip('\n')) + '\n'
            if new_line != original_line:
                changes_made = True
                result['changes'].append(f"第{i+1}行: 修复目录标题")
        
        # 检查是否退出目录章节
        elif in_toc and (line.startswith('##') or (line.strip() == '---' and i > toc_start + 5)):
            in_toc = False
        
        # 在目录章节内修复格式
        elif in_toc:
            new_line, indent = fix_toc_item(line.rstrip('\n'))
            new_line = new_line + '\n'
            if new_line != original_line:
                changes_made = True
                result['changes'].append(f"第{i+1}行: 修复目录项格式（缩进: {indent}）")
        
        new_lines.append(new_line)
    
    if changes_made:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            result['fixed'] = True
        except Exception as e:
            result['error'] = f"写入失败: {e}"
    
    return result

def main():
    """主函数"""
    root_dir = Path(__file__).parent
    
    # 排除的目录和文件
    exclude_dirs = {'00-项目导航', 'examples', 'tools', '.git'}
    exclude_files = {'README.md', 'CHANGELOG.md', 'CONTRIBUTING.md', 'LICENSE.md', 
                     'INDEX.md', 'NAVIGATION-按场景.md', 'NAVIGATION-按角色.md',
                     'QUICK-START.md', 'README-EN.md', 'readme.md', '00-全局目录树.md',
                     '00-概念索引.md', 'toc_format_check_report.md', 'check_toc_format.py',
                     'fix_toc_format.py'}
    
    files_to_fix = []
    for md_file in root_dir.rglob('*.md'):
        if any(exclude in md_file.parts for exclude in exclude_dirs):
            continue
        if md_file.name in exclude_files:
            continue
        files_to_fix.append(md_file)
    
    print(f"找到 {len(files_to_fix)} 个文件需要检查")
    print("=" * 80)
    
    fixed_count = 0
    error_count = 0
    
    for file_path in sorted(files_to_fix):
        rel_path = os.path.relpath(file_path, root_dir)
        print(f"处理: {rel_path}")
        
        result = fix_file(file_path)
        
        if result.get('error'):
            print(f"  ❌ 错误: {result['error']}")
            error_count += 1
        elif result['fixed']:
            print(f"  ✅ 已修复 ({len(result['changes'])} 处修改)")
            fixed_count += 1
            # 显示前3个修改
            for change in result['changes'][:3]:
                print(f"     - {change}")
            if len(result['changes']) > 3:
                print(f"     ... 还有 {len(result['changes']) - 3} 处修改")
        else:
            print(f"  ⏭️  无需修复")
    
    print("=" * 80)
    print(f"\n修复完成:")
    print(f"  总文件数: {len(files_to_fix)}")
    print(f"  已修复: {fixed_count}")
    print(f"  错误: {error_count}")
    print(f"  无需修复: {len(files_to_fix) - fixed_count - error_count}")

if __name__ == '__main__':
    main()
