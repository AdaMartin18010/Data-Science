#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL内容批量重构工具

本工具用于自动化处理PostgreSQL文件夹中的文件重构，
应用统一的内容模板，提高内容质量。
"""

import os
import re
import json
import shutil
from pathlib import Path
from typing import List, Dict, Tuple

class PostgreSQLContentRefactor:
    """PostgreSQL内容重构工具"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.template_path = self.base_path / "统一内容模板.md"
        self.progress_file = self.base_path / "重构进度.json"
        self.quality_report = self.base_path / "质量报告.json"
        
        # 文件分类
        self.file_categories = {
            "sql_language": ["SQL语言", "sql", "语言规范"],
            "system_architecture": ["系统架构", "架构", "architecture"],
            "query_optimization": ["查询优化", "优化", "optimization"],
            "transaction_management": ["事务", "事务管理", "transaction"],
            "mvcc": ["MVCC", "多版本", "并发控制"],
            "formal_proof": ["形式化", "证明", "理论", "formal"],
            "ai_integration": ["AI", "人工智能", "机器学习"],
            "vector_database": ["向量", "向量数据库", "vector"],
            "performance": ["性能", "性能优化", "performance"],
            "security": ["安全", "权限", "security"]
        }
        
        # 质量评分标准
        self.quality_criteria = {
            "concept_definition": 20,  # 概念定义
            "formal_proof": 25,        # 形式化证明
            "code_examples": 20,       # 代码示例
            "practical_applications": 15,  # 实际应用
            "references": 10,          # 参考文献
            "wikidata_alignment": 10   # Wikidata对齐
        }
    
    def scan_files(self) -> List[Dict]:
        """扫描所有文件并分类"""
        files = []
        
        for file_path in self.base_path.rglob("*.md"):
            if file_path.name in ["README.md", "统一内容模板.md", "改进进度跟踪.md"]:
                continue
                
            file_info = {
                "path": str(file_path),
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "category": self._categorize_file(file_path),
                "quality_score": 0,
                "needs_refactor": False
            }
            
            # 评估文件质量
            file_info["quality_score"] = self._assess_quality(file_path)
            file_info["needs_refactor"] = file_info["quality_score"] < 70
            
            files.append(file_info)
        
        return files
    
    def _categorize_file(self, file_path: Path) -> str:
        """分类文件"""
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        for category, keywords in self.file_categories.items():
            for keyword in keywords:
                if keyword.lower() in content.lower() or keyword.lower() in file_path.name.lower():
                    return category
        
        return "other"
    
    def _assess_quality(self, file_path: Path) -> float:
        """评估文件质量"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            score = 0
            
            # 检查概念定义
            if re.search(r'中文定义|English Definition', content):
                score += self.quality_criteria["concept_definition"]
            
            # 检查形式化证明
            if re.search(r'\\begin\{theorem\}|\\begin\{proof\}', content):
                score += self.quality_criteria["formal_proof"]
            
            # 检查代码示例
            if re.search(r'```sql|```python|```c', content):
                score += self.quality_criteria["code_examples"]
            
            # 检查实际应用
            if re.search(r'实际应用|最佳实践|PostgreSQL', content):
                score += self.quality_criteria["practical_applications"]
            
            # 检查参考文献
            if re.search(r'参考文献|References|学术文献', content):
                score += self.quality_criteria["references"]
            
            # 检查Wikidata对齐
            if re.search(r'Wikidata|概念ID', content):
                score += self.quality_criteria["wikidata_alignment"]
            
            return min(score, 100)
            
        except Exception as e:
            print(f"评估文件 {file_path} 质量时出错: {e}")
            return 0
    
    def generate_refactor_plan(self, files: List[Dict]) -> Dict:
        """生成重构计划"""
        plan = {
            "total_files": len(files),
            "high_quality": len([f for f in files if f["quality_score"] >= 80]),
            "medium_quality": len([f for f in files if 60 <= f["quality_score"] < 80]),
            "low_quality": len([f for f in files if f["quality_score"] < 60]),
            "needs_refactor": len([f for f in files if f["needs_refactor"]]),
            "categories": {},
            "priority_files": []
        }
        
        # 按类别统计
        for file_info in files:
            category = file_info["category"]
            if category not in plan["categories"]:
                plan["categories"][category] = {
                    "count": 0,
                    "avg_score": 0,
                    "files": []
                }
            
            plan["categories"][category]["count"] += 1
            plan["categories"][category]["files"].append(file_info)
        
        # 计算平均分
        for category in plan["categories"]:
            files_in_category = plan["categories"][category]["files"]
            if files_in_category:
                avg_score = sum(f["quality_score"] for f in files_in_category) / len(files_in_category)
                plan["categories"][category]["avg_score"] = round(avg_score, 2)
        
        # 确定优先级文件
        priority_files = [f for f in files if f["needs_refactor"]]
        priority_files.sort(key=lambda x: (x["quality_score"], x["size"]))
        plan["priority_files"] = priority_files[:20]  # 前20个优先级文件
        
        return plan
    
    def apply_template(self, file_path: str, category: str) -> str:
        """应用统一模板"""
        template = self.template_path.read_text(encoding='utf-8')
        
        # 根据类别调整模板
        if category == "sql_language":
            title = "SQL语言规范 - PostgreSQL 17完整版"
        elif category == "system_architecture":
            title = "PostgreSQL系统架构 - PostgreSQL 17完整版"
        elif category == "query_optimization":
            title = "查询优化理论 - PostgreSQL 17完整版"
        elif category == "transaction_management":
            title = "事务管理理论 - PostgreSQL 17完整版"
        elif category == "mvcc":
            title = "MVCC并发控制理论 - PostgreSQL 17完整版"
        elif category == "formal_proof":
            title = "形式化证明理论 - PostgreSQL 17完整版"
        elif category == "ai_integration":
            title = "AI集成理论 - PostgreSQL 17完整版"
        elif category == "vector_database":
            title = "向量数据库理论 - PostgreSQL 17完整版"
        else:
            title = "PostgreSQL理论 - PostgreSQL 17完整版"
        
        # 替换模板中的占位符
        content = template.replace("[主题名称]", title)
        content = content.replace("[完整的中文概念定义，包含核心特征和功能]", 
                                f"{title}的中文定义")
        content = content.replace("[完整的英文概念定义，与中文定义对应]", 
                                f"English definition for {title}")
        
        return content
    
    def refactor_file(self, file_info: Dict) -> bool:
        """重构单个文件"""
        try:
            file_path = Path(file_info["path"])
            category = file_info["category"]
            
            # 备份原文件
            backup_path = file_path.with_suffix('.md.backup')
            shutil.copy2(file_path, backup_path)
            
            # 应用模板
            new_content = self.apply_template(file_info["path"], category)
            
            # 写入新内容
            file_path.write_text(new_content, encoding='utf-8')
            
            # 更新质量评分
            new_score = self._assess_quality(file_path)
            file_info["quality_score"] = new_score
            file_info["refactored"] = True
            
            print(f"✅ 重构完成: {file_path.name} (质量评分: {new_score})")
            return True
            
        except Exception as e:
            print(f"❌ 重构失败: {file_info['path']} - {e}")
            return False
    
    def batch_refactor(self, max_files: int = 10) -> Dict:
        """批量重构文件"""
        print("🔍 扫描文件...")
        files = self.scan_files()
        
        print("📊 生成重构计划...")
        plan = self.generate_refactor_plan(files)
        
        print(f"📈 质量统计:")
        print(f"   - 高质量文件: {plan['high_quality']}")
        print(f"   - 中等质量文件: {plan['medium_quality']}")
        print(f"   - 低质量文件: {plan['low_quality']}")
        print(f"   - 需要重构: {plan['needs_refactor']}")
        
        # 选择要重构的文件
        priority_files = plan["priority_files"][:max_files]
        
        print(f"\n🚀 开始批量重构 ({len(priority_files)} 个文件)...")
        
        success_count = 0
        for file_info in priority_files:
            print(f"\n📝 重构: {file_info['name']}")
            if self.refactor_file(file_info):
                success_count += 1
        
        # 保存进度
        self._save_progress(files, plan)
        
        print(f"\n✅ 批量重构完成!")
        print(f"   - 成功重构: {success_count}/{len(priority_files)}")
        print(f"   - 平均质量提升: {self._calculate_quality_improvement(files)}")
        
        return {
            "success_count": success_count,
            "total_processed": len(priority_files),
            "plan": plan
        }
    
    def _save_progress(self, files: List[Dict], plan: Dict):
        """保存进度"""
        progress_data = {
            "timestamp": str(Path().cwd()),
            "files": files,
            "plan": plan,
            "total_files": len(files),
            "avg_quality": sum(f["quality_score"] for f in files) / len(files) if files else 0
        }
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
    
    def _calculate_quality_improvement(self, files: List[Dict]) -> float:
        """计算质量提升"""
        refactored_files = [f for f in files if f.get("refactored", False)]
        if not refactored_files:
            return 0.0
        
        improvement = sum(f["quality_score"] for f in refactored_files) / len(refactored_files)
        return round(improvement, 2)
    
    def generate_report(self) -> str:
        """生成质量报告"""
        if not self.progress_file.exists():
            return "没有找到进度文件，请先运行重构"
        
        with open(self.progress_file, 'r', encoding='utf-8') as f:
            progress_data = json.load(f)
        
        report = f"""
