#!/usr/bin/env python3
"""
数据科学知识库增强版自动化质量检查工具

该工具提供全面的质量检查功能，包括：
- 内容质量检查（完整性、准确性、深度）
- 格式规范检查（一致性、规范性）
- 链接有效性检查（内部、外部链接）
- 代码质量检查（语法、可运行性）
- 数学公式检查（LaTeX格式）
- 交叉引用检查（完整性、一致性）
- 自动化报告生成
"""

import os
import re
import ast
import json
import yaml
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import markdown
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib
import requests
from urllib.parse import urlparse
import sqlite3


@dataclass
class QualityIssue:
    """质量问题的数据结构"""
    file_path: str
    line_number: int
    issue_type: str
    description: str
    severity: str  # 'error', 'warning', 'info'
    suggestion: str = ""
    context: str = ""


@dataclass
class QualityScore:
    """质量评分数据结构"""
    file_path: str
    title_hierarchy: float
    content_depth: float
    code_quality: float
    math_formulas: float
    links: float
    format: float
    cross_references: float
    overall: float
    issues: List[QualityIssue]
    word_count: int
    code_block_count: int
    math_formula_count: int
    link_count: int


@dataclass
class DocumentMetrics:
    """文档指标数据结构"""
    file_path: str
    file_size: int
    line_count: int
    word_count: int
    title_count: int
    code_block_count: int
    math_formula_count: int
    link_count: int
    image_count: int
    table_count: int
    last_modified: datetime


class ContentQualityChecker:
    """内容质量检查器"""
    
    def __init__(self):
        self.min_content_length = 500  # 最小内容长度（行数）
        self.min_word_count = 2000     # 最小字数
        self.required_sections = [
            '概述', '理论基础', '实现方法', '应用案例', '性能分析', '最佳实践'
        ]
    
    def check(self, file_path: str, content: str) -> Tuple[float, List[QualityIssue]]:
        """检查内容质量"""
        issues = []
        score = 100.0
        
        # 检查内容长度
        line_count = len(content.split('\n'))
        if line_count < self.min_content_length:
            issues.append(QualityIssue(
                file_path=file_path,
                line_number=1,
                issue_type="content_length",
                description=f"文档内容过短，当前{line_count}行，建议至少{self.min_content_length}行",
                severity="warning"
            ))
            score -= 20
        
        # 检查字数
        word_count = len(content.split())
        if word_count < self.min_word_count:
            issues.append(QualityIssue(
                file_path=file_path,
                line_number=1,
                issue_type="word_count",
                description=f"文档字数过少，当前{word_count}字，建议至少{self.min_word_count}字",
                severity="warning"
            ))
            score -= 15
        
        # 检查必需章节
        missing_sections = []
        for section in self.required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            issues.append(QualityIssue(
                file_path=file_path,
                line_number=1,
                issue_type="missing_sections",
                description=f"缺少必需章节: {', '.join(missing_sections)}",
                severity="warning",
                suggestion="建议添加缺失的章节以提升文档完整性"
            ))
            score -= len(missing_sections) * 5
        
        # 检查内容深度
        depth_score = self._check_content_depth(content)
        score += depth_score
        
        return max(0, score), issues
    
    def _check_content_depth(self, content: str) -> float:
        """检查内容深度"""
        score = 0
        
        # 检查是否有数学公式
        if re.search(r'\$[^$]+\$', content):
            score += 10
        
        # 检查是否有代码块
        if re.search(r'```\w+', content):
            score += 10
        
        # 检查是否有图表
        if re.search(r'!\[.*\]\(.*\)', content):
            score += 5
        
        # 检查是否有表格
        if re.search(r'\|.*\|', content):
            score += 5
        
        return score


