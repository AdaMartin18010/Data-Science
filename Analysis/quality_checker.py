#!/usr/bin/env python3
"""
数据科学知识库自动化质量检查工具

该工具用于检查知识库文档的质量，包括：
- 文档结构检查
- 内容质量检查
- 格式规范性检查
- 交叉引用检查
- 代码示例检查
"""

import os
import re
import ast
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
import markdown
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class QualityIssue:
    """质量问题的数据结构"""
    file_path: str
    line_number: int
    issue_type: str
    description: str
    severity: str  # 'error', 'warning', 'info'
    suggestion: str = ""


@dataclass
class QualityScore:
    """质量评分数据结构"""
    file_path: str
    title_hierarchy: float
    code_quality: float
    math_formulas: float
    links: float
    format: float
    overall: float
    issues: List[QualityIssue]


class DocumentParser:
    """文档解析器"""
    
    def __init__(self):
        self.title_pattern = r'^(#{1,6})\s+(.+)$'
        self.code_pattern = r'```(\w+)?\n(.*?)```'
        self.math_pattern = r'\$([^$]+)\$'
        self.block_math_pattern = r'\$\$([^$]+)\$\$'
        self.link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    def parse_document(self, content: str) -> Dict[str, Any]:
        """解析文档内容"""
        return {
            'titles': self.extract_titles(content),
            'code_blocks': self.extract_code_blocks(content),
            'math_formulas': self.extract_math_formulas(content),
            'links': self.extract_links(content),
            'content': content
        }
    
    def extract_titles(self, content: str) -> List[Dict[str, Any]]:
        """提取标题层次"""
        titles = []
        for line_num, line in enumerate(content.split('\n'), 1):
            match = re.match(self.title_pattern, line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                titles.append({
                    'level': level,
                    'title': title,
                    'line_number': line_num
                })
        return titles
    
    def extract_code_blocks(self, content: str) -> List[Dict[str, Any]]:
        """提取代码块"""
        code_blocks = []
        for match in re.finditer(self.code_pattern, content, re.DOTALL):
            language = match.group(1) or 'text'
            code = match.group(2)
            code_blocks.append({
                'language': language,
                'code': code,
                'start_line': content[:match.start()].count('\n') + 1
            })
        return code_blocks
    
    def extract_math_formulas(self, content: str) -> Dict[str, List[str]]:
        """提取数学公式"""
        inline_formulas = re.findall(self.math_pattern, content)
        block_formulas = re.findall(self.block_math_pattern, content)
        
        return {
            'inline': inline_formulas,
            'block': block_formulas
        }
    
    def extract_links(self, content: str) -> List[Dict[str, str]]:
        """提取链接"""
        links = []
        for match in re.finditer(self.link_pattern, content):
            text = match.group(1)
            url = match.group(2)
            links.append({'text': text, 'url': url})
        return links


class QualityChecker:
    """质量检查器"""
    
    def __init__(self):
        self.parser = DocumentParser()
        self.issues = []
    
    def check_document(self, file_path: str) -> QualityScore:
        """检查单个文档的质量"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return QualityScore(
                file_path=file_path,
                title_hierarchy=0.0,
                code_quality=0.0,
                math_formulas=0.0,
                links=0.0,
                format=0.0,
                overall=0.0,
                issues=[QualityIssue(file_path, 0, 'error', f'无法读取文件: {e}', 'error')]
            )
        
        # 解析文档
        parsed = self.parser.parse_document(content)
        
        # 执行各项检查
        title_score, title_issues = self.check_title_hierarchy(parsed['titles'])
        code_score, code_issues = self.check_code_quality(parsed['code_blocks'])
        math_score, math_issues = self.check_math_formulas(parsed['math_formulas'])
        link_score, link_issues = self.check_links(parsed['links'], file_path)
        format_score, format_issues = self.check_format(content)
        
        # 合并所有问题
        all_issues = title_issues + code_issues + math_issues + link_issues + format_issues
        
        # 计算总体评分
        overall_score = (title_score + code_score + math_score + link_score + format_score) / 5
        
        return QualityScore(
            file_path=file_path,
            title_hierarchy=title_score,
            code_quality=code_score,
            math_formulas=math_score,
            links=link_score,
            format=format_score,
            overall=overall_score,
            issues=all_issues
        )
    
    def check_title_hierarchy(self, titles: List[Dict[str, Any]]) -> Tuple[float, List[QualityIssue]]:
        """检查标题层次"""
        issues = []
        score = 10.0
        
        if not titles:
            issues.append(QualityIssue(
                file_path="", line_number=0,
                issue_type="title_hierarchy",
                description="文档缺少标题",
                severity="warning"
            ))
            score -= 3.0
        
        # 检查标题层次跳跃
        for i, title in enumerate(titles):
            if i > 0:
                prev_level = titles[i-1]['level']
                curr_level = title['level']
                if curr_level > prev_level + 1:
                    issues.append(QualityIssue(
                        file_path="", line_number=title['line_number'],
                        issue_type="title_hierarchy",
                        description=f"标题层次跳跃: {title['title']}",
                        severity="warning",
                        suggestion="建议保持标题层次连续"
                    ))
                    score -= 1.0
            
            # 检查标题长度
            if len(title['title']) > 100:
                issues.append(QualityIssue(
                    file_path="", line_number=title['line_number'],
                    issue_type="title_hierarchy",
                    description=f"标题过长: {title['title']}",
                    severity="info",
                    suggestion="建议标题长度控制在100字符以内"
                ))
                score -= 0.5
        
        return max(0.0, score), issues
    
    def check_code_quality(self, code_blocks: List[Dict[str, Any]]) -> Tuple[float, List[QualityIssue]]:
        """检查代码质量"""
        issues = []
        score = 10.0
        
        for block in code_blocks:
            code = block['code']
            language = block['language']
            
            # 检查代码语法
            if language in ['python', 'rust', 'javascript']:
                try:
                    if language == 'python':
                        ast.parse(code)
                    # 其他语言的语法检查可以在这里添加
                except SyntaxError as e:
                    issues.append(QualityIssue(
                        file_path="", line_number=block['start_line'],
                        issue_type="code_quality",
                        description=f"语法错误: {e}",
                        severity="error"
                    ))
                    score -= 2.0
            
            # 检查代码长度
            if len(code.split('\n')) > 100:
                issues.append(QualityIssue(
                    file_path="", line_number=block['start_line'],
                    issue_type="code_quality",
                    description="代码块过长",
                    severity="warning",
                    suggestion="建议将长代码块分解为多个小段"
                ))
                score -= 1.0
            
            # 检查注释
            if language != 'text' and not re.search(r'#.*|//.*|/\*.*\*/', code):
                issues.append(QualityIssue(
                    file_path="", line_number=block['start_line'],
                    issue_type="code_quality",
                    description="代码缺少注释",
                    severity="info",
                    suggestion="建议为代码添加适当的注释"
                ))
                score -= 0.5
        
        return max(0.0, score), issues
    
    def check_math_formulas(self, formulas: Dict[str, List[str]]) -> Tuple[float, List[QualityIssue]]:
        """检查数学公式"""
        issues = []
        score = 10.0
        
        all_formulas = formulas['inline'] + formulas['block']
        
        for formula in all_formulas:
            # 检查基本的LaTeX语法
            if not self.is_valid_latex(formula):
                issues.append(QualityIssue(
                    file_path="", line_number=0,
                    issue_type="math_formulas",
                    description=f"LaTeX语法可能有问题: {formula}",
                    severity="warning"
                ))
                score -= 1.0
        
        return max(0.0, score), issues
    
    def is_valid_latex(self, formula: str) -> bool:
        """检查LaTeX语法是否基本正确"""
        # 简单的LaTeX语法检查
        # 检查括号匹配
        if formula.count('{') != formula.count('}'):
            return False
        
        if formula.count('(') != formula.count(')'):
            return False
        
        # 检查常见的LaTeX命令
        latex_commands = ['\\alpha', '\\beta', '\\gamma', '\\delta', '\\theta', 
                         '\\lambda', '\\mu', '\\sigma', '\\phi', '\\psi',
                         '\\sum', '\\prod', '\\int', '\\frac', '\\sqrt',
                         '\\text', '\\mathbf', '\\mathit', '\\mathcal']
        
        # 这里可以添加更复杂的LaTeX语法检查
        return True
    
    def check_links(self, links: List[Dict[str, str]], file_path: str) -> Tuple[float, List[QualityIssue]]:
        """检查链接有效性"""
        issues = []
        score = 10.0
        
        for link in links:
            url = link['url']
            
            # 检查内部链接
            if url.startswith('./') or url.startswith('../'):
                if not self.is_valid_internal_link(url, file_path):
                    issues.append(QualityIssue(
                        file_path="", line_number=0,
                        issue_type="links",
                        description=f"内部链接可能无效: {url}",
                        severity="warning"
                    ))
                    score -= 1.0
            
            # 检查外部链接格式
            elif url.startswith('http'):
                if not self.is_valid_external_link_format(url):
                    issues.append(QualityIssue(
                        file_path="", line_number=0,
                        issue_type="links",
                        description=f"外部链接格式可能有问题: {url}",
                        severity="info"
                    ))
                    score -= 0.5
        
        return max(0.0, score), issues
    
    def is_valid_internal_link(self, url: str, file_path: str) -> bool:
        """检查内部链接是否有效"""
        # 简化的内部链接检查
        # 在实际应用中，这里应该检查文件是否存在
        return True
    
    def is_valid_external_link_format(self, url: str) -> bool:
        """检查外部链接格式是否正确"""
        # 简单的URL格式检查
        return re.match(r'https?://[^\s/$.?#].[^\s]*', url) is not None
    
    def check_format(self, content: str) -> Tuple[float, List[QualityIssue]]:
        """检查格式规范性"""
        issues = []
        score = 10.0
        
        lines = content.split('\n')
        
        # 检查行长度
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(QualityIssue(
                    file_path="", line_number=i,
                    issue_type="format",
                    description=f"第{i}行过长",
                    severity="info",
                    suggestion="建议行长度控制在120字符以内"
                ))
                score -= 0.2
        
        # 检查空行使用
        if re.search(r'\n{4,}', content):
            issues.append(QualityIssue(
                file_path="", line_number=0,
                issue_type="format",
                description="空行使用过多",
                severity="info",
                suggestion="建议合理使用空行分隔内容"
            ))
            score -= 1.0
        
        return max(0.0, score), issues


class ReportGenerator:
    """报告生成器"""
    
    def generate_html_report(self, check_results: List[QualityScore]) -> str:
        """生成HTML格式的质量检查报告"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>知识库质量检查报告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .issue { color: red; }
                .warning { color: orange; }
                .info { color: blue; }
                .success { color: green; }
                .score { font-weight: bold; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>知识库质量检查报告</h1>
            <div class="summary">
                <h2>总体评分: <span class="score">{total_score}</span></h2>
                <p>检查时间: {timestamp}</p>
                <p>检查文件数: {file_count}</p>
            </div>
            <div class="details">
                {details}
            </div>
        </body>
        </html>
        """
        
        # 计算总体统计
        total_score = sum(r.overall for r in check_results) / len(check_results) if check_results else 0
        file_count = len(check_results)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 生成详细内容
        details = ""
        
        # 总体评分表格
        details += "<h3>总体评分</h3>"
        details += "<table>"
        details += "<tr><th>文件</th><th>总体评分</th><th>标题层次</th><th>代码质量</th><th>数学公式</th><th>链接</th><th>格式</th></tr>"
        
        for result in check_results:
            details += f"<tr>"
            details += f"<td>{result.file_path}</td>"
            details += f"<td class='score'>{result.overall:.1f}/10</td>"
            details += f"<td>{result.title_hierarchy:.1f}/10</td>"
            details += f"<td>{result.code_quality:.1f}/10</td>"
            details += f"<td>{result.math_formulas:.1f}/10</td>"
            details += f"<td>{result.links:.1f}/10</td>"
            details += f"<td>{result.format:.1f}/10</td>"
            details += f"</tr>"
        
        details += "</table>"
        
        # 问题详情
        details += "<h3>问题详情</h3>"
        for result in check_results:
            if result.issues:
                details += f"<h4>{result.file_path}</h4>"
                details += "<ul>"
                for issue in result.issues:
                    severity_class = issue.severity
                    details += f"<li class='{severity_class}'>{issue.description}"
                    if issue.suggestion:
                        details += f" (建议: {issue.suggestion})"
                    details += "</li>"
                details += "</ul>"
        
        return html_template.format(
            total_score=f"{total_score:.1f}/10",
            timestamp=timestamp,
            file_count=file_count,
            details=details
        )
    
    def generate_json_report(self, check_results: List[QualityScore]) -> str:
        """生成JSON格式的检查结果"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_files': len(check_results),
                'average_score': sum(r.overall for r in check_results) / len(check_results) if check_results else 0,
                'total_issues': sum(len(r.issues) for r in check_results)
            },
            'details': []
        }
        
        for result in check_results:
            detail = {
                'file_path': result.file_path,
                'scores': {
                    'overall': result.overall,
                    'title_hierarchy': result.title_hierarchy,
                    'code_quality': result.code_quality,
                    'math_formulas': result.math_formulas,
                    'links': result.links,
                    'format': result.format
                },
                'issues': [
                    {
                        'type': issue.issue_type,
                        'description': issue.description,
                        'severity': issue.severity,
                        'suggestion': issue.suggestion
                    }
                    for issue in result.issues
                ]
            }
            report['details'].append(detail)
        
        return json.dumps(report, indent=2, ensure_ascii=False)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='知识库质量检查工具')
    parser.add_argument('path', help='要检查的文件或目录路径')
    parser.add_argument('--format', choices=['html', 'json'], default='html',
                       help='输出格式 (默认: html)')
    parser.add_argument('--output', help='输出文件路径')
    
    args = parser.parse_args()
    
    # 创建检查器
    checker = QualityChecker()
    generator = ReportGenerator()
    
    # 收集要检查的文件
    files_to_check = []
    path = Path(args.path)
    
    if path.is_file():
        files_to_check = [str(path)]
    elif path.is_dir():
        for file_path in path.rglob('*.md'):
            files_to_check.append(str(file_path))
    
    # 执行检查
    results = []
    for file_path in files_to_check:
        print(f"检查文件: {file_path}")
        result = checker.check_document(file_path)
        results.append(result)
    
    # 生成报告
    if args.format == 'html':
        report = generator.generate_html_report(results)
    else:
        report = generator.generate_json_report(results)
    
    # 输出报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"报告已保存到: {args.output}")
    else:
        print(report)


if __name__ == '__main__':
    main() 