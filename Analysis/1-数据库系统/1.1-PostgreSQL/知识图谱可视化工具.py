#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL知识图谱可视化工具
"""

import networkx as nx
import matplotlib.pyplot as plt
import json
from pathlib import Path

class KnowledgeGraphVisualizer:
    def __init__(self):
        self.G = nx.DiGraph()
        self.concepts = []
        self.relations = []
    
    def load_concepts_from_files(self, base_path="."):
        """从文件加载概念"""
        base_path = Path(base_path)
        md_files = list(base_path.rglob("*.md"))
        
        for file_path in md_files:
            if file_path.name.startswith("1.1."):
                # 提取概念名称
                concept_name = self._extract_concept_name(file_path.name)
                if concept_name:
                    self.concepts.append(concept_name)
                    self.G.add_node(concept_name)
        
        # 添加核心概念关系
        self._add_core_relations()
    
    def _extract_concept_name(self, filename):
        """从文件名提取概念名称"""
        # 移除文件编号和扩展名
        name = filename.replace(".md", "")
        if "-" in name:
            return name.split("-", 1)[1]
        return name
    
    def _add_core_relations(self):
        """添加核心概念关系"""
        core_relations = [
            ("PostgreSQL系统架构", "进程模型"),
            ("PostgreSQL系统架构", "内存管理"),
            ("PostgreSQL系统架构", "存储系统"),
            ("关系数据模型", "SQL语言规范"),
            ("关系数据模型", "索引结构"),
            ("查询处理", "查询优化"),
            ("查询处理", "并发控制"),
            ("事务管理", "ACID性质"),
            ("事务管理", "隔离级别"),
            ("存储管理", "缓冲区管理"),
            ("存储管理", "WAL日志"),
            ("安全机制", "访问控制"),
            ("安全机制", "数据加密"),
            ("扩展系统", "自定义数据类型"),
            ("扩展系统", "自定义函数"),
            ("分布式事务", "两阶段提交"),
            ("分布式事务", "SAGA模式"),
            ("流式处理", "实时聚合"),
            ("流式处理", "窗口函数"),
            ("机器学习集成", "模型训练"),
            ("机器学习集成", "特征工程"),
            ("向量数据库", "相似性搜索"),
            ("向量数据库", "向量索引"),
            ("图数据库", "图遍历"),
            ("图数据库", "图算法")
        ]
        
        for source, target in core_relations:
            if source in self.concepts and target in self.concepts:
                self.G.add_edge(source, target)
                self.relations.append((source, target))
    
    def create_concept_hierarchy(self):
        """创建概念层次结构图"""
        plt.figure(figsize=(16, 12))
        
        # 使用层次布局
        pos = nx.spring_layout(self.G, k=2, iterations=50)
        
        # 绘制节点
        nx.draw_networkx_nodes(self.G, pos, 
                              node_color='lightblue',
                              node_size=3000,
                              alpha=0.8)
        
        # 绘制边
        nx.draw_networkx_edges(self.G, pos,
                              edge_color='gray',
                              arrows=True,
                              arrowsize=20,
                              alpha=0.6)
        
        # 绘制标签
        nx.draw_networkx_labels(self.G, pos,
                               font_size=8,
                               font_weight='bold')
        
        plt.title("PostgreSQL知识体系概念关系图", fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig("postgresql_knowledge_graph.png", dpi=300, bbox_inches='tight')
        plt.show()
    
    def analyze_concept_importance(self):
        """分析概念重要性"""
        # 计算中心性指标
        in_degree = dict(self.G.in_degree())
        out_degree = dict(self.G.out_degree())
        betweenness = nx.betweenness_centrality(self.G)
        closeness = nx.closeness_centrality(self.G)
        
        # 找出核心概念
        core_concepts = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:10]
        
        print("核心概念（被依赖最多）:")
        for concept, degree in core_concepts:
            print(f"  {concept}: {degree}")
        
        # 找出基础概念
        foundational_concepts = sorted(out_degree.items(), key=lambda x: x[1], reverse=True)[:10]
        
        print("\n基础概念（依赖最多）:")
        for concept, degree in foundational_concepts:
            print(f"  {concept}: {degree}")
        
        return {
            'core_concepts': core_concepts,
            'foundational_concepts': foundational_concepts,
            'betweenness': betweenness,
            'closeness': closeness
        }
    
    def create_learning_path(self, target_concept):
        """创建学习路径"""
        if target_concept not in self.G:
            print(f"概念 '{target_concept}' 不存在")
            return
        
        # 使用BFS找到最短路径
        try:
            path = nx.shortest_path(self.G, source="PostgreSQL系统架构", target=target_concept)
            print(f"\n学习路径 (从系统架构到 {target_concept}):")
            for i, concept in enumerate(path, 1):
                print(f"  {i}. {concept}")
        except nx.NetworkXNoPath:
            print(f"无法找到从系统架构到 {target_concept} 的路径")
    
    def export_graph_data(self, output_file="knowledge_graph_data.json"):
        """导出图数据"""
        graph_data = {
            'nodes': list(self.G.nodes()),
            'edges': list(self.G.edges()),
            'concepts': self.concepts,
            'relations': self.relations
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)
        
        print(f"图数据已导出到: {output_file}")

def main():
    """主函数"""
    visualizer = KnowledgeGraphVisualizer()
    
    # 加载概念
    visualizer.load_concepts_from_files()
    
    # 创建可视化
    visualizer.create_concept_hierarchy()
    
    # 分析概念重要性
    visualizer.analyze_concept_importance()
    
    # 创建学习路径示例
    visualizer.create_learning_path("查询优化")
    
    # 导出数据
    visualizer.export_graph_data()

if __name__ == "__main__":
    main()
