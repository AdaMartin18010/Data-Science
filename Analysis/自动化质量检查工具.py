#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL国际化Wiki标准自动化质量检查工具

本工具用于检查PostgreSQL相关文档是否符合国际化Wiki标准，
包括数学公式验证、术语一致性检查、参考文献验证等功能。
"""

import re
import yaml
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Generator, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IssueType(Enum):
    """问题类型枚举"""
    MATHEMATICAL_FORMULA = "数学公式错误"
    TERMINOLOGY_INCONSISTENCY = "术语不一致"
    REFERENCE_INVALID = "参考文献无效"
    BILINGUAL_MISSING = "双语对照缺失"
    WIKIDATA_ALIGNMENT = "Wikidata对齐错误"
    FORMAT_ERROR = "格式错误"
    CONTENT_INCOMPLETE = "内容不完整"

@dataclass
class QualityIssue:
    """质量问题数据类"""
    issue_type: IssueType
    file_path: str
    line_number: int
    description: str
    severity: str  # "high", "medium", "low"
    suggestion: str

class PostgreSQLQualityChecker:
    """PostgreSQL质量检查器"""
    
    def __init__(self, base_path: str = "Analysis"):
        self.base_path = Path(base_path)
        self.standards = self.load_standards()
        self.terminology_db = self.load_terminology_database()
        self.wikidata_mappings = self.load_wikidata_mappings()
        
    def load_standards(self) -> Dict[str, Any]:
        """加载质量标准"""
        standards_file = self.base_path / "国际化Wiki标准与知识规范对齐指南.md"
        if standards_file.exists():
            # 这里应该解析标准文档，简化处理
            return {
                "mathematical_formula": {
                    "required_patterns": [r'\$.*?\$', r'\\\[.*?\\\]', r'\\\(.*?\\\)'],
                    "forbidden_patterns": [r'\$\$.*?\$\$']  # 避免使用$$ $$
                },
                "terminology": {
                    "required_terms": ["PostgreSQL", "ACID", "MVCC", "SQL"],
                    "forbidden_terms": ["postgres", "acid", "mvcc"]
                }
            }
        return {}
    
    def load_terminology_database(self) -> Dict[str, Dict[str, str]]:
        """加载术语数据库"""
        return {
            "PostgreSQL": {
                "zh": "PostgreSQL",
                "en": "PostgreSQL",
                "definition_zh": "对象关系型数据库管理系统",
                "definition_en": "Object-relational database management system"
            },
            "ACID": {
                "zh": "ACID属性",
                "en": "ACID Properties",
                "definition_zh": "原子性、一致性、隔离性、持久性",
                "definition_en": "Atomicity, Consistency, Isolation, Durability"
            },
            "MVCC": {
                "zh": "多版本并发控制",
                "en": "Multi-Version Concurrency Control",
                "definition_zh": "通过维护数据多个版本实现并发控制",
                "definition_en": "Concurrency control through multiple data versions"
            }
        }
    
    def load_wikidata_mappings(self) -> Dict[str, str]:
        """加载Wikidata映射"""
        return {
            "PostgreSQL": "Q192490",
            "ACID": "Q193078",
            "SQL": "Q193321",
            "Query Optimizer": "Q727659"
        }
    
    def check_mathematical_formulas(self, content: str, file_path: str) -> Generator[QualityIssue, None, None]:
        """检查数学公式的正确性"""
        # 检查LaTeX语法
        latex_patterns = [
            (r'\$([^$]+)\$', "行内公式"),
            (r'\\\[([^\]]+)\\\]', "块级公式"),
            (r'\\\(([^)]+)\\\)', "行内公式")
        ]
        
        for pattern, formula_type in latex_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                formula = match.group(1)
                line_number = content[:match.start()].count('\n') + 1
                
                # 检查基本语法错误
                if self.has_latex_syntax_error(formula):
                    yield QualityIssue(
                        issue_type=IssueType.MATHEMATICAL_FORMULA,
                        file_path=file_path,
                        line_number=line_number,
                        description=f"{formula_type}语法错误: {formula}",
                        severity="high",
                        suggestion="请检查LaTeX语法，确保括号匹配和命令正确"
                    )
                
                # 检查数学符号使用
                if self.has_invalid_math_symbols(formula):
                    yield QualityIssue(
                        issue_type=IssueType.MATHEMATICAL_FORMULA,
                        file_path=file_path,
                        line_number=line_number,
                        description=f"{formula_type}包含无效数学符号: {formula}",
                        severity="medium",
                        suggestion="请使用标准LaTeX数学符号"
                    )
    
    def has_latex_syntax_error(self, formula: str) -> bool:
        """检查LaTeX语法错误"""
        # 检查括号匹配
        brackets = {'{': '}', '[': ']', '(': ')'}
        stack = []
        
        for char in formula:
            if char in brackets:
                stack.append(char)
            elif char in brackets.values():
                if not stack or brackets[stack.pop()] != char:
                    return True
        
        return len(stack) > 0
    
    def has_invalid_math_symbols(self, formula: str) -> bool:
        """检查无效的数学符号"""
        # 这里可以定义无效符号列表
        invalid_symbols = ['\\', '&', '%', '#', '^', '_']
        return any(symbol in formula for symbol in invalid_symbols)
    
    def check_terminology_consistency(self, content: str, file_path: str) -> Generator[QualityIssue, None, None]:
        """检查术语使用的一致性"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # 检查术语使用
            for term, term_info in self.terminology_db.items():
                # 检查是否使用了正确的术语
                if term.lower() in line.lower() and term not in line:
                    yield QualityIssue(
                        issue_type=IssueType.TERMINOLOGY_INCONSISTENCY,
                        file_path=file_path,
                        line_number=line_num,
                        description=f"术语使用不一致: 应该使用 '{term}' 而不是 '{term.lower()}'",
                        severity="medium",
                        suggestion=f"请使用标准术语 '{term}'"
                    )
                
                # 检查双语对照
                if term in line:
                    # 检查是否有对应的中文定义
                    if term_info.get('zh') and term_info['zh'] not in content:
                        yield QualityIssue(
                            issue_type=IssueType.BILINGUAL_MISSING,
                            file_path=file_path,
                            line_number=line_num,
                            description=f"缺少中文术语对照: {term}",
                            severity="low",
                            suggestion=f"请添加中文术语: {term_info['zh']}"
                        )
    
    def check_references(self, content: str, file_path: str) -> Generator[QualityIssue, None, None]:
        """检查参考文献的完整性"""
        # 检查引用格式
        citation_patterns = [
            r'\[([^\]]+)\]',  # [引用]
            r'\\cite\{([^}]+)\}',  # \cite{引用}
            r'\\ref\{([^}]+)\}'  # \ref{引用}
        ]
        
        for pattern in citation_patterns:
            for match in re.finditer(pattern, content):
                citation = match.group(1)
                line_number = content[:match.start()].count('\n') + 1
                
                # 检查引用是否在参考文献列表中
                if not self.is_valid_reference(citation, content):
                    yield QualityIssue(
                        issue_type=IssueType.REFERENCE_INVALID,
                        file_path=file_path,
                        line_number=line_number,
                        description=f"无效的参考文献: {citation}",
                        severity="medium",
                        suggestion="请检查参考文献格式和完整性"
                    )
    
    def is_valid_reference(self, citation: str, content: str) -> bool:
        """检查参考文献是否有效"""
        # 简化检查：看是否在参考文献部分
        ref_section = re.search(r'##?\s*参考文献?|##?\s*References?', content, re.IGNORECASE)
        if ref_section:
            ref_content = content[ref_section.start():]
            return citation in ref_content
        return False
    
    def check_wikidata_alignment(self, content: str, file_path: str) -> Generator[QualityIssue, None, None]:
        """检查Wikidata对齐"""
        for term, wikidata_id in self.wikidata_mappings.items():
            if term in content:
                # 检查是否有Wikidata ID
                if f"Q{wikidata_id}" not in content and wikidata_id not in content:
                    line_number = content.find(term) // 80 + 1  # 估算行号
                    yield QualityIssue(
                        issue_type=IssueType.WIKIDATA_ALIGNMENT,
                        file_path=file_path,
                        line_number=line_number,
                        description=f"缺少Wikidata对齐: {term}",
                        severity="low",
                        suggestion=f"请添加Wikidata ID: {wikidata_id}"
                    )
    
    def check_format_consistency(self, content: str, file_path: str) -> Generator[QualityIssue, None, None]:
        """检查格式一致性"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # 检查标题格式
            if line.startswith('#'):
                if not re.match(r'^#{1,6}\s+', line):
                    yield QualityIssue(
                        issue_type=IssueType.FORMAT_ERROR,
                        file_path=file_path,
                        line_number=line_num,
                        description="标题格式错误",
                        severity="medium",
                        suggestion="标题后应该有空格"
                    )
            
            # 检查代码块格式
            if line.startswith('```'):
                if not re.match(r'^```[a-zA-Z]*$', line):
                    yield QualityIssue(
                        issue_type=IssueType.FORMAT_ERROR,
                        file_path=file_path,
                        line_number=line_num,
                        description="代码块格式错误",
                        severity="low",
                        suggestion="代码块应该指定语言或为空"
                    )
    
    def check_content_completeness(self, content: str, file_path: str) -> Generator[QualityIssue, None, None]:
        """检查内容完整性"""
        required_sections = [
            "概述", "Overview",
            "概念定义", "Concept Definition",
            "总结", "Summary"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            yield QualityIssue(
                issue_type=IssueType.CONTENT_INCOMPLETE,
                file_path=file_path,
                line_number=1,
                description=f"缺少必要章节: {', '.join(missing_sections)}",
                severity="high",
                suggestion="请添加缺失的章节"
            )
    
    def check_file(self, file_path: str) -> List[QualityIssue]:
        """检查单个文件"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 执行各种检查
            for issue in self.check_mathematical_formulas(content, file_path):
                issues.append(issue)
            
            for issue in self.check_terminology_consistency(content, file_path):
                issues.append(issue)
            
            for issue in self.check_references(content, file_path):
                issues.append(issue)
            
            for issue in self.check_wikidata_alignment(content, file_path):
                issues.append(issue)
            
            for issue in self.check_format_consistency(content, file_path):
                issues.append(issue)
            
            for issue in self.check_content_completeness(content, file_path):
                issues.append(issue)
                
        except Exception as e:
            logger.error(f"检查文件 {file_path} 时出错: {e}")
            issues.append(QualityIssue(
                issue_type=IssueType.FORMAT_ERROR,
                file_path=file_path,
                line_number=1,
                description=f"文件读取错误: {e}",
                severity="high",
                suggestion="请检查文件编码和格式"
            ))
        
        return issues
    
    def check_directory(self, directory: str = None) -> Dict[str, List[QualityIssue]]:
        """检查整个目录"""
        if directory is None:
            directory = self.base_path
        
        results = {}
        
        for file_path in Path(directory).rglob("*.md"):
            if "国际化" in file_path.name or "PostgreSQL" in file_path.name:
                logger.info(f"检查文件: {file_path}")
                issues = self.check_file(str(file_path))
                if issues:
                    results[str(file_path)] = issues
        
        return results
    
    def generate_report(self, results: Dict[str, List[QualityIssue]], output_file: str = None) -> str:
        """生成质量报告"""
        report = []
        report.append("# PostgreSQL国际化Wiki标准质量检查报告")
        report.append("")
        report.append(f"生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        total_files = len(results)
        total_issues = sum(len(issues) for issues in results.values())
        
        report.append(f"## 总体统计")
        report.append(f"- 检查文件数: {total_files}")
        report.append(f"- 发现问题数: {total_issues}")
        report.append("")
        
        # 按问题类型统计
        issue_counts = {}
        for issues in results.values():
            for issue in issues:
                issue_counts[issue.issue_type.value] = issue_counts.get(issue.issue_type.value, 0) + 1
        
        report.append("## 问题类型分布")
        for issue_type, count in sorted(issue_counts.items()):
            report.append(f"- {issue_type}: {count}")
        report.append("")
        
        # 详细问题列表
        report.append("## 详细问题列表")
        for file_path, issues in results.items():
            report.append(f"### {file_path}")
            report.append("")
            
            for issue in issues:
                report.append(f"**{issue.issue_type.value}** (第{issue.line_number}行, {issue.severity}级别)")
                report.append(f"- 描述: {issue.description}")
                report.append(f"- 建议: {issue.suggestion}")
                report.append("")
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger.info(f"质量报告已保存到: {output_file}")
        
        return report_text

def main():
    """主函数"""
    checker = PostgreSQLQualityChecker()
    
    # 检查整个目录
    results = checker.check_directory()
    
    # 生成报告
    report = checker.generate_report(results, "quality_report.md")
    
    # 打印摘要
    total_issues = sum(len(issues) for issues in results.values())
    print(f"检查完成！发现 {total_issues} 个问题")
    print("详细报告已保存到 quality_report.md")

if __name__ == "__main__":
    main()
