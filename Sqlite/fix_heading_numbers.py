#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复Markdown文件中的章节标题格式
将中文数字编号改为阿拉伯数字编号
只修复实际的章节标题（##、### 等），不修改目录
"""

import os
import re
from pathlib import Path

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

def fix_heading_line(line: str) -> str:
    """修复单个标题行"""
    # 匹配：## 一、 标题 或 ### 四.1. 标题
    # 一级标题：## 一、 或 ## 二、
    pattern1 = r'^(##+)\s+([一二三四五六七八九十]+)、\s+(.+)$'
    match1 = re.match(pattern1, line)
    if match1:
        level = match1.group(1)
        chinese_num = match1.group(2)
        title = match1.group(3)
        arabic_num = chinese_to_arabic(chinese_num)
        return f'{level} {arabic_num}. {title}'
    
    # 二级标题：### 四.1. 或 ### 五.2.
    pattern2 = r'^(##+)\s+([一二三四五六七八九十]+)\.(\d+)\.\s+(.+)$'
    match2 = re.match(pattern2, line)
    if match2:
        level = match2.group(1)
        chinese_num = match2.group(2)
        sub_num = match2.group(3)
        title = match2.group(4)
        arabic_num = chinese_to_arabic(chinese_num)
        return f'{level} {arabic_num}.{sub_num}. {title}'
    
    # 二级标题（中文数字.中文数字）：### 四.一. 或 ### 五.二.
    pattern3 = r'^(##+)\s+([一二三四五六七八九十]+)\.([一二三四五六七八九十]+)\.\s+(.+)$'
    match3 = re.match(pattern3, line)
    if match3:
        level = match3.group(1)
        chinese_num1 = match3.group(2)
        chinese_num2 = match3.group(3)
        title = match3.group(4)
        arabic_num1 = chinese_to_arabic(chinese_num1)
        arabic_num2 = chinese_to_arabic(chinese_num2)
        return f'{level} {arabic_num1}.{arabic_num2}. {title}'
    
    # 三级标题：#### 七.2.1. 或 #### 九.1.1.
    pattern4 = r'^(##+)\s+([一二三四五六七八九十]+)\.(\d+)\.(\d+)\.\s+(.+)$'
    match4 = re.match(pattern4, line)
    if match4:
        level = match4.group(1)
        chinese_num = match4.group(2)
        sub_num1 = match4.group(3)
        sub_num2 = match4.group(4)
        title = match4.group(5)
        arabic_num = chinese_to_arabic(chinese_num)
        return f'{level} {arabic_num}.{sub_num1}.{sub_num2}. {title}'
    
    return line

def fix_file(file_path: Path) -> dict:
    """修复单个文件的章节标题"""
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
    changes_made = False
    
    for i, line in enumerate(lines):
        original_line = line
        stripped = line.rstrip('\n\r')
        
        # 只处理标题行（以 ## 开头）
        if re.match(r'^##+\s+', stripped):
            new_stripped = fix_heading_line(stripped)
            if new_stripped != stripped:
                changes_made = True
                result['changes'].append(f"第{i+1}行: {stripped[:50]}... -> {new_stripped[:50]}...")
                new_lines.append(new_stripped + '\n')
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
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
                     'fix_toc_format.py', 'fix_heading_numbers.py'}
    
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
