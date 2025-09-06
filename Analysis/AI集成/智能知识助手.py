#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL知识库智能助手 - 2025增强版
集成AI功能，提供智能问答、内容推荐、学习路径规划
"""

import os
import json
import re
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
from pathlib import Path
import yaml
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import jieba
import jieba.analyse

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class KnowledgeItem:
    """知识项数据类"""
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    difficulty: str  # beginner, intermediate, advanced
    language: str
    file_path: str
    last_updated: datetime
    view_count: int = 0
    rating: float = 0.0

@dataclass
class UserProfile:
    """用户画像数据类"""
    user_id: str
    interests: List[str]
    skill_level: str
    learning_goals: List[str]
    completed_items: List[str]
    bookmarked_items: List[str]
    learning_history: List[Dict[str, Any]]
    preferences: Dict[str, Any]

@dataclass
class Question:
    """问题数据类"""
    question_id: str
    content: str
    category: str
    difficulty: str
    context: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: datetime = None

@dataclass
class Answer:
    """答案数据类"""
    answer_id: str
    question_id: str
    content: str
    confidence: float
    sources: List[str]
    related_topics: List[str]
    generated_at: datetime

class KnowledgeBase:
    """知识库管理器"""
    
    def __init__(self, base_path: str = "Analysis"):
        self.base_path = Path(base_path)
        self.knowledge_items = {}
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.content_vectors = None
        self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """加载知识库"""
        
        logger.info("加载知识库...")
        
        # 扫描所有Markdown文件
        for md_file in self.base_path.rglob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 提取元数据
                metadata = self.extract_metadata(content, md_file)
                
                # 创建知识项
                knowledge_item = KnowledgeItem(
                    id=metadata['id'],
                    title=metadata['title'],
                    content=content,
                    category=metadata['category'],
                    tags=metadata['tags'],
                    difficulty=metadata['difficulty'],
                    language=metadata['language'],
                    file_path=str(md_file),
                    last_updated=datetime.fromtimestamp(md_file.stat().st_mtime)
                )
                
                self.knowledge_items[knowledge_item.id] = knowledge_item
                
            except Exception as e:
                logger.error(f"加载文件失败 {md_file}: {e}")
        
        logger.info(f"知识库加载完成，共 {len(self.knowledge_items)} 个知识项")
        
        # 构建向量索引
        self.build_vector_index()
    
    def extract_metadata(self, content: str, file_path: Path) -> Dict[str, Any]:
        """提取文档元数据"""
        
        # 提取标题
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else file_path.stem
        
        # 提取分类
        category = self.infer_category(file_path)
        
        # 提取标签
        tags = self.extract_tags(content)
        
        # 推断难度
        difficulty = self.infer_difficulty(content)
        
        # 推断语言
        language = self.detect_language(content)
        
        # 生成ID
        item_id = self.generate_id(file_path)
        
        return {
            'id': item_id,
            'title': title,
            'category': category,
            'tags': tags,
            'difficulty': difficulty,
            'language': language
        }
    
    def infer_category(self, file_path: Path) -> str:
        """推断文档分类"""
        
        path_str = str(file_path)
        
        if '数据库系统' in path_str or 'database' in path_str.lower():
            return 'database'
        elif '形式科学理论' in path_str or 'formal' in path_str.lower():
            return 'formal_science'
        elif '数据模型与算法' in path_str or 'algorithm' in path_str.lower():
            return 'algorithm'
        elif '软件架构与工程' in path_str or 'architecture' in path_str.lower():
            return 'architecture'
        elif '行业应用与场景' in path_str or 'application' in path_str.lower():
            return 'application'
        elif '知识图谱与可视化' in path_str or 'visualization' in path_str.lower():
            return 'visualization'
        elif '持续集成与演进' in path_str or 'integration' in path_str.lower():
            return 'integration'
        else:
            return 'other'
    
    def extract_tags(self, content: str) -> List[str]:
        """提取标签"""
        
        # 使用jieba提取关键词
        keywords = jieba.analyse.extract_tags(content, topK=10, withWeight=False)
        
        # 提取技术术语
        tech_terms = re.findall(r'\b[A-Z][a-z]+[A-Z][a-z]+\b', content)
        
        # 提取数据库相关术语
        db_terms = re.findall(r'\b(?:PostgreSQL|MySQL|MongoDB|Redis|SQL|NoSQL|ACID|MVCC|索引|查询|优化)\b', content)
        
        # 合并并去重
        all_tags = list(set(keywords + tech_terms + db_terms))
        
        return all_tags[:15]  # 限制标签数量
    
    def infer_difficulty(self, content: str) -> str:
        """推断难度级别"""
        
        # 高级概念关键词
        advanced_keywords = [
            '形式化', '证明', '定理', '算法复杂度', '分布式', '并发控制',
            'formal', 'proof', 'theorem', 'complexity', 'distributed', 'concurrency'
        ]
        
        # 中级概念关键词
        intermediate_keywords = [
            '优化', '性能', '架构', '设计模式', '最佳实践',
            'optimization', 'performance', 'architecture', 'design pattern', 'best practice'
        ]
        
        # 基础概念关键词
        beginner_keywords = [
            '基础', '入门', '简介', '概述', '基本概念',
            'basic', 'introduction', 'overview', 'fundamental'
        ]
        
        content_lower = content.lower()
        
        advanced_count = sum(1 for keyword in advanced_keywords if keyword.lower() in content_lower)
        intermediate_count = sum(1 for keyword in intermediate_keywords if keyword.lower() in content_lower)
        beginner_count = sum(1 for keyword in beginner_keywords if keyword.lower() in content_lower)
        
        if advanced_count > intermediate_count and advanced_count > beginner_count:
            return 'advanced'
        elif intermediate_count > beginner_count:
            return 'intermediate'
        else:
            return 'beginner'
    
    def detect_language(self, content: str) -> str:
        """检测语言"""
        
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        english_chars = len(re.findall(r'[a-zA-Z]', content))
        
        if chinese_chars > english_chars:
            return 'zh-CN'
        else:
            return 'en-US'
    
    def generate_id(self, file_path: Path) -> str:
        """生成唯一ID"""
        
        relative_path = file_path.relative_to(self.base_path)
        return str(relative_path).replace('/', '_').replace('.md', '')
    
    def build_vector_index(self):
        """构建向量索引"""
        
        logger.info("构建向量索引...")
        
        # 准备文本内容
        texts = []
        for item in self.knowledge_items.values():
            # 组合标题、内容和标签
            combined_text = f"{item.title} {' '.join(item.tags)} {item.content[:1000]}"
            texts.append(combined_text)
        
        # 构建TF-IDF向量
        self.content_vectors = self.vectorizer.fit_transform(texts)
        
        logger.info("向量索引构建完成")
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """搜索知识库"""
        
        if self.content_vectors is None:
            return []
        
        # 将查询转换为向量
        query_vector = self.vectorizer.transform([query])
        
        # 计算相似度
        similarities = cosine_similarity(query_vector, self.content_vectors).flatten()
        
        # 获取最相似的结果
        item_ids = list(self.knowledge_items.keys())
        results = list(zip(item_ids, similarities))
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]

class AIKnowledgeAssistant:
    """AI知识助手"""
    
    def __init__(self, knowledge_base: KnowledgeBase):
        self.knowledge_base = knowledge_base
        self.user_profiles = {}
        self.conversation_history = {}
        self.ai_models = self.initialize_ai_models()
    
    def initialize_ai_models(self) -> Dict[str, Any]:
        """初始化AI模型"""
        
        # 这里可以集成实际的AI模型
        # 例如：OpenAI GPT、Claude、本地LLM等
        
        return {
            'question_answering': None,  # 问答模型
            'content_generation': None,  # 内容生成模型
            'recommendation': None,      # 推荐模型
            'translation': None          # 翻译模型
        }
    
    def answer_question(self, question: Question) -> Answer:
        """回答用户问题"""
        
        logger.info(f"处理问题: {question.content}")
        
        # 搜索相关知识
        search_results = self.knowledge_base.search(question.content, top_k=5)
        
        # 构建上下文
        context = self.build_context(search_results)
        
        # 生成答案
        answer_content = self.generate_answer(question.content, context)
        
        # 计算置信度
        confidence = self.calculate_confidence(question.content, answer_content, search_results)
        
        # 提取相关主题
        related_topics = self.extract_related_topics(search_results)
        
        # 创建答案对象
        answer = Answer(
            answer_id=f"ans_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            question_id=question.question_id,
            content=answer_content,
            confidence=confidence,
            sources=[item_id for item_id, _ in search_results],
            related_topics=related_topics,
            generated_at=datetime.now()
        )
        
        return answer
    
    def build_context(self, search_results: List[Tuple[str, float]]) -> str:
        """构建上下文"""
        
        context_parts = []
        
        for item_id, similarity in search_results:
            if similarity > 0.1:  # 相似度阈值
                item = self.knowledge_base.knowledge_items[item_id]
                context_parts.append(f"## {item.title}\n{item.content[:500]}...")
        
        return "\n\n".join(context_parts)
    
    def generate_answer(self, question: str, context: str) -> str:
        """生成答案"""
        
        # 这里集成实际的AI模型来生成答案
        # 实际实现中会调用AI服务
        
        # 模拟AI生成的答案
        answer_template = f"""
