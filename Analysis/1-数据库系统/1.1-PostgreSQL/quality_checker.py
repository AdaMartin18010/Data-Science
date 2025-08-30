#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL知识体系质量检查工具
"""

import os
import re
import json
from pathlib import Path

class QualityChecker:
    def __init__(self, base_path="."):
        self.base_path = Path(base_path)
        self.report = {
            'overall_score': 0.0,
            'file_count': 0,
            'quality_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'detailed_reports': []
        }
    
    def check_all_files(self):
        """检查所有Markdown文件"""
        md_files = list(self.base_path.rglob("*.md"))
        total_score = 0.0
        
        for file_path in md_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_score = self._check_file_quality(content)
                total_score += file_score
                
                file_report = {
                    'file_path': str(file_path),
                    'score': file_score,
                    'issues': self._identify_issues(content)
                }
                self.report['detailed_reports'].append(file_report)
                
                # 更新质量分布
                if file_score >= 0.8:
                    self.report['quality_distribution']['high'] += 1
                elif file_score >= 0.6:
                    self.report['quality_distribution']['medium'] += 1
                else:
                    self.report['quality_distribution']['low'] += 1
                    
            except Exception as e:
                print(f"检查文件 {file_path} 时出错: {e}")
        
        self.report['file_count'] = len(md_files)
        if md_files:
            self.report['overall_score'] = total_score / len(md_files)
        
        return self.report
    
    def _check_file_quality(self, content):
        """检查文件质量"""
        score = 0.0
        
        # 检查概念定义 (25%)
        if re.search(r'##\s*1\.\s*概述|##\s*1\.\s*定义', content):
            score += 0.25
        
        # 检查形式化表示 (20%)
        if re.search(r'```latex|\\newcommand|\\begin\{theorem\}', content):
            score += 0.20
        
        # 检查SQL代码 (20%)
        if re.search(r'```sql|CREATE TABLE|SELECT|INSERT', content):
            score += 0.20
        
        # 检查应用实例 (15%)
        if re.search(r'应用实例|应用场景|实际应用', content):
            score += 0.15
        
        # 检查参考文献 (10%)
        if re.search(r'##\s*参考文献|##\s*References', content):
            score += 0.10
        
        # 检查双语支持 (10%)
        if re.search(r'English|English Definition', content):
            score += 0.10
        
        return min(score, 1.0)
    
    def _identify_issues(self, content):
        """识别问题"""
        issues = []
        
        if not re.search(r'##\s*1\.', content):
            issues.append("缺少概述或定义部分")
        
        if not re.search(r'```sql', content):
            issues.append("缺少SQL代码示例")
        
        if not re.search(r'应用实例|应用场景', content):
            issues.append("缺少应用实例")
        
        if not re.search(r'参考文献|References', content):
            issues.append("缺少参考文献")
        
        return issues
    
    def generate_report(self, output_file="quality_report.json"):
        """生成报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        
        print(f"\n质量检查报告:")
        print(f"总体分数: {self.report['overall_score']:.2f}")
        print(f"文件数量: {self.report['file_count']}")
        print(f"高质量: {self.report['quality_distribution']['high']}")
        print(f"中等质量: {self.report['quality_distribution']['medium']}")
        print(f"低质量: {self.report['quality_distribution']['low']}")

if __name__ == "__main__":
    checker = QualityChecker()
    checker.check_all_files()
    checker.generate_report()
