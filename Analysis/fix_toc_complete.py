#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整修复目录结构：
1. 为缺少目录的文件添加目录
2. 移除多余的目录，只保留一个
3. 确保目录格式统一
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict

def extract_headings(content: str) -> List[Tuple[int, str, str]]:
    """提取所有标题，返回(级别, 标题文本, 原始行)"""
    headings = []
    lines = content.split('\n')
    in_code_block = False
    code_block_markers = ['```', '~~~']
    
    for i, line in enumerate(lines):
        # 检测代码块
        stripped = line.strip()
        
        # 检测代码块开始/结束
        if stripped.startswith('```') or stripped.startswith('~~~'):
            marker_char = stripped[0] if stripped else ''
            if len(stripped) >= 3 and stripped[0] == stripped[1] == stripped[2]:
                in_code_block = not in_code_block
            continue
        
        # 跳过代码块内的所有内容
        if in_code_block:
            continue
        
        # 跳过空行
        if not stripped:
            continue
        
        # 跳过缩进的行（可能是代码或列表项）
        if line.startswith('    ') or line.startswith('\t'):
            continue
        
        # 跳过看起来像代码注释的行
        if stripped.startswith('#') and not re.match(r'^#{1,6}\s+[^#]', line):
            continue
        
        # 跳过看起来像代码输出的行
        if re.match(r'^[\[\{\(].*[\]\}\)]', stripped) and any(c in stripped for c in ["'", '"', 'b\'', 'b"']):
            continue
        
        # 跳过配置文件名
        if re.match(r'^[a-z_]+\.(conf|config|yaml|yml|json|xml)$', stripped, re.IGNORECASE):
            continue
        
        # 匹配标题
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            
            # 过滤掉明显不是标题的内容
            if len(text) < 2:
                continue
            if re.match(r'^[\[\{\(].*[\]\}\)]$', text) and any(c in text for c in ["'", '"', 'b\'']):
                continue
            if text.startswith('b\'') or text.startswith('b"'):
                continue
            
            headings.append((level, text, line))
    
    return headings

def generate_anchor(text: str) -> str:
    """生成GitHub风格的锚点"""
    anchor = text.lower()
    anchor = re.sub(r'\s+', '-', anchor)
    anchor = re.sub(r'[^\w\u4e00-\u9fff\-\(\)]', '', anchor)
    anchor = re.sub(r'-+', '-', anchor)
    anchor = anchor.strip('-')
    return anchor

def generate_toc(headings: List[Tuple[int, str, str]]) -> str:
    """生成目录，保留标题编号"""
    if not headings:
        return ""
    
    toc_lines = ["## 📑 目录", ""]
    
    # 第一个标题应该是H1，作为文档标题
    if headings[0][0] == 1:
        doc_title = headings[0][1]
        doc_anchor = generate_anchor(doc_title)
        toc_lines.append(f"- [{doc_title}](#{doc_anchor})")
        toc_lines.append("  - [📑 目录](#-目录)")
        start_idx = 1
    else:
        start_idx = 0
    
    # 处理其他标题
    stack = []
    
    for i in range(start_idx, len(headings)):
        level, text, _ = headings[i]
        
        # 跳过目录标题本身
        if text == "📑 目录" or text == "目录":
            continue
        
        # 确定缩进
        while stack and stack[-1][0] >= level:
            stack.pop()
        
        indent = "  " * len(stack)
        anchor = generate_anchor(text)
        
        toc_item = f"{indent}- [{text}](#{anchor})"
        toc_lines.append(toc_item)
        
        stack.append((level, text))
    
    return "\n".join(toc_lines)

def find_toc_positions(content: str) -> List[Tuple[int, int]]:
    """找到所有目录的位置（开始行，结束行），排除代码块中的"""
    lines = content.split('\n')
    toc_positions = []
    in_code_block = False
    code_block_markers = ['```', '~~~']
    
    for i, line in enumerate(lines):
        # 检测代码块
        stripped = line.strip()
        if stripped.startswith('```') or stripped.startswith('~~~'):
            marker_char = stripped[0] if stripped else ''
            if len(stripped) >= 3 and stripped[0] == marker_char == stripped[1] == stripped[2]:
                in_code_block = not in_code_block
            continue
        
        # 跳过代码块内的内容
        if in_code_block:
            continue
        
        # 检查是否是目录标题（支持中英文）
        if re.match(r'^##\s+[📑]?\s*目录', line) or re.match(r'^##\s+.*[Tt]able.*[Cc]ontents', line):
            # 找到目录开始
            start = i
            # 找到目录结束（下一个同级或更高级标题，或分隔线）
            end = len(lines)
            for j in range(i + 1, len(lines)):
                if re.match(r'^---', lines[j]):
                    end = j
                    break
                if re.match(r'^##\s+', lines[j]) and not re.match(r'^##\s+[📑]?\s*目录', lines[j]):
                    end = j
                    break
                if re.match(r'^#\s+', lines[j]):
                    end = j
                    break
            toc_positions.append((start, end))
    
    return toc_positions

