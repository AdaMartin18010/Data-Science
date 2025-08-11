#!/usr/bin/env python3
"""
简化版质量检查工具
专注于基本的文档质量评估，避免复杂依赖
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any


class SimpleQualityChecker:
    """简化版质量检查器"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.all_files = self._get_all_markdown_files()
    
    def _get_all_markdown_files(self) -> List[str]:
        """获取所有Markdown文件"""
        files = []
        for root, dirs, filenames in os.walk(self.base_path):
            for filename in filenames:
                if filename.endswith('.md'):
                    files.append(os.path.join(root, filename))
        return files
    
    def check_document(self, file_path: str) -> Dict[str, Any]:
        """检查单个文档"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {
                'file_path': file_path,
                'error': str(e),
                'score': 0,
                'metrics': {},
                'issues': []
            }
        
        # 计算基础指标
        lines = content.split('\n')
        line_count = len(lines)
        word_count = len(content.split())
        
        # 检查代码块
        code_blocks = re.findall(r'```\w+', content)
        code_block_count = len(code_blocks)
        
        # 检查数学公式
        math_formulas = re.findall(r'\$[^$]+\$', content)
        math_formula_count = len(math_formulas)
        
        # 检查链接
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        link_count = len(links)
        
        # 检查标题
        titles = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
        title_count = len(titles)
        
        # 计算质量分数
        score = 100.0
        issues = []
        
        # 检查内容长度
        if line_count < 100:
            score -= 30
            issues.append({
                'type': 'content_length',
                'severity': 'high',
                'description': f'文档内容过短，当前{line_count}行，建议至少100行'
            })
        elif line_count < 500:
            score -= 10
            issues.append({
                'type': 'content_length',
                'severity': 'medium',
                'description': f'文档内容较短，当前{line_count}行，建议扩充到500行以上'
            })
        
        # 检查代码示例
        if code_block_count == 0:
            score -= 15
            issues.append({
                'type': 'no_code_examples',
                'severity': 'medium',
                'description': '缺少代码示例'
            })
        
        # 检查数学公式
        if math_formula_count == 0:
            score -= 10
            issues.append({
                'type': 'no_math_formulas',
                'severity': 'low',
                'description': '缺少数学公式'
            })
        
        # 检查链接
        if link_count == 0:
            score -= 5
            issues.append({
                'type': 'no_links',
                'severity': 'low',
                'description': '缺少内部或外部链接'
            })
        
        # 检查标题结构
        if title_count < 3:
            score -= 10
            issues.append({
                'type': 'poor_structure',
                'severity': 'medium',
                'description': '标题结构不完整，建议添加更多章节'
            })
        
        return {
            'file_path': file_path,
            'score': max(0, score),
            'metrics': {
                'line_count': line_count,
                'word_count': word_count,
                'code_block_count': code_block_count,
                'math_formula_count': math_formula_count,
                'link_count': link_count,
                'title_count': title_count
            },
            'issues': issues
        }
    
    def check_all_documents(self) -> List[Dict[str, Any]]:
        """检查所有文档"""
        results = []
        for file_path in self.all_files:
            result = self.check_document(file_path)
            results.append(result)
        return results
    
    def generate_report(self, results: List[Dict[str, Any]]) -> str:
        """生成质量报告"""
        # 过滤掉错误文件
        valid_results = [r for r in results if 'error' not in r]
        
        if not valid_results:
            return "没有找到有效的Markdown文件"
        
        # 计算统计信息
        total_docs = len(valid_results)
        avg_score = sum(r['score'] for r in valid_results) / total_docs
        total_issues = sum(len(r['issues']) for r in valid_results)
        
        # 按分数排序
        sorted_results = sorted(valid_results, key=lambda x: x['score'])
        
        # 生成报告
        report = f"""
# 数据科学知识库质量检查报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 总体统计

- **检查文档数**: {total_docs}
- **平均质量分数**: {avg_score:.2f}/100
- **总问题数**: {total_issues}

## 质量分布

- **优秀 (90-100分)**: {len([r for r in valid_results if r['score'] >= 90])} 个文档
- **良好 (70-89分)**: {len([r for r in valid_results if 70 <= r['score'] < 90])} 个文档
- **一般 (50-69分)**: {len([r for r in valid_results if 50 <= r['score'] < 70])} 个文档
- **需要改进 (0-49分)**: {len([r for r in valid_results if r['score'] < 50])} 个文档

## 文档详情

"""
        
        # 添加每个文档的详细信息
        for result in sorted_results:
            report += f"""
### {result['file_path']}

- **质量分数**: {result['score']:.2f}/100
- **行数**: {result['metrics']['line_count']}
- **字数**: {result['metrics']['word_count']}
- **代码块**: {result['metrics']['code_block_count']}
- **数学公式**: {result['metrics']['math_formula_count']}
- **链接**: {result['metrics']['link_count']}
- **标题**: {result['metrics']['title_count']}

"""
            
            if result['issues']:
                report += "**问题列表**:\n"
                for issue in result['issues']:
                    report += f"- **{issue['severity'].upper()}**: {issue['description']}\n"
                report += "\n"
        
        # 添加改进建议
        report += """
## 改进建议

### 高优先级
- 扩充内容过短的文档（<100行）
- 添加代码示例到缺少的文档
- 完善文档结构，添加更多章节

### 中优先级
- 添加数学公式和形式化定义
- 建立内部和外部链接
- 提升文档的实用性

### 低优先级
- 优化格式和排版
- 添加更多图表和示例
- 完善交叉引用

## 下一步行动

1. 优先处理分数低于50分的文档
2. 扩充内容过短的文档
3. 添加缺失的代码示例
4. 完善文档结构和导航
"""
        
        return report


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='简化版质量检查工具')
    parser.add_argument('--path', default='.', help='检查路径')
    parser.add_argument('--output', default='simple_quality_report.md', help='输出文件')
    
    args = parser.parse_args()
    
    checker = SimpleQualityChecker(args.path)
    results = checker.check_all_documents()
    report = checker.generate_report(results)
    
    # 保存报告
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"质量检查完成，报告已保存到: {args.output}")
    
    # 显示简要统计
    valid_results = [r for r in results if 'error' not in r]
    if valid_results:
        avg_score = sum(r['score'] for r in valid_results) / len(valid_results)
        print(f"检查了 {len(valid_results)} 个文档")
        print(f"平均质量分数: {avg_score:.2f}/100")
        
        # 显示需要改进的文档
        low_score_docs = [r for r in valid_results if r['score'] < 50]
        if low_score_docs:
            print(f"\n需要优先改进的文档 ({len(low_score_docs)} 个):")
            for doc in low_score_docs[:5]:  # 显示前5个
                print(f"- {doc['file_path']} (分数: {doc['score']:.2f})")


if __name__ == '__main__':
    main() 