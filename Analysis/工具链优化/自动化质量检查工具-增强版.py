#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL知识库自动化质量检查工具 - 2025增强版
支持AI驱动的质量分析、实时监控、智能推荐
"""

import os
import json
import re
import ast
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quality_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class QualityIssue:
    """质量问题数据类"""
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # critical, warning, info
    description: str
    suggestion: str
    confidence: float
    category: str
    auto_fixable: bool = False
    fix_suggestion: Optional[str] = None

@dataclass
class QualityMetrics:
    """质量指标数据类"""
    file_path: str
    overall_score: float
    content_quality: float
    structure_quality: float
    code_quality: float
    math_quality: float
    link_quality: float
    format_quality: float
    ai_enhancement_score: float
    issues: List[QualityIssue]
    recommendations: List[str]
    last_updated: datetime

class AIQualityAnalyzer:
    """AI驱动的质量分析器"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.cluster_model = KMeans(n_clusters=10, random_state=42)
        self.quality_patterns = self.load_quality_patterns()
        self.ml_model = self.load_ml_model()
    
    def load_quality_patterns(self) -> Dict[str, List[str]]:
        """加载质量模式"""
        return {
            'excellent_content': [
                'formal definition', 'mathematical proof', 'algorithm implementation',
                'performance analysis', 'real-world application', 'best practices'
            ],
            'good_structure': [
                'clear hierarchy', 'logical flow', 'comprehensive coverage',
                'cross-references', 'consistent formatting'
            ],
            'needs_improvement': [
                'incomplete', 'placeholder', 'todo', 'fixme', 'missing',
                'outdated', 'inconsistent', 'unclear'
            ]
        }
    
    def load_ml_model(self):
        """加载机器学习模型"""
        # 这里可以加载预训练的模型
        # 实际实现中会从文件或API加载
        return None
    
    def analyze_content_quality(self, content: str) -> Dict[str, float]:
        """AI分析内容质量"""
        
        # 特征提取
        features = self.extract_content_features(content)
        
        # 质量评分
        quality_scores = {
            'completeness': self.assess_completeness(features),
            'accuracy': self.assess_accuracy(features),
            'clarity': self.assess_clarity(features),
            'depth': self.assess_depth(features),
            'practicality': self.assess_practicality(features)
        }
        
        return quality_scores
    
    def extract_content_features(self, content: str) -> Dict[str, Any]:
        """提取内容特征"""
        
        features = {
            'word_count': len(content.split()),
            'math_formulas': len(re.findall(r'\$.*?\$', content)),
            'code_blocks': len(re.findall(r'```', content)),
            'headers': len(re.findall(r'^#+', content, re.MULTILINE)),
            'links': len(re.findall(r'\[.*?\]\(.*?\)', content)),
            'images': len(re.findall(r'!\[.*?\]\(.*?\)', content)),
            'tables': len(re.findall(r'\|.*\|', content)),
            'lists': len(re.findall(r'^\s*[-*+]', content, re.MULTILINE)),
            'references': len(re.findall(r'\[\d+\]', content)),
            'yaml_blocks': len(re.findall(r'^---\n.*?\n---', content, re.DOTALL)),
            'mermaid_diagrams': len(re.findall(r'```mermaid', content))
        }
        
        # 内容类型分析
        features['has_formal_definition'] = bool(re.search(r'formal.*definition|定义', content, re.IGNORECASE))
        features['has_proof'] = bool(re.search(r'proof|证明|theorem|定理', content, re.IGNORECASE))
        features['has_algorithm'] = bool(re.search(r'algorithm|算法|pseudocode', content, re.IGNORECASE))
        features['has_example'] = bool(re.search(r'example|示例|for example', content, re.IGNORECASE))
        features['has_performance'] = bool(re.search(r'performance|性能|complexity|复杂度', content, re.IGNORECASE))
        
        return features
    
    def assess_completeness(self, features: Dict[str, Any]) -> float:
        """评估完整性"""
        score = 0.0
        
        # 基础内容检查
        if features['word_count'] > 500:
            score += 0.2
        if features['headers'] >= 3:
            score += 0.2
        if features['has_formal_definition']:
            score += 0.2
        if features['has_example']:
            score += 0.2
        if features['references'] >= 2:
            score += 0.2
        
        return min(score, 1.0)
    
    def assess_accuracy(self, features: Dict[str, Any]) -> float:
        """评估准确性"""
        score = 0.0
        
        # 数学公式和代码块表示准确性
        if features['math_formulas'] > 0:
            score += 0.3
        if features['code_blocks'] > 0:
            score += 0.3
        if features['has_proof']:
            score += 0.2
        if features['has_algorithm']:
            score += 0.2
        
        return min(score, 1.0)
    
    def assess_clarity(self, features: Dict[str, Any]) -> float:
        """评估清晰性"""
        score = 0.0
        
        # 结构化内容
        if features['headers'] >= 5:
            score += 0.3
        if features['tables'] > 0:
            score += 0.2
        if features['lists'] >= 3:
            score += 0.2
        if features['mermaid_diagrams'] > 0:
            score += 0.3
        
        return min(score, 1.0)
    
    def assess_depth(self, features: Dict[str, Any]) -> float:
        """评估深度"""
        score = 0.0
        
        # 深度内容指标
        if features['word_count'] > 1000:
            score += 0.3
        if features['has_performance']:
            score += 0.2
        if features['yaml_blocks'] > 0:
            score += 0.2
        if features['references'] >= 5:
            score += 0.3
        
        return min(score, 1.0)
    
    def assess_practicality(self, features: Dict[str, Any]) -> float:
        """评估实用性"""
        score = 0.0
        
        # 实用性指标
        if features['code_blocks'] >= 2:
            score += 0.4
        if features['has_example']:
            score += 0.3
        if features['links'] >= 3:
            score += 0.3
        
        return min(score, 1.0)