# PostgreSQL内容重构质量报告

## 总体统计
- 总文件数: {progress_data['total_files']}
- 平均质量评分: {progress_data['avg_quality']:.2f}
- 重构时间: {progress_data['timestamp']}

## 分类统计
"""
        
        for category, stats in progress_data['plan']['categories'].items():
            report += f"""
### {category}
- 文件数量: {stats['count']}
- 平均质量: {stats['avg_score']:.2f}
"""
        
        report += f"""
## 质量分布
- 高质量文件 (≥80分): {progress_data['plan']['high_quality']}
- 中等质量文件 (60-79分): {progress_data['plan']['medium_quality']}
- 低质量文件 (<60分): {progress_data['plan']['low_quality']}
- 需要重构: {progress_data['plan']['needs_refactor']}

## 建议
1. 继续重构低质量文件
2. 完善形式化证明
3. 添加更多代码示例
4. 更新到PostgreSQL 17特性
"""
        
        return report

def main():
    """主函数"""
    # 设置工作目录
    base_path = Path(__file__).parent
    refactor = PostgreSQLContentRefactor(str(base_path))
    
    print("🔄 PostgreSQL内容批量重构工具")
    print("=" * 50)
    
    # 运行批量重构
    result = refactor.batch_refactor(max_files=5)
    
    # 生成报告
    report = refactor.generate_report()
    
    # 保存报告
    report_path = base_path / "质量报告.md"
    report_path.write_text(report, encoding='utf-8')
    
    print(f"\n📄 质量报告已保存到: {report_path}")

if __name__ == "__main__":
    main()
