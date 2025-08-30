#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版PostgreSQL文件质量评估工具
"""

import os
import re
import json
from pathlib import Path

def assess_file_quality(file_path):
    """评估单个文件质量"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return {'score': 0, 'level': '极低质量', 'issues': ['文件无法读取']}
    
    score = 0
    issues = []
    
    # 文件大小评分
    size = len(content)
    if size > 10000:
        score += 30
    elif size > 5000:
        score += 20
    elif size > 2000:
        score += 15
    elif size > 1000:
        score += 10
    elif size > 500:
        score += 5
    else:
        issues.append("内容过短")
    
    # 结构评分
    if '##' in content:
        score += 15
    if '```' in content:
        score += 15
    if re.search(r'[\u4e00-\u9fff]', content):
        score += 10
    if re.search(r'[a-zA-Z]', content):
        score += 10
    
    # 技术深度评分
    if 'theorem' in content or '定理' in content:
        score += 20
    if 'PostgreSQL' in content:
        score += 10
    if 'SQL' in content:
        score += 10
    
    # 确定质量等级
    if score >= 80:
        level = '高质量'
    elif score >= 60:
        level = '中等质量'
    elif score >= 40:
        level = '低质量'
    else:
        level = '极低质量'
    
    return {
        'score': score,
        'level': level,
        'size': size,
        'issues': issues
    }

def main():
    """主函数"""
    current_dir = Path(__file__).parent
    results = {}
    
    # 评估所有.md文件
    for file_path in current_dir.glob("*.md"):
        if file_path.name.startswith('.'):
            continue
        
        result = assess_file_quality(file_path)
        results[file_path.name] = result
    
    # 统计
    total_files = len(results)
    high_quality = sum(1 for r in results.values() if r['level'] == '高质量')
    medium_quality = sum(1 for r in results.values() if r['level'] == '中等质量')
    low_quality = sum(1 for r in results.values() if r['level'] == '低质量')
    very_low_quality = sum(1 for r in results.values() if r['level'] == '极低质量')
    
    avg_score = sum(r['score'] for r in results.values()) / total_files if total_files > 0 else 0
    
    # 生成报告
    report = f"""
# PostgreSQL文件质量评估报告

## 统计摘要
- 总文件数: {total_files}
- 平均分数: {avg_score:.1f}
- 高质量: {high_quality} ({high_quality/total_files*100:.1f}%)
- 中等质量: {medium_quality} ({medium_quality/total_files*100:.1f}%)
- 低质量: {low_quality} ({low_quality/total_files*100:.1f}%)
- 极低质量: {very_low_quality} ({very_low_quality/total_files*100:.1f}%)

## 详细结果
"""
    
    # 按分数排序
    sorted_results = sorted(results.items(), key=lambda x: x[1]['score'], reverse=True)
    
    for filename, result in sorted_results:
        report += f"""
### {filename}
- 分数: {result['score']}
- 等级: {result['level']}
- 大小: {result['size']} 字符
- 问题: {', '.join(result['issues']) if result['issues'] else '无'}
"""
    
    # 保存报告
    with open(current_dir / '质量评估报告.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 保存JSON结果
    with open(current_dir / 'quality_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("评估完成！")
    print(f"总文件数: {total_files}")
    print(f"平均分数: {avg_score:.1f}")
    print(f"高质量文件: {high_quality}")
    print(f"需要改进的文件: {low_quality + very_low_quality}")

if __name__ == "__main__":
    main()
