#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档链接检查工具
递归检查所有Markdown文件中的本地链接，找出缺失的文件
"""

import os
import re
import glob
from pathlib import Path
from typing import List, Dict, Set, Tuple

class LinkChecker:
    def __init__(self, root_dir: str = "Analysis"):
        self.root_dir = Path(root_dir)
        self.all_files = set()
        self.referenced_files = set()
        self.missing_files = set()
        self.broken_links = []
        
    def scan_all_files(self):
        """扫描所有Markdown文件"""
        pattern = str(self.root_dir / "**/*.md")
        for file_path in glob.glob(pattern, recursive=True):
            self.all_files.add(Path(file_path).relative_to(self.root_dir))
        print(f"找到 {len(self.all_files)} 个Markdown文件")
    
    def extract_links_from_file(self, file_path: Path) -> List[str]:
        """从单个文件中提取所有本地链接"""
        links = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 匹配Markdown链接格式 [text](url)
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            matches = re.findall(link_pattern, content)
            
            for text, url in matches:
                # 只处理本地.md文件链接
                if url.endswith('.md') and not url.startswith('http'):
                    links.append(url)
                    
        except Exception as e:
            print(f"读取文件 {file_path} 时出错: {e}")
            
        return links
    
    def resolve_relative_path(self, base_file: Path, link_path: str) -> Path:
        """解析相对路径"""
        if link_path.startswith('/'):
            # 绝对路径（相对于根目录）
            return self.root_dir / link_path[1:]
        else:
            # 相对路径
            return (base_file.parent / link_path).resolve()
    
    def check_links(self):
        """检查所有文件中的链接"""
        for file_path in self.all_files:
            full_path = self.root_dir / file_path
            links = self.extract_links_from_file(full_path)
            
            for link in links:
                self.referenced_files.add(link)
                resolved_path = self.resolve_relative_path(full_path, link)
                
                # 检查文件是否存在
                if not resolved_path.exists():
                    self.missing_files.add(link)
                    self.broken_links.append({
                        'source_file': str(file_path),
                        'link': link,
                        'resolved_path': str(resolved_path)
                    })
    
    def generate_report(self) -> str:
        """生成检查报告"""
        report = []
        report.append("# 文档链接检查报告\n")
        report.append(f"检查时间: {Path().cwd()}")
        report.append(f"根目录: {self.root_dir}\n")
        
        report.append(f"## 统计信息")
        report.append(f"- 总文件数: {len(self.all_files)}")
        report.append(f"- 引用文件数: {len(self.referenced_files)}")
        report.append(f"- 缺失文件数: {len(self.missing_files)}\n")
        
        if self.missing_files:
            report.append("## 缺失的文件")
            for missing_file in sorted(self.missing_files):
                report.append(f"- `{missing_file}`")
            report.append("")
            
            report.append("## 损坏的链接详情")
            for broken in self.broken_links:
                report.append(f"### 源文件: `{broken['source_file']}`")
                report.append(f"- 链接: `{broken['link']}`")
                report.append(f"- 解析路径: `{broken['resolved_path']}`")
                report.append("")
        else:
            report.append("## ✅ 所有链接都有效！")
            
        return "\n".join(report)
    
    def run(self):
        """运行完整的检查流程"""
        print("开始扫描文件...")
        self.scan_all_files()
        
        print("检查链接...")
        self.check_links()
        
        print("生成报告...")
        report = self.generate_report()
        
        # 保存报告
        report_file = self.root_dir / "链接检查报告.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"报告已保存到: {report_file}")
        print(f"\n{report}")
        
        return len(self.missing_files) == 0

def main():
    checker = LinkChecker()
    success = checker.run()
    
    if success:
        print("\n🎉 所有链接检查通过！")
    else:
        print(f"\n❌ 发现 {len(checker.missing_files)} 个缺失文件")
        print("请根据报告创建缺失的文件或修复链接。")

if __name__ == "__main__":
    main()
