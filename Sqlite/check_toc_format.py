#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查Markdown文件的目录格式是否符合模板
模板文件：cases/01-Chrome浏览器案例.md
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# 模板格式特征
TEMPLATE_FEATURES = {
    'toc_title': r'^##\s+1\.\s+📑\s+目录',  # 目录标题格式：## 1. 📑 目录
    'main_list_item': r'^\s*-\s+\[',  # 主列表项：- [（0个空格）
    'level1_item': r'^\s{2}-\s+\[\d+\.',  # 一级子项：  - [1. （2个空格）
    'level2_item': r'^\s{4}-\s+\[\d+\.\d+\.',  # 二级子项：    - [3.1. （4个空格）
}

def check_toc_format(file_path: Path) -> Dict:
    """检查单个文件的目录格式"""
    result = {
        'file': str(file_path),
        'has_toc': False,
        'toc_title_correct': False,
        'has_main_sections': False,
        'has_sub_sections': False,
        'indent_issues': [],
        'numbering_issues': [],
        'needs_fix': False,
        'issues': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        result['issues'].append(f"读取文件失败: {e}")
        result['needs_fix'] = True
        return result
    
    # 查找目录章节
    toc_start = None
    toc_end = None
    in_toc = False
    
    for i, line in enumerate(lines):
        # 检查目录标题（阿拉伯数字格式 - 正确格式）
        if re.match(TEMPLATE_FEATURES['toc_title'], line):
            result['has_toc'] = True
            result['toc_title_correct'] = True
            toc_start = i
            in_toc = True
            continue
        
        # 检查其他格式的目录标题（中文数字格式 - 需要修复）
        if re.match(r'^##\s+[一二三四五六七八九十]+、\s+📑\s+目录', line):
            result['has_toc'] = True
            result['toc_title_correct'] = False
            result['issues'].append(f"第{i+1}行: 目录标题使用中文数字，应为阿拉伯数字 '## 1. 📑 目录'")
            result['needs_fix'] = True
            toc_start = i
            in_toc = True
            continue
        
        if in_toc:
            # 检查是否结束目录（遇到下一个 ## 标题或 --- 分隔符）
            if line.startswith('##') and i > toc_start:
                toc_end = i
                break
            if line.strip() == '---' and i > toc_start + 5:  # 至少要有几行内容
                toc_end = i
                break
    
    if not result['has_toc']:
        result['issues'].append("缺少目录章节")
        result['needs_fix'] = True
        return result
    
    if toc_start is None:
        return result
    
    # 分析目录内容
    toc_lines = lines[toc_start:toc_end] if toc_end else lines[toc_start:]
    
    for i, line in enumerate(toc_lines, start=toc_start+1):
        line_num = i + 1
        
        # 跳过空行和目录标题
        if not line.strip() or re.match(TEMPLATE_FEATURES['toc_title'], line):
            continue
        
        # 检查是否是列表项
        if not re.match(r'^\s*-\s+\[', line):
            continue
        
        leading_spaces = len(line) - len(line.lstrip())
        
        # 检查主列表项（文档标题，0个空格）
        if leading_spaces == 0:
            # 主列表项通常是文档标题，不需要编号检查
            continue
        
        # 检查一级子项（章节，如 1. 2. 3.，2个空格）
        elif leading_spaces == 2:
            result['has_main_sections'] = True
            # 检查编号格式
            if re.match(TEMPLATE_FEATURES['level1_item'], line):
                pass  # 格式正确
            else:
                # 检查是否是中文数字编号
                if re.match(r'^\s{2}-\s+\[[一二三四五六七八九十]+、', line):
                    result['numbering_issues'].append(f"第{line_num}行: 一级子项使用中文数字编号，应为阿拉伯数字")
                    result['needs_fix'] = True
                elif re.match(r'^\s{2}-\s+\[[^\d]', line):
                    # 可能是文档标题的子项，允许没有编号
                    pass
        
        # 检查二级子项（子章节，如 3.1. 3.2.，4个空格）
        elif leading_spaces == 4:
            result['has_sub_sections'] = True
            # 检查编号格式
            if re.match(TEMPLATE_FEATURES['level2_item'], line):
                pass  # 格式正确
            else:
                # 检查是否是中文数字编号
                if re.match(r'^\s{4}-\s+\[[一二三四五六七八九十]+\.\d+\.', line):
                    result['numbering_issues'].append(f"第{line_num}行: 二级子项使用中文数字编号，应为阿拉伯数字")
                    result['needs_fix'] = True
                elif re.match(r'^\s{4}-\s+\[\d+\.\d+', line):
                    # 可能是其他格式，需要检查
                    pass
        
        # 其他缩进（可能是格式错误）
        else:
            if leading_spaces > 4:
                result['indent_issues'].append(f"第{line_num}行: 缩进过多 ({leading_spaces}个空格，应为0/2/4个)")
                result['needs_fix'] = True
            elif leading_spaces == 1 or leading_spaces == 3:
                result['indent_issues'].append(f"第{line_num}行: 缩进不正确 ({leading_spaces}个空格，应为0/2/4个)")
                result['needs_fix'] = True
    
    # 汇总问题
    if result['indent_issues']:
        result['issues'].extend(result['indent_issues'])
    if result['numbering_issues']:
        result['issues'].extend(result['numbering_issues'])
    
    return result

def scan_all_md_files(root_dir: Path) -> List[Dict]:
    """扫描所有Markdown文件"""
    results = []
    
    # 排除的目录和文件
    exclude_dirs = {'00-项目导航', 'examples', 'tools', '.git'}
    exclude_files = {'README.md', 'CHANGELOG.md', 'CONTRIBUTING.md', 'LICENSE.md', 
                     'INDEX.md', 'NAVIGATION-按场景.md', 'NAVIGATION-按角色.md',
                     'QUICK-START.md', 'README-EN.md', 'readme.md', '00-全局目录树.md',
                     '00-概念索引.md'}
    
    for md_file in root_dir.rglob('*.md'):
        # 跳过排除的目录
        if any(exclude in md_file.parts for exclude in exclude_dirs):
            continue
        
        # 跳过排除的文件
        if md_file.name in exclude_files:
            continue
        
        result = check_toc_format(md_file)
        results.append(result)
    
    return results

def main():
    """主函数"""
    root_dir = Path(__file__).parent
    print(f"扫描目录: {root_dir}")
    print("=" * 80)
    
    results = scan_all_md_files(root_dir)
    
    # 统计
    total_files = len(results)
    needs_fix = [r for r in results if r['needs_fix']]
    has_toc = [r for r in results if r['has_toc']]
    correct_format = [r for r in results if r['has_toc'] and not r['needs_fix']]
    
    print(f"\n统计结果:")
    print(f"  总文件数: {total_files}")
    print(f"  有目录的文件: {len(has_toc)}")
    print(f"  格式正确的文件: {len(correct_format)}")
    print(f"  需要修复的文件: {len(needs_fix)}")
    print("=" * 80)
    
    # 显示需要修复的文件
    if needs_fix:
        print(f"\n需要修复的文件 ({len(needs_fix)} 个):\n")
        for result in sorted(needs_fix, key=lambda x: x['file']):
            rel_path = os.path.relpath(result['file'], root_dir)
            print(f"  {rel_path}")
            for issue in result['issues'][:3]:  # 只显示前3个问题
                print(f"    - {issue}")
            if len(result['issues']) > 3:
                print(f"    ... 还有 {len(result['issues']) - 3} 个问题")
            print()
    else:
        print("\n✅ 所有文件的目录格式都正确！")
    
    # 生成报告
    report_file = root_dir / 'toc_format_check_report.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# 目录格式检查报告\n\n")
        f.write(f"**检查时间**: {Path(__file__).stat().st_mtime}\n\n")
        f.write(f"**模板文件**: `cases/01-Chrome浏览器案例.md`\n\n")
        f.write("## 统计结果\n\n")
        f.write(f"- 总文件数: {total_files}\n")
        f.write(f"- 有目录的文件: {len(has_toc)}\n")
        f.write(f"- 格式正确的文件: {len(correct_format)}\n")
        f.write(f"- 需要修复的文件: {len(needs_fix)}\n\n")
        f.write("## 需要修复的文件详情\n\n")
        
        for result in sorted(needs_fix, key=lambda x: x['file']):
            rel_path = os.path.relpath(result['file'], root_dir)
            f.write(f"### {rel_path}\n\n")
            for issue in result['issues']:
                f.write(f"- {issue}\n")
            f.write("\n")
    
    print(f"\n详细报告已保存到: {report_file}")

if __name__ == '__main__':
    main()