def fix_document(file_path: Path) -> Tuple[bool, str, str]:
    """修复单个文档的目录结构"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"读取文件失败: {e}", ""
    
    # 检查是否是占位文件
    if '本文件由自动化工具创建' in content:
        return False, "占位文件，跳过", ""
    
    # 提取标题
    headings = extract_headings(content)
    
    if not headings:
        return False, "没有找到标题", ""
    
    # 生成新目录
    new_toc = generate_toc(headings)
    
    if not new_toc:
        return False, "无法生成目录", ""
    
    # 检查现有目录
    toc_positions = find_toc_positions(content)
    lines = content.split('\n')
    
    if len(toc_positions) == 0:
        # 没有目录，添加一个
        insert_pos = 0
        for i, line in enumerate(lines):
            if re.match(r'^#\s+', line):
                insert_pos = i + 1
                break
        
        new_lines = lines[:insert_pos] + [""] + new_toc.split('\n') + [""] + ["---", ""] + lines[insert_pos:]
        new_content = '\n'.join(new_lines)
        action = "添加目录"
        
    elif len(toc_positions) == 1:
        # 有一个目录，替换它
        start, end = toc_positions[0]
        new_lines = lines[:start] + new_toc.split('\n') + lines[end:]
        new_content = '\n'.join(new_lines)
        action = "更新目录"
        
    else:
        # 有多个目录，只保留第一个，替换它
        start, end = toc_positions[0]
        # 移除其他目录
        to_remove = []
        for pos_start, pos_end in toc_positions[1:]:
            to_remove.append((pos_start, pos_end))
        
        # 从后往前删除，避免索引变化
        new_lines = lines[:]
        for pos_start, pos_end in reversed(to_remove):
            new_lines = new_lines[:pos_start] + new_lines[pos_end:]
        
        # 更新第一个目录
        # 重新计算位置（因为可能已经删除了其他目录）
        new_content_temp = '\n'.join(new_lines)
        new_lines_temp = new_content_temp.split('\n')
        for i, line in enumerate(new_lines_temp):
            if re.match(r'^##\s+[📑]?\s*目录', line):
                start = i
                end = len(new_lines_temp)
                for j in range(i + 1, len(new_lines_temp)):
                    if re.match(r'^---', new_lines_temp[j]):
                        end = j
                        break
                    if re.match(r'^##\s+', new_lines_temp[j]) and not re.match(r'^##\s+[📑]?\s*目录', new_lines_temp[j]):
                        end = j
                        break
                    if re.match(r'^#\s+', new_lines_temp[j]):
                        end = j
                        break
                break
        
        new_lines = new_lines_temp[:start] + new_toc.split('\n') + new_lines_temp[end:]
        new_content = '\n'.join(new_lines)
        action = f"移除{len(toc_positions)-1}个多余目录，更新剩余目录"
    
    # 写回文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True, action, ""
    except Exception as e:
        return False, f"写入文件失败: {e}", ""

def main():
    """主函数"""
    base_dir = Path(__file__).parent
    
    # 查找所有Markdown文件
    md_files = list(base_dir.rglob("*.md"))
    md_files = [f for f in md_files if f.name != "README.md"]
    md_files = [f for f in md_files if not f.name.startswith("fix_") and not f.name.startswith("check_")]
    
    print(f"找到 {len(md_files)} 个Markdown文件")
    print("=" * 60)
    
    fixed_count = 0
    error_count = 0
    skipped_count = 0
    multiple_toc_fixed = 0
    
    for md_file in sorted(md_files):
        rel_path = md_file.relative_to(base_dir)
        print(f"\n处理: {rel_path}")
        
        success, message, _ = fix_document(md_file)
        
        if success:
            print(f"  ✅ {message}")
            fixed_count += 1
            if "移除" in message and "多余目录" in message:
                multiple_toc_fixed += 1
        elif "占位文件" in message or "没有找到标题" in message or "无法生成目录" in message:
            print(f"  ⏭️  {message}")
            skipped_count += 1
        else:
            print(f"  ❌ {message}")
            error_count += 1
    
    print("\n" + "=" * 60)
    print(f"处理完成:")
    print(f"  ✅ 成功: {fixed_count}")
    print(f"    - 修复多个目录: {multiple_toc_fixed}")
    print(f"  ⏭️  跳过: {skipped_count}")
    print(f"  ❌ 错误: {error_count}")
    print(f"  📊 总计: {len(md_files)}")

if __name__ == "__main__":
    main()