class FormatChecker:
    """格式规范检查器"""
    
    def __init__(self):
        self.title_pattern = r'^(#{1,6})\s+(.+)$'
        self.code_pattern = r'```(\w+)?\n(.*?)```'
        self.math_pattern = r'\$([^$]+)\$'
        self.block_math_pattern = r'\$\$([^$]+)\$\$'
        self.link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        self.image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    def check(self, file_path: str, content: str) -> Tuple[float, List[QualityIssue]]:
        """检查格式规范"""
        issues = []
        score = 100.0
        
        # 检查标题层次
        title_score, title_issues = self._check_title_hierarchy(content)
        score += title_score - 100
        issues.extend(title_issues)
        
        # 检查代码块格式
        code_score, code_issues = self._check_code_blocks(content)
        score += code_score - 100
        issues.extend(code_issues)
        
        # 检查数学公式格式
        math_score, math_issues = self._check_math_formulas(content)
        score += math_score - 100
        issues.extend(math_issues)
        
        # 检查链接格式
        link_score, link_issues = self._check_links(content)
        score += link_score - 100
        issues.extend(link_issues)
        
        return max(0, score), issues
    
    def _check_title_hierarchy(self, content: str) -> Tuple[float, List[QualityIssue]]:
        """检查标题层次"""
        issues = []
        score = 100.0
        titles = []
        
        for line_num, line in enumerate(content.split('\n'), 1):
            match = re.match(self.title_pattern, line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                titles.append((level, title, line_num))
        
        # 检查标题层次是否合理
        for i, (level, title, line_num) in enumerate(titles):
            if i > 0 and level > titles[i-1][0] + 1:
                issues.append(QualityIssue(
                    file_path="",
                    line_number=line_num,
                    issue_type="title_hierarchy",
                    description=f"标题层次跳跃过大: {title}",
                    severity="warning",
                    suggestion="建议调整标题层次，避免跳跃"
                ))
                score -= 5
        
        return score, issues
    
    def _check_code_blocks(self, content: str) -> Tuple[float, List[QualityIssue]]:
        """检查代码块格式"""
        issues = []
        score = 100.0
        
        for match in re.finditer(self.code_pattern, content, re.DOTALL):
            language = match.group(1)
            code = match.group(2)
            
            if not language:
                issues.append(QualityIssue(
                    file_path="",
                    line_number=content[:match.start()].count('\n') + 1,
                    issue_type="code_language",
                    description="代码块缺少语言标识",
                    severity="info",
                    suggestion="建议为代码块添加语言标识"
                ))
                score -= 2
            
            if not code.strip():
                issues.append(QualityIssue(
                    file_path="",
                    line_number=content[:match.start()].count('\n') + 1,
                    issue_type="empty_code_block",
                    description="代码块为空",
                    severity="warning",
                    suggestion="建议添加代码内容或删除空代码块"
                ))
                score -= 5
        
        return score, issues
    
    def _check_math_formulas(self, content: str) -> Tuple[float, List[QualityIssue]]:
        """检查数学公式格式"""
        issues = []
        score = 100.0
        
        # 检查行内公式
        inline_formulas = re.findall(self.math_pattern, content)
        for formula in inline_formulas:
            if not self._is_valid_latex(formula):
                issues.append(QualityIssue(
                    file_path="",
                    line_number=1,
                    issue_type="invalid_math",
                    description=f"数学公式格式错误: {formula}",
                    severity="error",
                    suggestion="请检查LaTeX语法"
                ))
                score -= 10
        
        # 检查块级公式
        block_formulas = re.findall(self.block_math_pattern, content)
        for formula in block_formulas:
            if not self._is_valid_latex(formula):
                issues.append(QualityIssue(
                    file_path="",
                    line_number=1,
                    issue_type="invalid_math",
                    description=f"块级数学公式格式错误: {formula}",
                    severity="error",
                    suggestion="请检查LaTeX语法"
                ))
                score -= 10
        
        return score, issues
    
    def _check_links(self, content: str) -> Tuple[float, List[QualityIssue]]:
        """检查链接格式"""
        issues = []
        score = 100.0
        
        for match in re.finditer(self.link_pattern, content):
            text = match.group(1)
            url = match.group(2)
            
            if not text.strip():
                issues.append(QualityIssue(
                    file_path="",
                    line_number=content[:match.start()].count('\n') + 1,
                    issue_type="empty_link_text",
                    description="链接文本为空",
                    severity="warning",
                    suggestion="建议为链接添加描述文本"
                ))
                score -= 5
        
        return score, issues
    
    def _is_valid_latex(self, formula: str) -> bool:
        """检查LaTeX公式是否有效"""
        # 简单的LaTeX语法检查
        try:
            # 检查基本语法
            if '\\' in formula:
                # 检查反斜杠后的命令
                commands = re.findall(r'\\(\w+)', formula)
                valid_commands = [
                    'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'theta', 'lambda',
                    'mu', 'pi', 'sigma', 'phi', 'psi', 'omega',
                    'sum', 'prod', 'int', 'lim', 'inf', 'max', 'min',
                    'frac', 'sqrt', 'log', 'exp', 'sin', 'cos', 'tan'
                ]
                for cmd in commands:
                    if cmd not in valid_commands and not cmd.isalpha():
                        return False
            return True
        except:
            return False


class LinkChecker:
    """链接有效性检查器"""
    
    def __init__(self):
        self.internal_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        self.external_link_pattern = r'https?://[^\s\)]+'
        self.checked_links = {}
    
    def check(self, file_path: str, content: str, base_path: str) -> Tuple[float, List[QualityIssue]]:
        """检查链接有效性"""
        issues = []
        score = 100.0
        
        # 检查内部链接
        internal_score, internal_issues = self._check_internal_links(content, file_path, base_path)
        score += internal_score - 100
        issues.extend(internal_issues)
        
        # 检查外部链接
        external_score, external_issues = self._check_external_links(content)
        score += external_score - 100
        issues.extend(external_issues)
        
        return max(0, score), issues
    
    def _check_internal_links(self, content: str, file_path: str, base_path: str) -> Tuple[float, List[QualityIssue]]:
        """检查内部链接"""
        issues = []
        score = 100.0
        
        for match in re.finditer(self.internal_link_pattern, content):
            text = match.group(1)
            url = match.group(2)
            
            # 跳过外部链接
            if url.startswith('http'):
                continue
            
            # 检查内部链接有效性
            if not self._is_valid_internal_link(url, file_path, base_path):
                issues.append(QualityIssue(
                    file_path=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                    issue_type="invalid_internal_link",
                    description=f"内部链接无效: {url}",
                    severity="error",
                    suggestion="请检查链接路径是否正确"
                ))
                score -= 10
        
        return score, issues
    
    def _check_external_links(self, content: str) -> Tuple[float, List[QualityIssue]]:
        """检查外部链接"""
        issues = []
        score = 100.0
        
        external_links = re.findall(self.external_link_pattern, content)
        for link in external_links:
            if not self._is_valid_external_link(link):
                issues.append(QualityIssue(
                    file_path="",
                    line_number=1,
                    issue_type="invalid_external_link",
                    description=f"外部链接无效: {link}",
                    severity="warning",
                    suggestion="请检查链接是否可访问"
                ))
                score -= 5
        
        return score, issues
    
    def _is_valid_internal_link(self, url: str, file_path: str, base_path: str) -> bool:
        """检查内部链接是否有效"""
        try:
            # 解析相对路径
            if url.startswith('./'):
                url = url[2:]
            elif url.startswith('../'):
                # 处理上级目录
                current_dir = Path(file_path).parent
                url = str(current_dir / url[3:])
            else:
                url = str(Path(base_path) / url)
            
            # 检查文件是否存在
            return Path(url).exists()
        except:
            return False
    
    def _is_valid_external_link(self, url: str) -> bool:
        """检查外部链接是否有效"""
        if url in self.checked_links:
            return self.checked_links[url]
        
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            self.checked_links[url] = response.status_code < 400
            return self.checked_links[url]
        except:
            self.checked_links[url] = False
            return False


class CodeQualityChecker:
    """代码质量检查器"""
    
    def __init__(self):
        self.supported_languages = ['python', 'rust', 'javascript', 'sql', 'haskell', 'go']
    
    def check(self, file_path: str, content: str) -> Tuple[float, List[QualityIssue]]:
        """检查代码质量"""
        issues = []
        score = 100.0
        
        # 提取代码块
        code_blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.DOTALL)
        
        for language, code in code_blocks:
            if not language or language not in self.supported_languages:
                continue
            
            code_score, code_issues = self._check_code_block(language, code)
            score += code_score - 100
            issues.extend(code_issues)
        
        return max(0, score), issues
    
    def _check_code_block(self, language: str, code: str) -> Tuple[float, List[QualityIssue]]:
        """检查单个代码块"""
        issues = []
        score = 100.0
        
        if language == 'python':
            return self._check_python_code(code)
        elif language == 'rust':
            return self._check_rust_code(code)
        elif language == 'sql':
            return self._check_sql_code(code)
        else:
            # 通用代码检查
            return self._check_generic_code(code)
    
    def _check_python_code(self, code: str) -> Tuple[float, List[QualityIssue]]:
        """检查Python代码"""
        issues = []
        score = 100.0
        
        try:
            # 语法检查
            ast.parse(code)
        except SyntaxError as e:
            issues.append(QualityIssue(
                file_path="",
                line_number=1,
                issue_type="python_syntax_error",
                description=f"Python语法错误: {str(e)}",
                severity="error",
                suggestion="请检查Python语法"
            ))
            score -= 20
        
        # 检查代码风格
        if len(code.split('\n')) > 10:
            # 检查是否有注释
            if '#' not in code:
                issues.append(QualityIssue(
                    file_path="",
                    line_number=1,
                    issue_type="missing_comments",
                    description="代码缺少注释",
                    severity="info",
                    suggestion="建议为复杂代码添加注释"
                ))
                score -= 5
        
        return score, issues
    
    def _check_rust_code(self, code: str) -> Tuple[float, List[QualityIssue]]:
        """检查Rust代码"""
        issues = []
        score = 100.0
        
        # 基本语法检查
        if 'fn ' in code and not code.strip().endswith('}'):
            issues.append(QualityIssue(
                file_path="",
                line_number=1,
                issue_type="rust_syntax",
                description="Rust代码可能缺少闭合括号",
                severity="warning",
                suggestion="请检查代码结构完整性"
            ))
            score -= 10
        
        return score, issues
    
    def _check_sql_code(self, code: str) -> Tuple[float, List[QualityIssue]]:
        """检查SQL代码"""
        issues = []
        score = 100.0
        
        # 检查SQL关键字
        sql_keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP']
        code_upper = code.upper()
        
        if 'SELECT' in code_upper and 'FROM' not in code_upper:
            issues.append(QualityIssue(
                file_path="",
                line_number=1,
                issue_type="sql_syntax",
                description="SELECT语句缺少FROM子句",
                severity="error",
                suggestion="请添加FROM子句"
            ))
            score -= 15
        
        return score, issues
    
    def _check_generic_code(self, code: str) -> Tuple[float, List[QualityIssue]]:
        """通用代码检查"""
        issues = []
        score = 100.0
        
        # 检查代码长度
        if len(code) > 1000:
            issues.append(QualityIssue(
                file_path="",
                line_number=1,
                issue_type="code_length",
                description="代码块过长，建议拆分",
                severity="info",
                suggestion="建议将长代码拆分为多个函数或模块"
            ))
            score -= 5
        
        return score, issues


