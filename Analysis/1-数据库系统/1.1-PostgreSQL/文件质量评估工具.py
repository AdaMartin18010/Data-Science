#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL文件质量评估工具
用于自动化评估所有PostgreSQL相关文件的质量
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
import hashlib

class PostgreSQLFileQualityAssessor:
    """PostgreSQL文件质量评估器"""
    
    def __init__(self, directory: str):
        self.directory = Path(directory)
        self.results = {}
        self.quality_scores = {}
        
    def assess_all_files(self) -> Dict[str, Any]:
        """评估所有文件的质量"""
        print("开始评估PostgreSQL文件质量...")
        
        # 获取所有.md文件
        md_files = list(self.directory.glob("*.md"))
        print(f"发现 {len(md_files)} 个Markdown文件")
        
        for file_path in md_files:
            self.assess_single_file(file_path)
        
        # 生成统计报告
        self.generate_statistics()
        
        return self.results
    
    def assess_single_file(self, file_path: Path) -> Dict[str, Any]:
        """评估单个文件的质量"""
        file_name = file_path.name
        print(f"评估文件: {file_name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件 {file_name} 失败: {e}")
            return {}
        
        # 计算文件大小
        file_size = len(content)
        
        # 分析内容结构
        structure_score = self.analyze_structure(content)
        
        # 分析内容质量
        content_score = self.analyze_content_quality(content)
        
        # 分析技术深度
        technical_score = self.analyze_technical_depth(content)
        
        # 分析国际化程度
        international_score = self.analyze_internationalization(content)
        
        # 计算综合得分
        total_score = self.calculate_total_score(
            structure_score, content_score, technical_score, international_score
        )
        
        # 确定质量等级
        quality_level = self.determine_quality_level(total_score)
        
        result = {
            'file_name': file_name,
            'file_size': file_size,
            'structure_score': structure_score,
            'content_score': content_score,
            'technical_score': technical_score,
            'international_score': international_score,
            'total_score': total_score,
            'quality_level': quality_level,
            'issues': self.identify_issues(content, total_score),
            'recommendations': self.generate_recommendations(total_score, quality_level)
        }
        
        self.results[file_name] = result
        self.quality_scores[file_name] = total_score
        
        return result
    
    def analyze_structure(self, content: str) -> float:
        """分析文档结构质量"""
        score = 0.0
        
        # 检查标题层级
        headers = re.findall(r'^#{1,6}\s+', content, re.MULTILINE)
        if len(headers) >= 3:
            score += 20
        
        # 检查目录结构
        if '##' in content and '###' in content:
            score += 15
        
        # 检查代码块
        code_blocks = re.findall(r'```[\w]*\n.*?```', content, re.DOTALL)
        if code_blocks:
            score += 15
        
        # 检查列表和表格
        if re.search(r'^\s*[-*+]\s+', content, re.MULTILINE):
            score += 10
        
        # 检查链接
        links = re.findall(r'\[.*?\]\(.*?\)', content)
        if links:
            score += 10
        
        return min(score, 100.0)
    
    def analyze_content_quality(self, content: str) -> float:
        """分析内容质量"""
        score = 0.0
        
        # 检查内容长度
        if len(content) > 5000:
            score += 20
        elif len(content) > 2000:
            score += 15
        elif len(content) > 1000:
            score += 10
        elif len(content) > 500:
            score += 5
        
        # 检查中文内容
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        if chinese_chars > 100:
            score += 15
        elif chinese_chars > 50:
            score += 10
        elif chinese_chars > 20:
            score += 5
        
        # 检查英文内容
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', content))
        if english_words > 200:
            score += 15
        elif english_words > 100:
            score += 10
        elif english_words > 50:
            score += 5
        
        # 检查技术术语
        technical_terms = ['PostgreSQL', 'SQL', 'ACID', 'MVCC', '索引', '事务', '查询']
        term_count = sum(1 for term in technical_terms if term in content)
        score += term_count * 5
        
        # 检查代码示例
        sql_blocks = re.findall(r'```sql\n.*?```', content, re.DOTALL)
        score += len(sql_blocks) * 10
        
        return min(score, 100.0)
    
    def analyze_technical_depth(self, content: str) -> float:
        """分析技术深度"""
        score = 0.0
        
        # 检查数学公式
        math_formulas = re.findall(r'\$.*?\$', content)
        score += len(math_formulas) * 5
        
        # 检查LaTeX公式
        latex_blocks = re.findall(r'```latex\n.*?```', content, re.DOTALL)
        score += len(latex_blocks) * 15
        
        # 检查定理和证明
        if 'theorem' in content.lower() or '定理' in content:
            score += 20
        
        if 'proof' in content.lower() or '证明' in content:
            score += 20
        
        # 检查算法描述
        if 'algorithm' in content.lower() or '算法' in content:
            score += 15
        
        # 检查性能分析
        if 'performance' in content.lower() or '性能' in content:
            score += 10
        
        # 检查基准测试
        if 'benchmark' in content.lower() or '基准' in content:
            score += 10
        
        return min(score, 100.0)
    
    def analyze_internationalization(self, content: str) -> float:
        """分析国际化程度"""
        score = 0.0
        
        # 检查双语内容
        if re.search(r'[\u4e00-\u9fff].*[a-zA-Z]', content) or re.search(r'[a-zA-Z].*[\u4e00-\u9fff]', content):
            score += 20
        
        # 检查英文定义
        if re.search(r'English.*:', content, re.IGNORECASE):
            score += 15
        
        # 检查中文定义
        if re.search(r'中文.*:', content):
            score += 15
        
        # 检查参考文献
        if 'references' in content.lower() or '参考文献' in content:
            score += 15
        
        # 检查Wiki链接
        if 'wikipedia' in content.lower() or 'wikidata' in content.lower():
            score += 15
        
        # 检查学术引用
        if re.search(r'\[\d+\]', content):
            score += 10
        
        # 检查标准规范
        if 'ISO' in content or 'ANSI' in content or 'IEEE' in content:
            score += 10
        
        return min(score, 100.0)
    
    def calculate_total_score(self, structure: float, content: float, technical: float, international: float) -> float:
        """计算综合得分"""
        # 权重分配
        weights = {
            'structure': 0.2,
            'content': 0.3,
            'technical': 0.3,
            'international': 0.2
        }
        
        total_score = (
            structure * weights['structure'] +
            content * weights['content'] +
            technical * weights['technical'] +
            international * weights['international']
        )
        
        return round(total_score, 2)
    
    def determine_quality_level(self, score: float) -> str:
        """确定质量等级"""
        if score >= 80:
            return "高质量"
        elif score >= 60:
            return "中等质量"
        elif score >= 40:
            return "低质量"
        else:
            return "极低质量"
    
    def identify_issues(self, content: str, score: float) -> List[str]:
        """识别问题"""
        issues = []
        
        if len(content) < 1000:
            issues.append("内容过短，缺乏实质性内容")
        
        if not re.search(r'[\u4e00-\u9fff]', content):
            issues.append("缺乏中文内容")
        
        if not re.search(r'[a-zA-Z]', content):
            issues.append("缺乏英文内容")
        
        if not re.search(r'```', content):
            issues.append("缺乏代码示例")
        
        if not re.search(r'#{1,6}', content):
            issues.append("缺乏标题结构")
        
        if score < 40:
            issues.append("整体质量过低，需要大幅改进")
        
        return issues
    
    def generate_recommendations(self, score: float, level: str) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if score < 60:
            recommendations.append("需要大幅增加内容深度和广度")
            recommendations.append("补充形式化理论和数学证明")
            recommendations.append("添加可执行的代码示例")
            recommendations.append("增加实际应用案例")
        
        if level == "中等质量":
            recommendations.append("完善理论证明体系")
            recommendations.append("增加国际化内容")
            recommendations.append("补充最新技术特性")
        
        if level == "高质量":
            recommendations.append("保持现有质量水平")
            recommendations.append("持续更新技术内容")
            recommendations.append("完善引用和参考文献")
        
        return recommendations
    
    def generate_statistics(self):
        """生成统计报告"""
        total_files = len(self.results)
        if total_files == 0:
            return
        
        # 质量等级统计
        quality_counts = {}
        for result in self.results.values():
            level = result['quality_level']
            quality_counts[level] = quality_counts.get(level, 0) + 1
        
        # 平均分数
        avg_score = sum(self.quality_scores.values()) / total_files
        
        # 文件大小统计
        sizes = [result['file_size'] for result in self.results.values()]
        avg_size = sum(sizes) / len(sizes)
        
        statistics = {
            'total_files': total_files,
            'quality_distribution': quality_counts,
            'average_score': round(avg_score, 2),
            'average_size': round(avg_size, 2),
            'score_distribution': {
                '80-100': len([s for s in self.quality_scores.values() if s >= 80]),
                '60-79': len([s for s in self.quality_scores.values() if 60 <= s < 80]),
                '40-59': len([s for s in self.quality_scores.values() if 40 <= s < 60]),
                '0-39': len([s for s in self.quality_scores.values() if s < 40])
            }
        }
        
        self.results['statistics'] = statistics
    
    def save_results(self, output_file: str = "quality_assessment_results.json"):
        """保存评估结果"""
        output_path = self.directory / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"评估结果已保存到: {output_path}")
    
    def generate_report(self) -> str:
        """生成评估报告"""
        if not self.results or 'statistics' not in self.results:
            return "没有评估结果"
        
        stats = self.results['statistics']
        
        report = f"""
# PostgreSQL文件质量评估报告

## 总体统计

- **总文件数**: {stats['total_files']}
- **平均质量分数**: {stats['average_score']}
- **平均文件大小**: {stats['average_size']} 字符

## 质量分布

- **高质量文件**: {stats['quality_distribution'].get('高质量', 0)} 个
- **中等质量文件**: {stats['quality_distribution'].get('中等质量', 0)} 个
- **低质量文件**: {stats['quality_distribution'].get('低质量', 0)} 个
- **极低质量文件**: {stats['quality_distribution'].get('极低质量', 0)} 个

## 分数分布

- **80-100分**: {stats['score_distribution']['80-100']} 个文件
- **60-79分**: {stats['score_distribution']['60-79']} 个文件
- **40-59分**: {stats['score_distribution']['40-59']} 个文件
- **0-39分**: {stats['score_distribution']['0-39']} 个文件

## 详细评估结果

"""
        
        # 按分数排序
        sorted_files = sorted(
            [(name, result) for name, result in self.results.items() if name != 'statistics'],
            key=lambda x: x[1]['total_score'],
            reverse=True
        )
        
        for file_name, result in sorted_files:
            report += f"""
### {file_name}

- **质量等级**: {result['quality_level']}
- **综合分数**: {result['total_score']}
- **文件大小**: {result['file_size']} 字符
- **结构分数**: {result['structure_score']}
- **内容分数**: {result['content_score']}
- **技术分数**: {result['technical_score']}
- **国际化分数**: {result['international_score']}

**问题**:
"""
            for issue in result['issues']:
                report += f"- {issue}\n"
            
            report += "\n**改进建议**:\n"
            for rec in result['recommendations']:
                report += f"- {rec}\n"
        
        return report

def main():
    """主函数"""
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 创建评估器
    assessor = PostgreSQLFileQualityAssessor(current_dir)
    
    # 执行评估
    assessor.assess_all_files()
    
    # 保存结果
    assessor.save_results()
    
    # 生成报告
    report = assessor.generate_report()
    
    # 保存报告
    report_file = os.path.join(current_dir, "质量评估报告.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"评估报告已保存到: {report_file}")
    
    # 打印摘要
    stats = assessor.results.get('statistics', {})
    if stats:
        print(f"\n评估摘要:")
        print(f"总文件数: {stats['total_files']}")
        print(f"平均分数: {stats['average_score']}")
        print(f"高质量文件: {stats['quality_distribution'].get('高质量', 0)}")
        print(f"中等质量文件: {stats['quality_distribution'].get('中等质量', 0)}")
        print(f"低质量文件: {stats['quality_distribution'].get('低质量', 0)}")
        print(f"极低质量文件: {stats['quality_distribution'].get('极低质量', 0)}")

if __name__ == "__main__":
    main()