基于PostgreSQL知识库，我来回答您的问题：

**问题**: {question}

**答案**:
根据相关知识，这个问题涉及以下要点：

1. **核心概念**: 从上下文可以看出，这主要涉及数据库系统的核心概念。

2. **技术细节**: 基于相关文档，这里需要关注技术实现细节。

3. **最佳实践**: 建议参考相关的最佳实践指南。

4. **实际应用**: 在实际项目中，需要注意以下要点...

**相关资源**:
- 相关文档提供了详细的实现指南
- 建议查看具体的代码示例
- 可以参考性能优化建议

如果您需要更详细的信息，我可以为您提供相关的文档链接和代码示例。
"""
        
        return answer_template.strip()
    
    def calculate_confidence(self, question: str, answer: str, search_results: List[Tuple[str, float]]) -> float:
        """计算答案置信度"""
        
        # 基于搜索结果相似度计算置信度
        if not search_results:
            return 0.0
        
        # 取最高相似度作为基础置信度
        max_similarity = max(similarity for _, similarity in search_results)
        
        # 根据搜索结果数量调整
        result_count_factor = min(len(search_results) / 5, 1.0)
        
        # 根据答案长度调整
        answer_length_factor = min(len(answer) / 1000, 1.0)
        
        confidence = max_similarity * 0.6 + result_count_factor * 0.2 + answer_length_factor * 0.2
        
        return min(confidence, 1.0)
    
    def extract_related_topics(self, search_results: List[Tuple[str, float]]) -> List[str]:
        """提取相关主题"""
        
        topics = set()
        
        for item_id, similarity in search_results:
            if similarity > 0.1:
                item = self.knowledge_base.knowledge_items[item_id]
                topics.update(item.tags[:3])  # 取前3个标签
        
        return list(topics)[:10]  # 限制主题数量
    
    def recommend_content(self, user_id: str, limit: int = 10) -> List[str]:
        """推荐内容"""
        
        if user_id not in self.user_profiles:
            # 创建默认用户画像
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id,
                interests=[],
                skill_level='beginner',
                learning_goals=[],
                completed_items=[],
                bookmarked_items=[],
                learning_history=[],
                preferences={}
            )
        
        user_profile = self.user_profiles[user_id]
        
        # 基于用户画像推荐内容
        recommendations = []
        
        # 基于兴趣推荐
        if user_profile.interests:
            for interest in user_profile.interests:
                search_results = self.knowledge_base.search(interest, top_k=3)
                recommendations.extend([item_id for item_id, _ in search_results])
        
        # 基于技能水平推荐
        skill_based_items = [
            item_id for item_id, item in self.knowledge_base.knowledge_items.items()
            if item.difficulty == user_profile.skill_level
        ]
        recommendations.extend(skill_based_items[:5])
        
        # 基于学习目标推荐
        if user_profile.learning_goals:
            for goal in user_profile.learning_goals:
                search_results = self.knowledge_base.search(goal, top_k=2)
                recommendations.extend([item_id for item_id, _ in search_results])
        
        # 去重并限制数量
        unique_recommendations = list(dict.fromkeys(recommendations))
        
        return unique_recommendations[:limit]
    
    def plan_learning_path(self, user_id: str, goal: str) -> List[str]:
        """规划学习路径"""
        
        # 分析目标
        goal_analysis = self.analyze_learning_goal(goal)
        
        # 搜索相关知识点
        related_items = self.knowledge_base.search(goal, top_k=20)
        
        # 按难度和依赖关系排序
        learning_path = self.organize_learning_path(related_items, goal_analysis)
        
        return learning_path
    
    def analyze_learning_goal(self, goal: str) -> Dict[str, Any]:
        """分析学习目标"""
        
        # 提取关键词
        keywords = jieba.analyse.extract_tags(goal, topK=5)
        
        # 推断难度
        difficulty = self.infer_goal_difficulty(goal)
        
        # 推断所需技能
        required_skills = self.infer_required_skills(goal)
        
        return {
            'keywords': keywords,
            'difficulty': difficulty,
            'required_skills': required_skills,
            'estimated_time': self.estimate_learning_time(difficulty)
        }
    
    def infer_goal_difficulty(self, goal: str) -> str:
        """推断目标难度"""
        
        advanced_indicators = ['高级', '深入', '优化', '架构', '分布式', '并发']
        intermediate_indicators = ['应用', '实践', '项目', '开发', '设计']
        
        goal_lower = goal.lower()
        
        if any(indicator in goal_lower for indicator in advanced_indicators):
            return 'advanced'
        elif any(indicator in goal_lower for indicator in intermediate_indicators):
            return 'intermediate'
        else:
            return 'beginner'
    
    def infer_required_skills(self, goal: str) -> List[str]:
        """推断所需技能"""
        
        skills = []
        
        if '数据库' in goal or 'database' in goal.lower():
            skills.extend(['SQL', '数据库设计', '查询优化'])
        
        if 'PostgreSQL' in goal:
            skills.extend(['PostgreSQL', '关系数据库', 'ACID'])
        
        if '优化' in goal or 'optimization' in goal.lower():
            skills.extend(['性能调优', '索引优化', '查询分析'])
        
        if '架构' in goal or 'architecture' in goal.lower():
            skills.extend(['系统设计', '微服务', '分布式系统'])
        
        return list(set(skills))
    
    def estimate_learning_time(self, difficulty: str) -> int:
        """估算学习时间（小时）"""
        
        time_estimates = {
            'beginner': 20,
            'intermediate': 40,
            'advanced': 80
        }
        
        return time_estimates.get(difficulty, 30)
    
    def organize_learning_path(self, related_items: List[Tuple[str, float]], goal_analysis: Dict[str, Any]) -> List[str]:
        """组织学习路径"""
        
        # 按难度分组
        beginner_items = []
        intermediate_items = []
        advanced_items = []
        
        for item_id, similarity in related_items:
            item = self.knowledge_base.knowledge_items[item_id]
            
            if item.difficulty == 'beginner':
                beginner_items.append((item_id, similarity))
            elif item.difficulty == 'intermediate':
                intermediate_items.append((item_id, similarity))
            else:
                advanced_items.append((item_id, similarity))
        
        # 构建学习路径
        learning_path = []
        
        # 添加基础内容
        beginner_items.sort(key=lambda x: x[1], reverse=True)
        learning_path.extend([item_id for item_id, _ in beginner_items[:3]])
        
        # 添加中级内容
        intermediate_items.sort(key=lambda x: x[1], reverse=True)
        learning_path.extend([item_id for item_id, _ in intermediate_items[:4]])
        
        # 添加高级内容
        advanced_items.sort(key=lambda x: x[1], reverse=True)
        learning_path.extend([item_id for item_id, _ in advanced_items[:3]])
        
        return learning_path
    
    def update_user_profile(self, user_id: str, interaction_data: Dict[str, Any]):
        """更新用户画像"""
        
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id,
                interests=[],
                skill_level='beginner',
                learning_goals=[],
                completed_items=[],
                bookmarked_items=[],
                learning_history=[],
                preferences={}
            )
        
        user_profile = self.user_profiles[user_id]
        
        # 更新学习历史
        user_profile.learning_history.append({
            'timestamp': datetime.now().isoformat(),
            'action': interaction_data.get('action', 'unknown'),
            'item_id': interaction_data.get('item_id'),
            'duration': interaction_data.get('duration', 0)
        })
        
        # 更新兴趣
        if 'item_id' in interaction_data:
            item = self.knowledge_base.knowledge_items.get(interaction_data['item_id'])
            if item:
                user_profile.interests.extend(item.tags)
                user_profile.interests = list(set(user_profile.interests))  # 去重
        
        # 更新完成项目
        if interaction_data.get('action') == 'complete':
            user_profile.completed_items.append(interaction_data['item_id'])
        
        # 更新书签
        if interaction_data.get('action') == 'bookmark':
            user_profile.bookmarked_items.append(interaction_data['item_id'])

class SmartLearningSystem:
    """智能学习系统"""
    
    def __init__(self):
        self.knowledge_base = KnowledgeBase()
        self.ai_assistant = AIKnowledgeAssistant(self.knowledge_base)
        self.learning_analytics = LearningAnalytics()
    
    def process_user_query(self, user_id: str, query: str) -> Dict[str, Any]:
        """处理用户查询"""
        
        # 创建问题对象
        question = Question(
            question_id=f"q_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            content=query,
            category=self.infer_question_category(query),
            difficulty=self.infer_question_difficulty(query),
            user_id=user_id,
            timestamp=datetime.now()
        )
        
        # 获取AI答案
        answer = self.ai_assistant.answer_question(question)
        
        # 获取推荐内容
        recommendations = self.ai_assistant.recommend_content(user_id, limit=5)
        
        # 更新用户画像
        self.ai_assistant.update_user_profile(user_id, {
            'action': 'query',
            'query': query,
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            'question': asdict(question),
            'answer': asdict(answer),
            'recommendations': recommendations,
            'learning_insights': self.learning_analytics.get_insights(user_id)
        }
    
    def infer_question_category(self, query: str) -> str:
        """推断问题分类"""
        
        if any(keyword in query.lower() for keyword in ['数据库', 'database', 'postgresql', 'mysql']):
            return 'database'
        elif any(keyword in query.lower() for keyword in ['算法', 'algorithm', '优化', 'optimization']):
            return 'algorithm'
        elif any(keyword in query.lower() for keyword in ['架构', 'architecture', '设计', 'design']):
            return 'architecture'
        else:
            return 'general'
    
    def infer_question_difficulty(self, query: str) -> str:
        """推断问题难度"""
        
        advanced_keywords = ['高级', '深入', '复杂', '优化', '性能', '分布式']
        intermediate_keywords = ['应用', '实践', '项目', '开发']
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in advanced_keywords):
            return 'advanced'
        elif any(keyword in query_lower for keyword in intermediate_keywords):
            return 'intermediate'
        else:
            return 'beginner'

class LearningAnalytics:
    """学习分析"""
    
    def __init__(self):
        self.analytics_data = {}
    
    def get_insights(self, user_id: str) -> Dict[str, Any]:
        """获取学习洞察"""
        
        # 这里可以分析用户的学习模式、进度等
        return {
            'learning_streak': 7,
            'total_study_time': 25.5,
            'completed_topics': 12,
            'current_level': 'intermediate',
            'next_milestone': '完成高级查询优化学习',
            'recommended_focus': '性能调优和索引优化'
        }

def main():
    """主函数"""
    
    # 创建智能学习系统
    learning_system = SmartLearningSystem()
    
    # 示例：处理用户查询
    user_id = "user_001"
    query = "PostgreSQL查询优化有哪些最佳实践？"
    
    result = learning_system.process_user_query(user_id, query)
    
    print("智能助手响应:")
    print(f"问题: {result['question']['content']}")
    print(f"答案: {result['answer']['content'][:200]}...")
    print(f"置信度: {result['answer']['confidence']:.2f}")
    print(f"推荐内容: {result['recommendations']}")
    
    print("\n智能学习系统初始化完成！")

if __name__ == "__main__":
    main()