class CrossReferenceChecker:
    """交叉引用检查器"""
    
    def __init__(self):
        self.reference_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        self.concept_pattern = r'\*\*([^*]+)\*\*'  # 加粗的概念
    
    def check(self, file_path: str, content: str, all_files: List[str]) -> Tuple[float, List[QualityIssue]]:
        """检查交叉引用"""
        issues = []
        score = 100.0
        
        # 提取文档中的概念
        concepts = re.findall(self.concept_pattern, content)
        
        # 检查概念是否有对应的文档
        for concept in concepts:
            if not self._has_concept_document(concept, all_files):
                issues.append(QualityIssue(
                    file_path=file_path,
                    line_number=1,
                    issue_type="missing_concept_document",
                    description=f"概念'{concept}'缺少对应的文档",
                    severity="info",
                    suggestion=f"建议为概念'{concept}'创建专门的文档"
                ))
                score -= 2
        
        # 检查引用完整性
        references = re.findall(self.reference_pattern, content)
        for text, url in references:
            if not self._is_valid_reference(url, all_files):
                issues.append(QualityIssue(
                    file_path=file_path,
                    line_number=1,
                    issue_type="invalid_reference",
                    description=f"引用无效: {url}",
                    severity="warning",
                    suggestion="请检查引用路径是否正确"
                ))
                score -= 5
        
        return max(0, score), issues
    
    def _has_concept_document(self, concept: str, all_files: List[str]) -> bool:
        """检查概念是否有对应的文档"""
        concept_lower = concept.lower()
        for file_path in all_files:
            if concept_lower in file_path.lower():
                return True
        return False
    
    def _is_valid_reference(self, url: str, all_files: List[str]) -> bool:
        """检查引用是否有效"""
        if url.startswith('http'):
            return True
        
        # 检查内部引用
        for file_path in all_files:
            if url in file_path:
                return True
        return False


