#!/usr/bin/env python3
"""
PostgreSQL文档格式统一处理工具
自动为文档添加序号和目录
"""
import re
import sys
from pathlib import Path
from datetime import datetime

class DocFormatter:
    def __init__(self):
        self.h2_counter = 0
        self.h3_counters = {}
        self.h4_counters = {}
        self.processed_count = 0
        self.failed_count = 0
    
    def reset_counters(self):
        """重置计数器"""
        self.h2_counter = 0
        self.h3_counters = {}
        self.h4_counters = {}
    
    def should_skip_heading(self, title):
        """判断是否跳过某些特殊标题"""
        skip_keywords = ['目录', 'Table of Contents', 'TOC', 'Contents']
        return any(keyword in title for keyword in skip_keywords)
    
    def add_number_to_heading(self, line):
        """为标题添加序号"""
        # H2标题
        if line.startswith('## '):
            title = line[3:].strip()
            
            # 跳过特殊标题
            if self.should_skip_heading(title):
                return line
            
            # 检查是否已有序号
            if re.match(r'^\d+\.', title):
                # 提取序号和标题
                match = re.match(r'^(\d+)\.\s*(.+)$', title)
                if match:
                    num, rest = match.groups()
                    self.h2_counter = int(num)
                    self.h3_counters[self.h2_counter] = 0
                    return line
            
            # 添加序号
            self.h2_counter += 1
            self.h3_counters[self.h2_counter] = 0
            return f"## {self.h2_counter}. {title}"
        
        # H3标题
        elif line.startswith('### '):
            title = line[4:].strip()
            
            if self.h2_counter == 0:
                return line
            
            # 检查是否已有序号
            if re.match(r'^\d+\.\d+', title):
                match = re.match(r'^(\d+)\.(\d+)\s*(.+)$', title)
                if match:
                    h2_num, h3_num, rest = match.groups()
                    self.h3_counters[self.h2_counter] = int(h3_num)
                    key = f"{self.h2_counter}.{h3_num}"
                    self.h4_counters[key] = 0
                    return line
            
            # 添加序号
            self.h3_counters[self.h2_counter] = self.h3_counters.get(self.h2_counter, 0) + 1
            h3_num = self.h3_counters[self.h2_counter]
            key = f"{self.h2_counter}.{h3_num}"
            self.h4_counters[key] = 0
            return f"### {self.h2_counter}.{h3_num} {title}"
        
        # H4标题
        elif line.startswith('#### '):
            title = line[5:].strip()
            
            if self.h2_counter == 0 or self.h3_counters.get(self.h2_counter, 0) == 0:
                return line
            
            # 检查是否已有序号
            if re.match(r'^\d+\.\d+\.\d+', title):
                return line
            
            # 添加序号
            h3_num = self.h3_counters[self.h2_counter]
            key = f"{self.h2_counter}.{h3_num}"
            self.h4_counters[key] = self.h4_counters.get(key, 0) + 1
            h4_num = self.h4_counters[key]
            return f"#### {self.h2_counter}.{h3_num}.{h4_num} {title}"
        
        return line
    
    def generate_anchor(self, number, title):
        """生成GitHub风格的锚点"""
        anchor = f"{number}-{title}".lower()
        anchor = anchor.replace(' ', '-')
        # 保留中文、数字、字母、连字符
        anchor = re.sub(r'[^\w\-\u4e00-\u9fa5]', '', anchor)
        return anchor
    
    def generate_toc(self, lines):
        """生成目录"""
        toc = ["## 目录\n"]
        has_content = False
        
        for line in lines:
            # 匹配H2标题
            match_h2 = re.match(r'^##\s+(\d+)\.\s+(.+)$', line)
            if match_h2:
                num, title = match_h2.groups()
                if not self.should_skip_heading(title):
                    anchor = self.generate_anchor(num, title)
                    toc.append(f"- [{num}. {title}](#{anchor})")
                    has_content = True
                continue
            
            # 匹配H3标题
            match_h3 = re.match(r'^###\s+(\d+\.\d+)\s+(.+)$', line)
            if match_h3:
                num, title = match_h3.groups()
                anchor = self.generate_anchor(num, title)
                toc.append(f"  - [{num} {title}](#{anchor})")
                has_content = True
                continue
            
            # 匹配H4标题（可选）
            match_h4 = re.match(r'^####\s+(\d+\.\d+\.\d+)\s+(.+)$', line)
            if match_h4:
                num, title = match_h4.groups()
                anchor = self.generate_anchor(num, title)
                # H4标题在目录中缩进更多
                toc.append(f"    - [{num} {title}](#{anchor})")
                has_content = True
                continue
        
        if not has_content:
            return None
        
        return '\n'.join(toc) + '\n'
    
    def find_toc_position(self, lines):
        """找到目录的位置"""
        toc_start = -1
        toc_end = -1
        
        for i, line in enumerate(lines):
            if '## 目录' in line or '## Table of Contents' in line:
                toc_start = i
            elif toc_start >= 0 and (line.startswith('## ') and not any(kw in line for kw in ['目录', 'Table of Contents'])):
                toc_end = i
                break
        
        return toc_start, toc_end
    
    def format_document(self, filepath):
        """格式化单个文档"""
        try:
            print(f"\n{'='*60}")
            print(f"处理: {filepath}")
            print(f"{'='*60}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            original_line_count = len(lines)
            
            # 重置计数器
            self.reset_counters()
            
            # 为标题添加序号
            formatted_lines = []
            for line in lines:
                formatted_lines.append(self.add_number_to_heading(line))
            
            # 生成目录
            toc = self.generate_toc(formatted_lines)
            
            if not toc:
                print("  ⚠️  文档没有标题，跳过目录生成")
                return False
            
            # 查找H1标题位置
            h1_index = -1
            for i, line in enumerate(formatted_lines):
                if line.startswith('# '):
                    h1_index = i
                    break
            
            if h1_index < 0:
                print("  ⚠️  文档没有H1标题")
                return False
            
            # 检查是否已有目录
            toc_start, toc_end = self.find_toc_position(formatted_lines)
            
            if toc_start >= 0:
                # 更新现有目录
                if toc_end < 0:
                    # 没有找到目录结束位置，查找下一个H2
                    for i in range(toc_start + 1, len(formatted_lines)):
                        if formatted_lines[i].startswith('## '):
                            toc_end = i
                            break
                
                if toc_end > toc_start:
                    formatted_lines[toc_start:toc_end] = [toc]
                    print("  ✅ 已更新现有目录")
                else:
                    formatted_lines[toc_start] = toc
                    print("  ✅ 已更新现有目录")
            else:
                # 插入新目录
                formatted_lines.insert(h1_index + 1, '\n' + toc)
                print("  ✅ 已添加新目录")
            
            # 检查是否需要添加元信息
            has_metadata = False
            for line in formatted_lines[-10:]:
                if '**最后更新' in line or '**Last Updated' in line:
                    has_metadata = True
                    break
            
            if not has_metadata:
                # 添加元信息
                today = datetime.now().strftime('%Y-%m-%d')
                formatted_lines.append('\n---\n')
                formatted_lines.append(f'**最后更新**: {today}')
                formatted_lines.append('**格式版本**: 1.0')
                print("  ✅ 已添加元信息")
            
            # 写回文件
            new_content = '\n'.join(formatted_lines)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # 统计信息
            new_line_count = len(formatted_lines)
            h2_count = self.h2_counter
            h3_count = sum(self.h3_counters.values())
            h4_count = sum(self.h4_counters.values())
            
            print(f"  📊 统计: H2={h2_count}, H3={h3_count}, H4={h4_count}")
            print(f"  📄 行数: {original_line_count} → {new_line_count}")
            print(f"  ✅ 处理完成")
            
            self.processed_count += 1
            return True
            
        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()
            self.failed_count += 1
            return False
    
    def process_files(self, filepaths):
        """批量处理文件"""
        print("\n" + "="*60)
        print("PostgreSQL文档格式统一处理工具")
        print("="*60)
        
        for filepath in filepaths:
            path = Path(filepath)
            
            if path.is_file() and path.suffix == '.md':
                self.format_document(filepath)
            elif path.is_dir():
                md_files = sorted(path.glob('*.md'))
                if not md_files:
                    print(f"\n⚠️  目录 {path} 中没有Markdown文件")
                    continue
                
                print(f"\n📁 处理目录: {path}")
                print(f"   找到 {len(md_files)} 个文件")
                
                for md_file in md_files:
                    self.format_document(md_file)
            else:
                print(f"\n⚠️  跳过非Markdown文件: {filepath}")
        
        # 打印总结
        print("\n" + "="*60)
        print("处理完成")
        print("="*60)
        print(f"✅ 成功: {self.processed_count} 个文件")
        print(f"❌ 失败: {self.failed_count} 个文件")
        print(f"📊 总计: {self.processed_count + self.failed_count} 个文件")
        print("="*60 + "\n")

def main():
    if len(sys.argv) < 2:
        print("""
PostgreSQL文档格式统一处理工具

用法:
    python format_docs.py <文件或目录>...

示例:
    # 处理单个文件
    python format_docs.py 06-实战案例/06.01-语义搜索系统端到端实现.md
    
    # 处理整个目录
    python format_docs.py 06-实战案例/
    
    # 批量处理多个文件/目录
    python format_docs.py 01-核心基础/ 02-查询处理/ 03-高级特性/
        """)
        sys.exit(1)
    
    formatter = DocFormatter()
    formatter.process_files(sys.argv[1:])

if __name__ == '__main__':
    main()

