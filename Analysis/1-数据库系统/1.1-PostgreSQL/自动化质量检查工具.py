#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL知识体系自动化质量检查工具
用于检查文档质量、完整性、国际化程度等指标
"""

import os
import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PostgreSQLQualityChecker:
    """PostgreSQL知识体系质量检查器"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.quality_standards = self._load_quality_standards()
        self.report = {
            'overall_score': 0.0,
            'file_count': 0,
            'quality_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'detailed_reports': [],
            'improvement_suggestions': []
        }
    
    def _load_quality_standards(self) -> Dict[str, Any]:
        """加载质量标准"""
        return {
            'content_completeness': {
                'weight': 0.25,
                'criteria': {
                    'concept_definition': {'weight': 0.20, 'required': True},
                    'formal_notation': {'weight': 0.15, 'required': True},
                    'theoretical_basis': {'weight': 0.20, 'required': True},
                    'implementation': {'weight': 0.20, 'required': True},
                    'examples': {'weight': 0.15, 'required': True},
                    'references': {'weight': 0.10, 'required': True}
                }
            },
            'technical_accuracy': {
                'weight': 0.30,
                'criteria': {
                    'definition_accuracy': {'weight': 0.30, 'required': True},
                    'theoretical_correctness': {'weight': 0.25, 'required': True},
                    'code_executability': {'weight': 0.25, 'required': True},
                    'performance_analysis': {'weight': 0.20, 'required': True}
                }
            },
            'internationalization': {
                'weight': 0.25,
                'criteria': {
                    'bilingual_support': {'weight': 0.40, 'required': True},
                    'wiki_standards': {'weight': 0.30, 'required': True},
                    'wikidata_alignment': {'weight': 0.30, 'required': True}
                }
            },
            'practical_value': {
                'weight': 0.20,
                'criteria': {
                    'real_world_examples': {'weight': 0.50, 'required': True},
                    'best_practices': {'weight': 0.30, 'required': True},
                    'performance_guidance': {'weight': 0.20, 'required': True}
                }
            }
        }
    
    def check_all_files(self) -> Dict[str, Any]:
        """检查所有文件的质量"""
        logger.info("开始质量检查...")
        
        # 查找所有Markdown文件
        md_files = list(self.base_path.rglob("*.md"))
        logger.info(f"找到 {len(md_files)} 个Markdown文件")
        
        total_score = 0.0
        file_scores = []
        
        for file_path in md_files:
            try:
                file_report = self.check_single_file(file_path)
                file_scores.append(file_report['score'])
                self.report['detailed_reports'].append(file_report)
                
                # 更新质量分布
                if file_report['score'] >= 0.8:
                    self.report['quality_distribution']['high'] += 1
                elif file_report['score'] >= 0.6:
                    self.report['quality_distribution']['medium'] += 1
                else:
                    self.report['quality_distribution']['low'] += 1
                    
            except Exception as e:
                logger.error(f"检查文件 {file_path} 时出错: {e}")
        
        # 计算总体分数
        if file_scores:
            self.report['overall_score'] = sum(file_scores) / len(file_scores)
        
        self.report['file_count'] = len(md_files)
        self._generate_improvement_suggestions()
        
        logger.info(f"质量检查完成，总体分数: {self.report['overall_score']:.2f}")
        return self.report
    
    def check_single_file(self, file_path: Path) -> Dict[str, Any]:
        """检查单个文件的质量"""
        logger.info(f"检查文件: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_report = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'score': 0.0,
            'component_scores': {},
            'issues': [],
            'suggestions': []
        }
        
        # 检查各个质量维度
        for dimension, config in self.quality_standards.items():
            dimension_score = self._check_dimension(content, dimension, config)
            file_report['component_scores'][dimension] = dimension_score
        
        # 计算加权总分
        total_score = 0.0
        for dimension, config in self.quality_standards.items():
            total_score += file_report['component_scores'][dimension] * config['weight']
        
        file_report['score'] = total_score
        return file_report
    
    def _check_dimension(self, content: str, dimension: str, config: Dict[str, Any]) -> float:
        """检查特定质量维度"""
        dimension_score = 0.0
        criteria_scores = {}
        
        for criterion, criterion_config in config['criteria'].items():
            criterion_score = self._check_criterion(content, criterion, criterion_config)
            criteria_scores[criterion] = criterion_score
            dimension_score += criterion_score * criterion_config['weight']
        
        return dimension_score
    
    def _check_criterion(self, content: str, criterion: str, config: Dict[str, Any]) -> float:
        """检查特定标准"""
        if criterion == 'concept_definition':
            return self._check_concept_definition(content)
        elif criterion == 'formal_notation':
            return self._check_formal_notation(content)
        elif criterion == 'theoretical_basis':
            return self._check_theoretical_basis(content)
        elif criterion == 'implementation':
            return self._check_implementation(content)
        elif criterion == 'examples':
            return self._check_examples(content)
        elif criterion == 'references':
            return self._check_references(content)
        elif criterion == 'bilingual_support':
            return self._check_bilingual_support(content)
        elif criterion == 'wiki_standards':
            return self._check_wiki_standards(content)
        elif criterion == 'wikidata_alignment':
            return self._check_wikidata_alignment(content)
        elif criterion == 'real_world_examples':
            return self._check_real_world_examples(content)
        elif criterion == 'best_practices':
            return self._check_best_practices(content)
        elif criterion == 'performance_guidance':
            return self._check_performance_guidance(content)
        else:
            return 0.0
    
    def _check_concept_definition(self, content: str) -> float:
        """检查概念定义"""
        score = 0.0
        
        # 检查中文定义
        if re.search(r'##\s*1\.\s*概述|##\s*1\.\s*定义', content):
            score += 0.3
        
        # 检查英文定义
        if re.search(r'English|English Definition', content, re.IGNORECASE):
            score += 0.3
        
        # 检查形式化定义
        if re.search(r'```latex|\\newcommand|\\begin\{theorem\}', content):
            score += 0.4
        
        return min(score, 1.0)
    
    def _check_formal_notation(self, content: str) -> float:
        """检查形式化表示"""
        score = 0.0
        
        # 检查LaTeX数学符号
        latex_patterns = [
            r'\\[a-zA-Z]+\{[^}]+\}',  # 命令
            r'\\[a-zA-Z]+',           # 简单命令
            r'\\begin\{[^}]+\}',      # 环境开始
            r'\\end\{[^}]+\}',        # 环境结束
            r'\\[a-zA-Z]+\([^)]*\)'   # 带参数的命令
        ]
        
        for pattern in latex_patterns:
            if re.search(pattern, content):
                score += 0.2
        
        return min(score, 1.0)
    
    def _check_theoretical_basis(self, content: str) -> float:
        """检查理论基础"""
        score = 0.0
        
        # 检查定理和证明
        if re.search(r'\\begin\{theorem\}|\\begin\{proof\}', content):
            score += 0.4
        
        # 检查数学定义
        if re.search(r'\\newcommand|\\def|\\mathcal\{[^}]+\}', content):
            score += 0.3
        
        # 检查理论说明
        if re.search(r'理论基础|理论分析|数学基础', content):
            score += 0.3
        
        return min(score, 1.0)
    
    def _check_implementation(self, content: str) -> float:
        """检查实现代码"""
        score = 0.0
        
        # 检查SQL代码
        if re.search(r'```sql|CREATE TABLE|SELECT|INSERT|UPDATE|DELETE', content, re.IGNORECASE):
            score += 0.4
        
        # 检查算法伪代码
        if re.search(r'```|Algorithm:|Input:|Output:', content):
            score += 0.3
        
        # 检查配置示例
        if re.search(r'配置|参数|设置', content):
            score += 0.3
        
        return min(score, 1.0)
    
    def _check_examples(self, content: str) -> float:
        """检查应用实例"""
        score = 0.0
        
        # 检查应用场景
        if re.search(r'应用实例|应用场景|实际应用', content):
            score += 0.4
        
        # 检查代码示例
        if re.search(r'```sql|```python|```bash', content):
            score += 0.3
        
        # 检查性能分析
        if re.search(r'性能分析|性能测试|基准测试', content):
            score += 0.3
        
        return min(score, 1.0)
    
    def _check_references(self, content: str) -> float:
        """检查参考文献"""
        score = 0.0
        
        # 检查参考文献部分
        if re.search(r'##\s*参考文献|##\s*References|参考文献', content):
            score += 0.5
        
        # 检查引用格式
        if re.search(r'\[\d+\]|\([^)]*\d{4}[^)]*\)', content):
            score += 0.5
        
        return min(score, 1.0)
    
    def _check_bilingual_support(self, content: str) -> float:
        """检查双语支持"""
        score = 0.0
        
        # 检查中英文对照
        if re.search(r'中文.*English|English.*中文', content, re.IGNORECASE):
            score += 0.5
        
        # 检查英文术语
        if re.search(r'[A-Z][a-z]+.*[A-Z][a-z]+', content):
            score += 0.3
        
        # 检查翻译质量
        if len(re.findall(r'[a-zA-Z]', content)) > 100:
            score += 0.2
        
        return min(score, 1.0)
    
    def _check_wiki_standards(self, content: str) -> float:
        """检查Wiki标准"""
        score = 0.0
        
        # 检查标准格式
        if re.search(r'##\s*[1-9]\.|###\s*[1-9]\.', content):
            score += 0.3
        
        # 检查链接格式
        if re.search(r'\[[^\]]+\]\([^)]+\)|\[\[[^\]]+\]\]', content):
            score += 0.2
        
        # 检查表格格式
        if re.search(r'\|.*\|.*\|', content):
            score += 0.2
        
        # 检查代码块
        if re.search(r'```[a-zA-Z]*\n', content):
            score += 0.3
        
        return min(score, 1.0)
    
    def _check_wikidata_alignment(self, content: str) -> float:
        """检查Wikidata对齐"""
        score = 0.0
        
        # 检查Wikidata ID
        if re.search(r'Q\d+|Wikidata ID|wikidata', content, re.IGNORECASE):
            score += 0.5
        
        # 检查外部链接
        if re.search(r'https?://[^\s]+', content):
            score += 0.3
        
        # 检查属性定义
        if re.search(r'属性|property|attribute', content, re.IGNORECASE):
            score += 0.2
        
        return min(score, 1.0)
    
    def _check_real_world_examples(self, content: str) -> float:
        """检查实际应用案例"""
        score = 0.0
        
        # 检查企业应用
        if re.search(r'企业|公司|业务|生产环境', content):
            score += 0.4
        
        # 检查具体场景
        if re.search(r'银行|电商|物流|金融|医疗', content):
            score += 0.3
        
        # 检查数据规模
        if re.search(r'TB|GB|百万|千万|亿', content):
            score += 0.3
        
        return min(score, 1.0)
    
    def _check_best_practices(self, content: str) -> float:
        """检查最佳实践"""
        score = 0.0
        
        # 检查最佳实践
        if re.search(r'最佳实践|best practice|推荐做法', content, re.IGNORECASE):
            score += 0.4
        
        # 检查注意事项
        if re.search(r'注意|warning|caution|注意事項', content):
            score += 0.3
        
        # 检查优化建议
        if re.search(r'优化|优化建议|performance|tuning', content, re.IGNORECASE):
            score += 0.3
        
        return min(score, 1.0)
    
    def _check_performance_guidance(self, content: str) -> float:
        """检查性能指导"""
        score = 0.0
        
        # 检查性能指标
        if re.search(r'性能|performance|吞吐量|延迟|响应时间', content, re.IGNORECASE):
            score += 0.4
        
        # 检查复杂度分析
        if re.search(r'O\([^)]+\)|复杂度|complexity', content):
            score += 0.3
        
        # 检查监控指标
        if re.search(r'监控|monitoring|指标|metrics', content, re.IGNORECASE):
            score += 0.3
        
        return min(score, 1.0)
    
    def _generate_improvement_suggestions(self):
        """生成改进建议"""
        suggestions = []
        
        # 基于质量分布生成建议
        low_quality_count = self.report['quality_distribution']['low']
        if low_quality_count > 0:
            suggestions.append(f"发现 {low_quality_count} 个低质量文件，建议优先改进")
        
        # 基于总体分数生成建议
        if self.report['overall_score'] < 0.8:
            suggestions.append("总体质量分数较低，建议系统性地改进内容质量")
        
        # 基于文件数量生成建议
        if self.report['file_count'] < 20:
            suggestions.append("文件数量较少，建议扩充知识体系内容")
        
        self.report['improvement_suggestions'] = suggestions
    
    def generate_report(self, output_file: str = "quality_report.json"):
        """生成质量报告"""
        report_path = self.base_path / output_file
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"质量报告已保存到: {report_path}")
        
        # 打印摘要
        self._print_summary()
    
    def _print_summary(self):
        """打印质量检查摘要"""
        print("\n" + "="*60)
        print("PostgreSQL知识体系质量检查报告")
        print("="*60)
        print(f"总体质量分数: {self.report['overall_score']:.2f}")
        print(f"检查文件数量: {self.report['file_count']}")
        print("\n质量分布:")
        for level, count in self.report['quality_distribution'].items():
            percentage = (count / self.report['file_count'] * 100) if self.report['file_count'] > 0 else 0
            print(f"  {level}: {count} ({percentage:.1f}%)")
        
        if self.report['improvement_suggestions']:
            print("\n改进建议:")
            for suggestion in self.report['improvement_suggestions']:
                print(f"  - {suggestion}")
        
        print("="*60)

def main():
    """主函数"""
    # 创建质量检查器
    checker = PostgreSQLQualityChecker()
    
    # 执行质量检查
    checker.check_all_files()
    
    # 生成报告
    checker.generate_report()
    
    # 生成详细报告
    checker.generate_report("quality_report_detailed.json")

if __name__ == "__main__":
    main()