class EnhancedQualityChecker:
    """增强版质量检查器"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.checkers = {
            'content': ContentQualityChecker(),
            'format': FormatChecker(),
            'links': LinkChecker(),
            'code': CodeQualityChecker(),
            'cross_ref': CrossReferenceChecker()
        }
        self.all_files = self._get_all_markdown_files()
    
    def _get_all_markdown_files(self) -> List[str]:
        """获取所有Markdown文件"""
        files = []
        for root, dirs, filenames in os.walk(self.base_path):
            for filename in filenames:
                if filename.endswith('.md'):
                    files.append(os.path.join(root, filename))
        return files
    
    def check_document(self, file_path: str) -> QualityScore:
        """检查单个文档"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return QualityScore(
                file_path=file_path,
                title_hierarchy=0,
                content_depth=0,
                code_quality=0,
                math_formulas=0,
                links=0,
                format=0,
                cross_references=0,
                overall=0,
                issues=[QualityIssue(
                    file_path=file_path,
                    line_number=1,
                    issue_type="file_error",
                    description=f"文件读取错误: {str(e)}",
                    severity="error"
                )],
                word_count=0,
                code_block_count=0,
                math_formula_count=0,
                link_count=0
            )
        
        # 计算基础指标
        word_count = len(content.split())
        code_block_count = len(re.findall(r'```\w+', content))
        math_formula_count = len(re.findall(r'\$[^$]+\$', content))
        link_count = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content))
        
        # 执行各项检查
        scores = {}
        all_issues = []
        
        # 内容质量检查
        scores['content_depth'], content_issues = self.checkers['content'].check(file_path, content)
        all_issues.extend(content_issues)
        
        # 格式检查
        scores['format'], format_issues = self.checkers['format'].check(file_path, content)
        all_issues.extend(format_issues)
        
        # 链接检查
        scores['links'], link_issues = self.checkers['links'].check(file_path, content, self.base_path)
        all_issues.extend(link_issues)
        
        # 代码质量检查
        scores['code_quality'], code_issues = self.checkers['code'].check(file_path, content)
        all_issues.extend(code_issues)
        
        # 交叉引用检查
        scores['cross_references'], cross_ref_issues = self.checkers['cross_ref'].check(file_path, content, self.all_files)
        all_issues.extend(cross_ref_issues)
        
        # 计算总体分数
        overall = sum(scores.values()) / len(scores)
        
        return QualityScore(
            file_path=file_path,
            title_hierarchy=scores.get('format', 0),
            content_depth=scores.get('content_depth', 0),
            code_quality=scores.get('code_quality', 0),
            math_formulas=scores.get('format', 0),
            links=scores.get('links', 0),
            format=scores.get('format', 0),
            cross_references=scores.get('cross_references', 0),
            overall=overall,
            issues=all_issues,
            word_count=word_count,
            code_block_count=code_block_count,
            math_formula_count=math_formula_count,
            link_count=link_count
        )
    
    def check_all_documents(self) -> List[QualityScore]:
        """检查所有文档"""
        results = []
        for file_path in self.all_files:
            result = self.check_document(file_path)
            results.append(result)
        return results
    
    def generate_report(self, results: List[QualityScore], output_format: str = 'html') -> str:
        """生成质量报告"""
        if output_format == 'html':
            return self._generate_html_report(results)
        elif output_format == 'json':
            return self._generate_json_report(results)
        else:
            return self._generate_text_report(results)
    
    def _generate_html_report(self, results: List[QualityScore]) -> str:
        """生成HTML报告"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>数据科学知识库质量检查报告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
                .summary { margin: 20px 0; }
                .document { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
                .score { font-weight: bold; }
                .error { color: red; }
                .warning { color: orange; }
                .info { color: blue; }
                .issue { margin: 5px 0; padding: 5px; background-color: #f9f9f9; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>数据科学知识库质量检查报告</h1>
                <p>生成时间: {}</p>
            </div>
        """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # 总体统计
        total_docs = len(results)
        avg_score = sum(r.overall for r in results) / total_docs if total_docs > 0 else 0
        total_issues = sum(len(r.issues) for r in results)
        
        html += f"""
            <div class="summary">
                <h2>总体统计</h2>
                <p>检查文档数: {total_docs}</p>
                <p>平均质量分数: {avg_score:.2f}</p>
                <p>总问题数: {total_issues}</p>
            </div>
        """
        
        # 文档详情
        for result in sorted(results, key=lambda x: x.overall):
            html += f"""
                <div class="document">
                    <h3>{result.file_path}</h3>
                    <p class="score">总体分数: {result.overall:.2f}</p>
                    <p>字数: {result.word_count}, 代码块: {result.code_block_count}, 数学公式: {result.math_formula_count}, 链接: {result.link_count}</p>
            """
            
            if result.issues:
                html += "<h4>问题列表:</h4>"
                for issue in result.issues:
                    html += f"""
                        <div class="issue {issue.severity}">
                            <strong>{issue.issue_type}</strong> (第{issue.line_number}行): {issue.description}
                            {f'<br>建议: {issue.suggestion}' if issue.suggestion else ''}
                        </div>
                    """
            
            html += "</div>"
        
        html += "</body></html>"
        return html
    
    def _generate_json_report(self, results: List[QualityScore]) -> str:
        """生成JSON报告"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'total_documents': len(results),
            'average_score': sum(r.overall for r in results) / len(results) if results else 0,
            'total_issues': sum(len(r.issues) for r in results),
            'documents': [asdict(result) for result in results]
        }
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    def _generate_text_report(self, results: List[QualityScore]) -> str:
        """生成文本报告"""
        report = f"""