class EnhancedQualityChecker:
    """增强版质量检查器"""
    
    def __init__(self, base_path: str = "Analysis"):
        self.base_path = Path(base_path)
        self.ai_analyzer = AIQualityAnalyzer()
        self.quality_rules = self.load_quality_rules()
        self.cache = {}
        self.metrics_history = []
        
    def load_quality_rules(self) -> Dict[str, Any]:
        """加载质量规则"""
        return {
            'title_hierarchy': {
                'max_skip': 1,
                'required_levels': ['#', '##', '###'],
                'penalty_per_skip': 0.1
            },
            'code_quality': {
                'min_comment_ratio': 0.1,
                'max_line_length': 120,
                'required_imports': ['typing', 'dataclasses']
            },
            'math_formulas': {
                'required_latex': True,
                'min_formulas': 1,
                'penalty_per_missing': 0.2
            },
            'links': {
                'min_internal_links': 2,
                'max_broken_links': 0,
                'penalty_per_broken': 0.3
            },
            'format': {
                'max_line_length': 120,
                'required_metadata': True,
                'consistent_encoding': 'utf-8'
            }
        }
    
    def check_file(self, file_path: Path) -> QualityMetrics:
        """检查单个文件"""
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 基础质量检查
            issues = self.basic_quality_check(file_path, content)
            
            # AI增强分析
            ai_scores = self.ai_analyzer.analyze_content_quality(content)
            
            # 计算综合评分
            scores = self.calculate_scores(content, issues, ai_scores)
            
            # 生成推荐
            recommendations = self.generate_recommendations(issues, ai_scores)
            
            return QualityMetrics(
                file_path=str(file_path),
                overall_score=scores['overall'],
                content_quality=scores['content'],
                structure_quality=scores['structure'],
                code_quality=scores['code'],
                math_quality=scores['math'],
                link_quality=scores['links'],
                format_quality=scores['format'],
                ai_enhancement_score=scores['ai_enhancement'],
                issues=issues,
                recommendations=recommendations,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error checking file {file_path}: {e}")
            return self.create_error_metrics(file_path, str(e))
    
    def basic_quality_check(self, file_path: Path, content: str) -> List[QualityIssue]:
        """基础质量检查"""
        
        issues = []
        lines = content.split('\n')
        
        # 标题层级检查
        issues.extend(self.check_title_hierarchy(lines))
        
        # 代码质量检查
        issues.extend(self.check_code_quality(content))
        
        # 数学公式检查
        issues.extend(self.check_math_formulas(content))
        
        # 链接检查
        issues.extend(self.check_links(content))
        
        # 格式检查
        issues.extend(self.check_format(lines))
        
        return issues
    
    def check_title_hierarchy(self, lines: List[str]) -> List[QualityIssue]:
        """检查标题层级"""
        
        issues = []
        header_levels = []
        
        for i, line in enumerate(lines):
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                header_levels.append((i + 1, level))
        
        # 检查层级跳跃
        for i in range(1, len(header_levels)):
            prev_level = header_levels[i-1][1]
            curr_level = header_levels[i][1]
            
            if curr_level - prev_level > 1:
                issues.append(QualityIssue(
                    file_path="",
                    line_number=header_levels[i][0],
                    issue_type="title_hierarchy",
                    severity="warning",
                    description=f"标题层级跳跃：从H{prev_level}跳到H{curr_level}",
                    suggestion="建议保持标题层级的连续性",
                    confidence=0.9,
                    category="structure",
                    auto_fixable=True,
                    fix_suggestion=f"将H{curr_level}改为H{prev_level + 1}"
                ))
        
        return issues
    
    def check_code_quality(self, content: str) -> List[QualityIssue]:
        """检查代码质量"""
        
        issues = []
        code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', content, re.DOTALL)
        
        for i, (lang, code) in enumerate(code_blocks):
            if lang in ['python', 'sql', 'javascript', 'typescript']:
                # 检查代码注释
                comment_lines = len([line for line in code.split('\n') if line.strip().startswith('#') or line.strip().startswith('--')])
                total_lines = len([line for line in code.split('\n') if line.strip()])
                
                if total_lines > 10 and comment_lines / total_lines < 0.1:
                    issues.append(QualityIssue(
                        file_path="",
                        line_number=0,
                        issue_type="code_quality",
                        severity="info",
                        description=f"代码块缺少注释（注释率：{comment_lines/total_lines:.1%}）",
                        suggestion="建议为复杂代码添加注释",
                        confidence=0.8,
                        category="code"
                    ))
                
                # 检查行长度
                long_lines = [line for line in code.split('\n') if len(line) > 120]
                if long_lines:
                    issues.append(QualityIssue(
                        file_path="",
                        line_number=0,
                        issue_type="code_quality",
                        severity="info",
                        description=f"代码行过长（{len(long_lines)}行超过120字符）",
                        suggestion="建议将长行拆分为多行",
                        confidence=0.7,
                        category="code"
                    ))
        
        return issues
    
    def check_math_formulas(self, content: str) -> List[QualityIssue]:
        """检查数学公式"""
        
        issues = []
        
        # 检查是否有数学公式
        math_formulas = re.findall(r'\$.*?\$', content)
        if not math_formulas:
            issues.append(QualityIssue(
                file_path="",
                line_number=0,
                issue_type="math_formulas",
                severity="info",
                description="文档缺少数学公式",
                suggestion="建议添加相关的数学定义和公式",
                confidence=0.6,
                category="content"
            ))
        
        # 检查LaTeX语法
        for formula in math_formulas:
            if '\\' not in formula and len(formula) > 3:
                issues.append(QualityIssue(
                    file_path="",
                    line_number=0,
                    issue_type="math_formulas",
                    severity="warning",
                    description=f"数学公式可能缺少LaTeX语法：{formula}",
                    suggestion="建议使用标准LaTeX语法",
                    confidence=0.8,
                    category="format"
                ))
        
        return issues
    
    def check_links(self, content: str) -> List[QualityIssue]:
        """检查链接"""
        
        issues = []
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        
        # 检查内部链接
        internal_links = [link for _, url in links if not url.startswith('http')]
        if len(internal_links) < 2:
            issues.append(QualityIssue(
                file_path="",
                line_number=0,
                issue_type="links",
                severity="info",
                description=f"内部链接较少（{len(internal_links)}个）",
                suggestion="建议增加与其他文档的交叉引用",
                confidence=0.7,
                category="structure"
            ))
        
        return issues
    
    def check_format(self, lines: List[str]) -> List[QualityIssue]:
        """检查格式"""
        
        issues = []
        
        # 检查行长度
        long_lines = [(i+1, line) for i, line in enumerate(lines) if len(line) > 120]
        for line_num, line in long_lines:
            issues.append(QualityIssue(
                file_path="",
                line_number=line_num,
                issue_type="format",
                severity="info",
                description=f"行过长（{len(line)}字符）",
                suggestion="建议将长行拆分为多行",
                confidence=0.8,
                category="format",
                auto_fixable=True
            ))
        
        return issues
    
    def calculate_scores(self, content: str, issues: List[QualityIssue], ai_scores: Dict[str, float]) -> Dict[str, float]:
        """计算质量评分"""
        
        # 基础评分
        base_score = 10.0
        
        # 根据问题扣分
        for issue in issues:
            if issue.severity == 'critical':
                base_score -= 2.0
            elif issue.severity == 'warning':
                base_score -= 1.0
            elif issue.severity == 'info':
                base_score -= 0.5
        
        # AI增强评分
        ai_enhancement = sum(ai_scores.values()) / len(ai_scores) * 2.0
        
        # 各维度评分
        scores = {
            'overall': max(0, min(10, base_score + ai_enhancement)),
            'content': ai_scores.get('completeness', 5) * 2,
            'structure': ai_scores.get('clarity', 5) * 2,
            'code': 8.0 if not any(i.issue_type == 'code_quality' for i in issues) else 6.0,
            'math': 8.0 if not any(i.issue_type == 'math_formulas' for i in issues) else 6.0,
            'links': 8.0 if not any(i.issue_type == 'links' for i in issues) else 6.0,
            'format': 8.0 if not any(i.issue_type == 'format' for i in issues) else 6.0,
            'ai_enhancement': ai_enhancement
        }
        
        return scores
    
    def generate_recommendations(self, issues: List[QualityIssue], ai_scores: Dict[str, float]) -> List[str]:
        """生成改进建议"""
        
        recommendations = []
        
        # 基于问题生成建议
        issue_types = [issue.issue_type for issue in issues]
        
        if 'title_hierarchy' in issue_types:
            recommendations.append("优化文档结构，保持标题层级的连续性")
        
        if 'code_quality' in issue_types:
            recommendations.append("为代码添加详细注释，提高可读性")
        
        if 'math_formulas' in issue_types:
            recommendations.append("添加数学公式和形式化定义")
        
        if 'links' in issue_types:
            recommendations.append("增加内部链接和交叉引用")
        
        # 基于AI评分生成建议
        if ai_scores.get('completeness', 0) < 0.7:
            recommendations.append("完善文档内容，增加更多详细信息")
        
        if ai_scores.get('practicality', 0) < 0.7:
            recommendations.append("添加更多实际应用示例和代码")
        
        if ai_scores.get('depth', 0) < 0.7:
            recommendations.append("深入探讨技术细节和理论基础")
        
        return recommendations
    
    def create_error_metrics(self, file_path: Path, error: str) -> QualityMetrics:
        """创建错误指标"""
        
        return QualityMetrics(
            file_path=str(file_path),
            overall_score=0.0,
            content_quality=0.0,
            structure_quality=0.0,
            code_quality=0.0,
            math_quality=0.0,
            link_quality=0.0,
            format_quality=0.0,
            ai_enhancement_score=0.0,
            issues=[QualityIssue(
                file_path=str(file_path),
                line_number=0,
                issue_type="file_error",
                severity="critical",
                description=f"文件读取错误：{error}",
                suggestion="检查文件路径和权限",
                confidence=1.0,
                category="system"
            )],
            recommendations=["修复文件访问问题"],
            last_updated=datetime.now()
        )
    
    def check_all_files(self, max_workers: int = 4) -> Dict[str, QualityMetrics]:
        """检查所有文件"""
        
        logger.info("开始质量检查...")
        
        # 获取所有Markdown文件
        md_files = list(self.base_path.rglob("*.md"))
        logger.info(f"找到 {len(md_files)} 个Markdown文件")
        
        results = {}
        
        # 并行处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(self.check_file, file_path): file_path 
                            for file_path in md_files}
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    metrics = future.result()
                    results[str(file_path)] = metrics
                    logger.info(f"完成检查：{file_path}")
                except Exception as e:
                    logger.error(f"检查文件 {file_path} 时出错：{e}")
        
        # 保存结果
        self.save_results(results)
        
        return results
    
    def save_results(self, results: Dict[str, QualityMetrics]):
        """保存检查结果"""
        
        # 转换为可序列化格式
        serializable_results = {}
        for file_path, metrics in results.items():
            serializable_results[file_path] = {
                'file_path': metrics.file_path,
                'overall_score': metrics.overall_score,
                'content_quality': metrics.content_quality,
                'structure_quality': metrics.structure_quality,
                'code_quality': metrics.code_quality,
                'math_quality': metrics.math_quality,
                'link_quality': metrics.link_quality,
                'format_quality': metrics.format_quality,
                'ai_enhancement_score': metrics.ai_enhancement_score,
                'issues': [asdict(issue) for issue in metrics.issues],
                'recommendations': metrics.recommendations,
                'last_updated': metrics.last_updated.isoformat()
            }
        
        # 保存到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"quality_report_enhanced_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"质量检查结果已保存到：{output_file}")
        
        # 生成摘要报告
        self.generate_summary_report(results, f"quality_summary_{timestamp}.md")
    
    def generate_summary_report(self, results: Dict[str, QualityMetrics], output_file: str):
        """生成摘要报告"""
        
        total_files = len(results)
        avg_score = sum(metrics.overall_score for metrics in results.values()) / total_files
        
        # 统计问题
        total_issues = sum(len(metrics.issues) for metrics in results.values())
        critical_issues = sum(1 for metrics in results.values() 
                            for issue in metrics.issues if issue.severity == 'critical')
        warning_issues = sum(1 for metrics in results.values() 
                           for issue in metrics.issues if issue.severity == 'warning')
        
        # 生成报告
        report = f"""# 质量检查摘要报告

## 总体统计

- **检查文件数**: {total_files}
- **平均质量分数**: {avg_score:.2f}/10
- **总问题数**: {total_issues}
  - 严重问题: {critical_issues}
  - 警告问题: {warning_issues}
  - 信息问题: {total_issues - critical_issues - warning_issues}

## 质量分布

| 分数区间 | 文件数 | 占比 |
|---------|--------|------|
| 9.0-10.0 | {len([m for m in results.values() if m.overall_score >= 9.0])} | {len([m for m in results.values() if m.overall_score >= 9.0])/total_files*100:.1f}% |
| 8.0-8.9 | {len([m for m in results.values() if 8.0 <= m.overall_score < 9.0])} | {len([m for m in results.values() if 8.0 <= m.overall_score < 9.0])/total_files*100:.1f}% |
| 7.0-7.9 | {len([m for m in results.values() if 7.0 <= m.overall_score < 8.0])} | {len([m for m in results.values() if 7.0 <= m.overall_score < 8.0])/total_files*100:.1f}% |
| < 7.0 | {len([m for m in results.values() if m.overall_score < 7.0])} | {len([m for m in results.values() if m.overall_score < 7.0])/total_files*100:.1f}% |

## 改进建议

### 高优先级
1. 修复所有严重问题
2. 完善低分文档内容
3. 统一文档格式标准

### 中优先级
1. 增加数学公式和形式化定义
2. 完善代码注释和示例
3. 优化文档结构

### 低优先级
1. 增加交叉引用
2. 优化视觉效果
3. 完善元数据

## 详细结果

"""
        
        # 添加详细结果
        for file_path, metrics in sorted(results.items(), key=lambda x: x[1].overall_score):
            report += f"### {file_path}\n"
            report += f"- **总分**: {metrics.overall_score:.2f}/10\n"
            report += f"- **问题数**: {len(metrics.issues)}\n"
            if metrics.recommendations:
                report += f"- **建议**: {', '.join(metrics.recommendations[:3])}\n"
            report += "\n"
        
        # 保存报告
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"摘要报告已保存到：{output_file}")

def main():
    """主函数"""
    
    # 创建质量检查器
    checker = EnhancedQualityChecker()
    
    # 执行质量检查
    results = checker.check_all_files(max_workers=4)
    
    # 输出统计信息
    total_files = len(results)
    avg_score = sum(metrics.overall_score for metrics in results.values()) / total_files
    
    print(f"\n质量检查完成！")
    print(f"检查文件数: {total_files}")
    print(f"平均质量分数: {avg_score:.2f}/10")
    
    # 显示最需要改进的文件
    worst_files = sorted(results.items(), key=lambda x: x[1].overall_score)[:5]
    print(f"\n最需要改进的文件:")
    for file_path, metrics in worst_files:
        print(f"  {file_path}: {metrics.overall_score:.2f}/10")

if __name__ == "__main__":
    main()
