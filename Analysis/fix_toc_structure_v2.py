#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一所有文档的目录结构（优化版）
参考格式：3.3.1-核心数据处理算法.md
确保：
1. 保留标题中的编号
2. 正确的层级缩进
3. 完整的目录结构
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
        if any(stripped.startswith(marker) for marker in code_block_markers):
            in_code_block = not in_code_block
            continue
        
        if in_code_block:
            continue
        
        # 匹配标题
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append((level, text, line))
    
    return headings

def generate_anchor(text: str) -> str:
    """生成GitHub风格的锚点"""
    # 转换为小写
    anchor = text.lower()
    # 替换空格为连字符
    anchor = re.sub(r'\s+', '-', anchor)
    # 移除特殊字符，保留中文、英文、数字、连字符、括号
    anchor = re.sub(r'[^\w\u4e00-\u9fff\-\(\)]', '', anchor)
    # 移除多余的连字符
    anchor = re.sub(r'-+', '-', anchor)
    # 移除首尾连字符
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
    stack = []  # 用于跟踪缩进层级，存储(level, text)
    
    for i in range(start_idx, len(headings)):
        level, text, _ = headings[i]
        
        # 跳过目录标题本身
        if text == "📑 目录" or text == "目录":
            continue
        
        # 确定缩进：移除栈中级别大于等于当前级别的项
        while stack and stack[-1][0] >= level:
            stack.pop()
        
        # 计算缩进（每个层级2个空格）
        indent = "  " * len(stack)
        
        # 生成锚点（使用完整标题文本）
        anchor = generate_anchor(text)
        
        # 构建目录项（保留标题中的编号）
        toc_item = f"{indent}- [{text}](#{anchor})"
        toc_lines.append(toc_item)
        
        # 将当前标题加入栈
        stack.append((level, text))
    
    return "\n".join(toc_lines)

def find_toc_position(content: str) -> int:
    """找到目录应该插入的位置（H1标题后）"""
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if re.match(r'^#\s+', line):
            # 在H1标题后插入目录
            return i + 1
    
    return 0

def has_toc(content: str) -> bool:
    """检查是否已有目录"""
    return "## 📑 目录" in content

def fix_document(file_path: Path) -> Tuple[bool, str]:
    """修复单个文档的目录结构"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"读取文件失败: {e}"
    
    # 提取标题
    headings = extract_headings(content)
    
    if not headings:
        return False, "没有找到标题"
    
    # 生成新目录
    new_toc = generate_toc(headings)
    
    if not new_toc:
        return False, "无法生成目录"
    
    # 检查是否需要更新
    if has_toc(content):
        # 替换现有目录
        lines = content.split('\n')
        toc_start = -1
        toc_end = -1
        
        for i, line in enumerate(lines):
            if re.match(r'^##\s+[📑]?\s*目录', line):
                toc_start = i
                # 找到目录结束位置（下一个同级或更高级标题，或分隔线）
                for j in range(i + 1, len(lines)):
                    if re.match(r'^---', lines[j]):
                        toc_end = j
                        break
                    if re.match(r'^##\s+', lines[j]) and not re.match(r'^##\s+[📑]?\s*目录', lines[j]):
                        toc_end = j
                        break
                if toc_end == -1:
                    # 如果没找到，查找下一个H1或H2标题
                    for j in range(i + 1, len(lines)):
                        if re.match(r'^#\s+', lines[j]) or (re.match(r'^##\s+', lines[j]) and not re.match(r'^##\s+[📑]?\s*目录', lines[j])):
                            toc_end = j
                            break
                if toc_end == -1:
                    toc_end = len(lines)
                break
        
        if toc_start != -1:
            # 替换目录
            new_lines = lines[:toc_start] + new_toc.split('\n') + lines[toc_end:]
            new_content = '\n'.join(new_lines)
        else:
            return False, "找到目录标记但无法定位"
    else:
        # 插入新目录
        insert_pos = find_toc_position(content)
        lines = content.split('\n')
        # 在H1后插入目录，然后添加分隔线
        new_lines = lines[:insert_pos] + [""] + new_toc.split('\n') + [""] + ["---", ""] + lines[insert_pos:]
        new_content = '\n'.join(new_lines)
    
    # 写回文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True, "成功"
    except Exception as e:
        return False, f"写入文件失败: {e}"

def main():
    """主函数"""
    base_dir = Path(__file__).parent
    analysis_dir = base_dir / "3-数据模型与算法"
    
    if not analysis_dir.exists():
        print(f"目录不存在: {analysis_dir}")
        return
    
    # 查找所有Markdown文件
    md_files = list(analysis_dir.rglob("*.md"))
    md_files = [f for f in md_files if f.name != "README.md"]
    
    print(f"找到 {len(md_files)} 个Markdown文件")
    print("=" * 60)
    
    fixed_count = 0
    error_count = 0
    skipped_count = 0
    
    for md_file in sorted(md_files):
        rel_path = md_file.relative_to(base_dir)
        print(f"\n处理: {rel_path}")
        
        success, message = fix_document(md_file)
        
        if success:
            print(f"  ✅ {message}")
            fixed_count += 1
        elif "没有找到标题" in message or "无法生成目录" in message:
            print(f"  ⏭️  {message}")
            skipped_count += 1
        else:
            print(f"  ❌ {message}")
            error_count += 1
    
    print("\n" + "=" * 60)
    print(f"处理完成:")
    print(f"  ✅ 成功: {fixed_count}")
    print(f"  ⏭️  跳过: {skipped_count}")
    print(f"  ❌ 错误: {error_count}")
    print(f"  📊 总计: {len(md_files)}")

if __name__ == "__main__":
    main()