数据科学知识库质量检查报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

总体统计:
- 检查文档数: {len(results)}
- 平均质量分数: {sum(r.overall for r in results) / len(results) if results else 0:.2f}
- 总问题数: {sum(len(r.issues) for r in results)}

文档详情:
"""
        
        for result in sorted(results, key=lambda x: x.overall):
            report += f"""
{result.file_path}
- 总体分数: {result.overall:.2f}
- 字数: {result.word_count}, 代码块: {result.code_block_count}, 数学公式: {result.math_formula_count}, 链接: {result.link_count}
"""
            
            if result.issues:
                report += "- 问题:\n"
                for issue in result.issues:
                    report += f"  * {issue.severity.upper()}: {issue.description}\n"
                    if issue.suggestion:
                        report += f"    建议: {issue.suggestion}\n"
        
        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据科学知识库质量检查工具')
    parser.add_argument('--path', default='.', help='检查路径')
    parser.add_argument('--output', default='quality_report.html', help='输出文件')
    parser.add_argument('--format', choices=['html', 'json', 'text'], default='html', help='输出格式')
    parser.add_argument('--single', help='检查单个文件')
    
    args = parser.parse_args()
    
    checker = EnhancedQualityChecker(args.path)
    
    if args.single:
        # 检查单个文件
        result = checker.check_document(args.single)
        results = [result]
    else:
        # 检查所有文件
        results = checker.check_all_documents()
    
    # 生成报告
    report = checker.generate_report(results, args.format)
    
    # 保存报告
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"质量检查完成，报告已保存到: {args.output}")
    print(f"检查了 {len(results)} 个文档")
    print(f"平均质量分数: {sum(r.overall for r in results) / len(results) if results else 0:.2f}")


if __name__ == '__main__':
    main() 