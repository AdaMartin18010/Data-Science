#!/usr/bin/env python3
"""
P1文档批量更新脚本
功能：为文档添加目录、PostgreSQL 17版本标注和新特性说明
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

def extract_headings(content: str) -> List[Tuple[int, str, str]]:
    """提取所有标题（级别、文本、锚点）"""
    headings = []
    lines = content.split('\n')

    for line in lines:
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()

            # 跳过元数据部分和目录本身
            if text.lower() in ['目录', 'table of contents', 'toc']:
                continue

            # 生成锚点
            anchor = text.lower()
            anchor = re.sub(r'[^\w\s-]', '', anchor)
            anchor = re.sub(r'[-\s]+', '-', anchor)

            headings.append((level, text, anchor))

    return headings

def generate_toc(headings: List[Tuple[int, str, str]]) -> str:
    """生成目录"""
    if not headings:
        return ""

    toc_lines = ["## 目录\n"]

    for level, text, anchor in headings:
        if level == 1:  # H1是标题，跳过
            continue

        indent = "  " * (level - 2)
        toc_lines.append(f"{indent}- [{text}](#{anchor})")

    toc_lines.append("")  # 空行
    return "\n".join(toc_lines)

def add_toc_to_document(file_path: Path) -> bool:
    """为文档添加目录"""
    try:
        content = file_path.read_text(encoding='utf-8')

        # 检查是否已有目录
        if re.search(r'^##\s+目录', content, re.MULTILINE):
            print(f"  ⚠️  文档已有目录，跳过: {file_path.name}")
            return False

        # 提取标题
        headings = extract_headings(content)

        if not headings:
            print(f"  ⚠️  未找到标题: {file_path.name}")
            return False

        # 生成目录
        toc = generate_toc(headings)

        # 插入目录
        # 查找合适的插入位置（在第一个##标题之前，或在---分隔符之后）
        lines = content.split('\n')
        insert_pos = 0

        for i, line in enumerate(lines):
            if line.strip() == '---' and i > 5:  # 跳过前置元数据的---
                insert_pos = i + 1
                break
            elif re.match(r'^##\s+', line) and i > 5:
                insert_pos = i
                break

        if insert_pos > 0:
            lines.insert(insert_pos, toc)
            new_content = '\n'.join(lines)
            file_path.write_text(new_content, encoding='utf-8')
            print(f"  ✅ 已添加目录: {file_path.name}")
            return True
        else:
            print(f"  ⚠️  未找到插入位置: {file_path.name}")
            return False

    except Exception as e:
        print(f"  ❌ 处理失败 {file_path.name}: {e}")
        return False

def add_pg17_note(file_path: Path, note_content: str) -> bool:
    """添加PostgreSQL 17新特性说明"""
    try:
        content = file_path.read_text(encoding='utf-8')

        # 检查是否已有PostgreSQL 17说明
        if 'PostgreSQL 17' in content[:500]:
            print(f"  ⚠️  文档已有PG17说明: {file_path.name}")
            return False

        # 在版本标注后添加PG17说明
        # 查找"---"分隔符前的位置
        lines = content.split('\n')
        insert_pos = -1

        for i, line in enumerate(lines):
            if line.strip() == '---' and i > 3:
                insert_pos = i
                break

        if insert_pos > 0:
            # 在---之前插入PG17说明
            lines.insert(insert_pos, "")
            lines.insert(insert_pos, note_content)
            new_content = '\n'.join(lines)
            file_path.write_text(new_content, encoding='utf-8')
            print(f"  ✅ 已添加PG17说明: {file_path.name}")
            return True
        else:
            print(f"  ⚠️  未找到插入位置: {file_path.name}")
            return False

    except Exception as e:
        print(f"  ❌ 处理失败 {file_path.name}: {e}")
        return False

def update_version_tag(file_path: Path) -> bool:
    """更新版本标注"""
    try:
        content = file_path.read_text(encoding='utf-8')

        # 检查是否已有版本标注
        if not re.search(r'> 📖 \*\*适用版本\*\*:', content):
            # 在标题后添加版本标注
            lines = content.split('\n')
            title_pos = -1

            for i, line in enumerate(lines):
                if re.match(r'^#\s+', line):
                    title_pos = i
                    break

            if title_pos >= 0:
                version_tag = """
> 📖 **适用版本**: PostgreSQL 17.x（推荐） | 16.x（兼容） | 15.x（兼容）
> 📅 **最后更新**: 2025-10-30
> 🎯 **文档目标**: [根据文档内容自动生成]
"""
                lines.insert(title_pos + 1, version_tag)
                new_content = '\n'.join(lines)
                file_path.write_text(new_content, encoding='utf-8')
                print(f"  ✅ 已添加版本标注: {file_path.name}")
                return True
        else:
            print(f"  ⚠️  文档已有版本标注: {file_path.name}")
            return False

    except Exception as e:
        print(f"  ❌ 处理失败 {file_path.name}: {e}")
        return False

def main():
    # 定义要处理的目录和文件
    base_dir = Path(".")

    directories = {
        "01-核心基础": {
            "files": [
                "01.01-系统架构与设计原理.md",
                "01.02-关系数据模型与理论.md",
                "01.03-SQL语言规范与标准.md",
                "01.04-事务管理与ACID特性.md",
                "01.05-并发控制与MVCC机制.md",
                "01.06-存储管理与数据持久化.md",
            ],
            "pg17_note": "> 🆕 **PostgreSQL 17改进**: 本章节涵盖的核心概念在PostgreSQL 17中得到进一步优化和增强"
        },
        "02-查询处理": {
            "files": [
                "02.01-查询优化器原理.md",
                "02.02-索引结构与优化.md",
                "02.03-统计信息与代价模型.md",
                "02.04-执行计划与性能调优.md",
                "02.05-并行查询处理.md",
            ],
            "pg17_note": "> 🆕 **PostgreSQL 17查询优化**: 改进的查询计划器、并行查询增强、索引优化（B-tree去重、BRIN提升15-20%）"
        }
    }

    print("\n" + "=" * 60)
    print("P1文档批量更新脚本")
    print("=" * 60 + "\n")

    total_files = 0
    updated_files = 0

    for dir_name, config in directories.items():
        dir_path = base_dir / dir_name

        if not dir_path.exists():
            print(f"⚠️  目录不存在: {dir_name}")
            continue

        print(f"\n📁 处理目录: {dir_name}")
        print(f"   文件数: {len(config['files'])}\n")

        for file_name in config['files']:
            file_path = dir_path / file_name

            if not file_path.exists():
                print(f"  ⚠️  文件不存在: {file_name}")
                continue

            print(f"  📄 处理文件: {file_name}")
            total_files += 1

            # 1. 更新版本标注（如果需要）
            update_version_tag(file_path)

            # 2. 添加PostgreSQL 17说明
            add_pg17_note(file_path, config['pg17_note'])

            # 3. 添加目录
            if add_toc_to_document(file_path):
                updated_files += 1

            print()

    print("\n" + "=" * 60)
    print(f"✅ 处理完成")
    print(f"   总文件数: {total_files}")
    print(f"   更新成功: {updated_files}")
    print(f"   跳过/失败: {total_files - updated_files}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
