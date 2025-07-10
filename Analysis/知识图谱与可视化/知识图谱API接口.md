# 知识图谱API接口

## 1. RESTful API设计

### 基础API框架

```python
# 知识图谱API框架
from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uvicorn
from neo4j import GraphDatabase
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeGraphAPI:
    """知识图谱API服务"""
    
    def __init__(self, neo4j_uri: str, username: str, password: str):
        self.app = FastAPI(
            title="知识图谱API",
            description="数据科学知识图谱查询和管理API",
            version="1.0.0"
        )
        
        # 配置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 初始化数据库连接
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))
        
        # 注册路由
        self.register_routes()
    
    def register_routes(self):
        """注册API路由"""
        
        @self.app.get("/")
        async def root():
            """API根路径"""
            return {
                "message": "知识图谱API服务",
                "version": "1.0.0",
                "endpoints": [
                    "/api/nodes",
                    "/api/edges", 
                    "/api/search",
                    "/api/analysis",
                    "/api/visualization"
                ]
            }
        
        @self.app.get("/api/nodes")
        async def get_nodes(
            node_type: Optional[str] = Query(None, description="节点类型"),
            limit: int = Query(100, description="返回数量限制"),
            skip: int = Query(0, description="跳过数量")
        ):
            """获取节点列表"""
            try:
                with self.driver.session() as session:
                    if node_type:
                        query = """
                        MATCH (n)
                        WHERE n.type = $node_type
                        RETURN n
                        SKIP $skip
                        LIMIT $limit
                        """
                        result = session.run(query, node_type=node_type, skip=skip, limit=limit)
                    else:
                        query = """
                        MATCH (n)
                        RETURN n
                        SKIP $skip
                        LIMIT $limit
                        """
                        result = session.run(query, skip=skip, limit=limit)
                    
                    nodes = [dict(record["n"]) for record in result]
                    return {"nodes": nodes, "count": len(nodes)}
            
            except Exception as e:
                logger.error(f"获取节点失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/nodes/{node_id}")
        async def get_node(node_id: str = Path(..., description="节点ID")):
            """获取特定节点"""
            try:
                with self.driver.session() as session:
                    query = """
                    MATCH (n {id: $node_id})
                    RETURN n
                    """
                    result = session.run(query, node_id=node_id)
                    record = result.single()
                    
                    if not record:
                        raise HTTPException(status_code=404, detail="节点不存在")
                    
                    return {"node": dict(record["n"])}
            
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取节点失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/nodes/{node_id}/neighbors")
        async def get_node_neighbors(
            node_id: str = Path(..., description="节点ID"),
            relationship_type: Optional[str] = Query(None, description="关系类型"),
            depth: int = Query(1, description="搜索深度")
        ):
            """获取节点邻居"""
            try:
                with self.driver.session() as session:
                    if relationship_type:
                        query = """
                        MATCH (n {id: $node_id})-[r:$rel_type*1..$depth]-(neighbor)
                        RETURN neighbor, r
                        """
                        result = session.run(query, node_id=node_id, rel_type=relationship_type, depth=depth)
                    else:
                        query = """
                        MATCH (n {id: $node_id})-[r*1..$depth]-(neighbor)
                        RETURN neighbor, r
                        """
                        result = session.run(query, node_id=node_id, depth=depth)
                    
                    neighbors = []
                    for record in result:
                        neighbors.append({
                            "neighbor": dict(record["neighbor"]),
                            "relationships": [dict(r) for r in record["r"]]
                        })
                    
                    return {"neighbors": neighbors, "count": len(neighbors)}
            
            except Exception as e:
                logger.error(f"获取邻居失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/search")
        async def search_nodes(
            query: str = Query(..., description="搜索查询"),
            search_type: str = Query("fuzzy", description="搜索类型: fuzzy, exact, semantic")
        ):
            """搜索节点"""
            try:
                with self.driver.session() as session:
                    if search_type == "fuzzy":
                        cypher_query = """
                        MATCH (n)
                        WHERE n.name CONTAINS $query OR n.description CONTAINS $query
                        RETURN n
                        LIMIT 50
                        """
                    elif search_type == "exact":
                        cypher_query = """
                        MATCH (n)
                        WHERE n.name = $query
                        RETURN n
                        """
                    else:  # semantic
                        cypher_query = """
                        MATCH (n)
                        WHERE n.embedding IS NOT NULL
                        WITH n, gds.similarity.cosine(n.embedding, $query_embedding) AS similarity
                        WHERE similarity > 0.7
                        RETURN n, similarity
                        ORDER BY similarity DESC
                        LIMIT 50
                        """
                    
                    result = session.run(cypher_query, query=query)
                    nodes = [dict(record["n"]) for record in result]
                    
                    return {"results": nodes, "count": len(nodes), "query": query}
            
            except Exception as e:
                logger.error(f"搜索失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/analysis/centrality")
        async def get_centrality_analysis(
            centrality_type: str = Query("degree", description="中心性类型: degree, betweenness, closeness, eigenvector")
        ):
            """获取中心性分析"""
            try:
                with self.driver.session() as session:
                    if centrality_type == "degree":
                        query = """
                        MATCH (n)
                        RETURN n.name, size((n)--()) as degree
                        ORDER BY degree DESC
                        LIMIT 20
                        """
                    elif centrality_type == "betweenness":
                        query = """
                        CALL gds.betweenness.stream('knowledge-graph')
                        YIELD nodeId, score
                        RETURN gds.util.asNode(nodeId).name as name, score
                        ORDER BY score DESC
                        LIMIT 20
                        """
                    elif centrality_type == "closeness":
                        query = """
                        CALL gds.closeness.stream('knowledge-graph')
                        YIELD nodeId, score
                        RETURN gds.util.asNode(nodeId).name as name, score
                        ORDER BY score DESC
                        LIMIT 20
                        """
                    else:  # eigenvector
                        query = """
                        CALL gds.eigenvector.stream('knowledge-graph')
                        YIELD nodeId, score
                        RETURN gds.util.asNode(nodeId).name as name, score
                        ORDER BY score DESC
                        LIMIT 20
                        """
                    
                    result = session.run(query)
                    centrality_data = [{"name": record["name"], "score": record["score"]} for record in result]
                    
                    return {"centrality": centrality_data, "type": centrality_type}
            
            except Exception as e:
                logger.error(f"中心性分析失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/analysis/communities")
        async def get_community_analysis():
            """获取社区分析"""
            try:
                with self.driver.session() as session:
                    query = """
                    CALL gds.louvain.stream('knowledge-graph')
                    YIELD nodeId, communityId
                    RETURN communityId, collect(gds.util.asNode(nodeId).name) as members
                    ORDER BY size(collect(gds.util.asNode(nodeId).name)) DESC
                    """
                    
                    result = session.run(query)
                    communities = []
                    for record in result:
                        communities.append({
                            "community_id": record["communityId"],
                            "members": record["members"],
                            "size": len(record["members"])
                        })
                    
                    return {"communities": communities, "count": len(communities)}
            
            except Exception as e:
                logger.error(f"社区分析失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/paths/{source_id}/{target_id}")
        async def get_paths(
            source_id: str = Path(..., description="源节点ID"),
            target_id: str = Path(..., description="目标节点ID"),
            max_length: int = Query(5, description="最大路径长度")
        ):
            """获取节点间路径"""
            try:
                with self.driver.session() as session:
                    query = """
                    MATCH path = (source {id: $source_id})-[*1..$max_length]-(target {id: $target_id})
                    RETURN path
                    LIMIT 10
                    """
                    
                    result = session.run(query, source_id=source_id, target_id=target_id, max_length=max_length)
                    paths = []
                    for record in result:
                        path = record["path"]
                        path_data = {
                            "nodes": [dict(node) for node in path.nodes],
                            "relationships": [dict(rel) for rel in path.relationships],
                            "length": len(path.relationships)
                        }
                        paths.append(path_data)
                    
                    return {"paths": paths, "count": len(paths)}
            
            except Exception as e:
                logger.error(f"路径分析失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """运行API服务"""
        uvicorn.run(self.app, host=host, port=port)

# 使用示例
def create_api_service():
    """创建API服务"""
    api = KnowledgeGraphAPI(
        neo4j_uri="bolt://localhost:7687",
        username="neo4j",
        password="password"
    )
    return api
```

### 数据模型定义

```python
# API数据模型
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class NodeModel(BaseModel):
    """节点模型"""
    id: str = Field(..., description="节点唯一标识")
    name: str = Field(..., description="节点名称")
    type: str = Field(..., description="节点类型")
    description: Optional[str] = Field(None, description="节点描述")
    properties: Dict[str, Any] = Field(default_factory=dict, description="节点属性")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

class RelationshipModel(BaseModel):
    """关系模型"""
    source_id: str = Field(..., description="源节点ID")
    target_id: str = Field(..., description="目标节点ID")
    type: str = Field(..., description="关系类型")
    properties: Dict[str, Any] = Field(default_factory=dict, description="关系属性")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str = Field(..., description="搜索查询")
    search_type: str = Field("fuzzy", description="搜索类型")
    filters: Dict[str, Any] = Field(default_factory=dict, description="过滤条件")
    limit: int = Field(100, description="结果数量限制")

class AnalysisRequest(BaseModel):
    """分析请求模型"""
    analysis_type: str = Field(..., description="分析类型")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="分析参数")
    filters: Dict[str, Any] = Field(default_factory=dict, description="过滤条件")

class VisualizationRequest(BaseModel):
    """可视化请求模型"""
    visualization_type: str = Field(..., description="可视化类型")
    data_source: str = Field(..., description="数据源")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="可视化参数")
    format: str = Field("html", description="输出格式")
```

## 2. GraphQL API设计

### GraphQL Schema定义

```python
# GraphQL Schema
import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType
from typing import List, Dict, Any

class NodeType(graphene.ObjectType):
    """节点类型"""
    id = graphene.ID(required=True)
    name = graphene.String(required=True)
    type = graphene.String(required=True)
    description = graphene.String()
    properties = graphene.JSONString()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    
    # 关联字段
    neighbors = graphene.List(lambda: NodeType)
    relationships = graphene.List(lambda: RelationshipType)
    
    def resolve_neighbors(self, info):
        """解析邻居节点"""
        # 实现邻居节点查询逻辑
        pass
    
    def resolve_relationships(self, info):
        """解析关系"""
        # 实现关系查询逻辑
        pass

class RelationshipType(graphene.ObjectType):
    """关系类型"""
    id = graphene.ID(required=True)
    source_id = graphene.ID(required=True)
    target_id = graphene.ID(required=True)
    type = graphene.String(required=True)
    properties = graphene.JSONString()
    created_at = graphene.DateTime()
    
    # 关联字段
    source = graphene.Field(NodeType)
    target = graphene.Field(NodeType)
    
    def resolve_source(self, info):
        """解析源节点"""
        # 实现源节点查询逻辑
        pass
    
    def resolve_target(self, info):
        """解析目标节点"""
        # 实现目标节点查询逻辑
        pass

class Query(graphene.ObjectType):
    """查询根类型"""
    node = graphene.Field(NodeType, id=graphene.ID(required=True))
    nodes = graphene.List(NodeType, 
                         node_type=graphene.String(),
                         limit=graphene.Int(),
                         offset=graphene.Int())
    search = graphene.List(NodeType,
                          query=graphene.String(required=True),
                          search_type=graphene.String())
    relationships = graphene.List(RelationshipType,
                                source_id=graphene.ID(),
                                target_id=graphene.ID(),
                                relationship_type=graphene.String())
    
    def resolve_node(self, info, id):
        """解析单个节点"""
        # 实现节点查询逻辑
        pass
    
    def resolve_nodes(self, info, node_type=None, limit=100, offset=0):
        """解析节点列表"""
        # 实现节点列表查询逻辑
        pass
    
    def resolve_search(self, info, query, search_type="fuzzy"):
        """解析搜索"""
        # 实现搜索逻辑
        pass
    
    def resolve_relationships(self, info, source_id=None, target_id=None, relationship_type=None):
        """解析关系"""
        # 实现关系查询逻辑
        pass

class CreateNodeInput(graphene.InputObjectType):
    """创建节点输入"""
    name = graphene.String(required=True)
    type = graphene.String(required=True)
    description = graphene.String()
    properties = graphene.JSONString()

class CreateRelationshipInput(graphene.InputObjectType):
    """创建关系输入"""
    source_id = graphene.ID(required=True)
    target_id = graphene.ID(required=True)
    type = graphene.String(required=True)
    properties = graphene.JSONString()

class Mutation(graphene.ObjectType):
    """变更根类型"""
    create_node = graphene.Field(NodeType, input=CreateNodeInput(required=True))
    update_node = graphene.Field(NodeType, id=graphene.ID(required=True), input=CreateNodeInput(required=True))
    delete_node = graphene.Field(graphene.Boolean, id=graphene.ID(required=True))
    create_relationship = graphene.Field(RelationshipType, input=CreateRelationshipInput(required=True))
    
    def resolve_create_node(self, info, input):
        """创建节点"""
        # 实现节点创建逻辑
        pass
    
    def resolve_update_node(self, info, id, input):
        """更新节点"""
        # 实现节点更新逻辑
        pass
    
    def resolve_delete_node(self, info, id):
        """删除节点"""
        # 实现节点删除逻辑
        pass
    
    def resolve_create_relationship(self, info, input):
        """创建关系"""
        # 实现关系创建逻辑
        pass

# 创建Schema
schema = graphene.Schema(query=Query, mutation=Mutation)
```

### GraphQL服务实现

```python
# GraphQL服务实现
from ariadne import ObjectType, QueryType, MutationType, make_executable_schema
from ariadne.asgi import GraphQL
import asyncio

class GraphQLService:
    """GraphQL服务"""
    
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
        self.setup_schema()
    
    def setup_schema(self):
        """设置GraphQL Schema"""
        # 定义类型
        type_defs = """
        type Node {
            id: ID!
            name: String!
            type: String!
            description: String
            properties: JSON
            neighbors: [Node!]!
            relationships: [Relationship!]!
        }
        
        type Relationship {
            id: ID!
            source: Node!
            target: Node!
            type: String!
            properties: JSON
        }
        
        type Query {
            node(id: ID!): Node
            nodes(type: String, limit: Int, offset: Int): [Node!]!
            search(query: String!, type: String): [Node!]!
            relationships(sourceId: ID, targetId: ID, type: String): [Relationship!]!
        }
        
        type Mutation {
            createNode(input: CreateNodeInput!): Node!
            updateNode(id: ID!, input: UpdateNodeInput!): Node!
            deleteNode(id: ID!): Boolean!
            createRelationship(input: CreateRelationshipInput!): Relationship!
        }
        
        input CreateNodeInput {
            name: String!
            type: String!
            description: String
            properties: JSON
        }
        
        input UpdateNodeInput {
            name: String
            type: String
            description: String
            properties: JSON
        }
        
        input CreateRelationshipInput {
            sourceId: ID!
            targetId: ID!
            type: String!
            properties: JSON
        }
        
        scalar JSON
        """
        
        # 创建解析器
        query = QueryType()
        mutation = MutationType()
        node = ObjectType("Node")
        relationship = ObjectType("Relationship")
        
        # 查询解析器
        @query.field("node")
        def resolve_node(*_, id):
            with self.driver.session() as session:
                result = session.run("MATCH (n {id: $id}) RETURN n", id=id)
                record = result.single()
                return dict(record["n"]) if record else None
        
        @query.field("nodes")
        def resolve_nodes(*_, type=None, limit=100, offset=0):
            with self.driver.session() as session:
                if type:
                    query = "MATCH (n {type: $type}) RETURN n SKIP $offset LIMIT $limit"
                    result = session.run(query, type=type, offset=offset, limit=limit)
                else:
                    query = "MATCH (n) RETURN n SKIP $offset LIMIT $limit"
                    result = session.run(query, offset=offset, limit=limit)
                
                return [dict(record["n"]) for record in result]
        
        @query.field("search")
        def resolve_search(*_, query, type="fuzzy"):
            with self.driver.session() as session:
                if type == "fuzzy":
                    cypher_query = """
                    MATCH (n)
                    WHERE n.name CONTAINS $query OR n.description CONTAINS $query
                    RETURN n
                    LIMIT 50
                    """
                else:
                    cypher_query = "MATCH (n {name: $query}) RETURN n"
                
                result = session.run(cypher_query, query=query)
                return [dict(record["n"]) for record in result]
        
        # 节点解析器
        @node.field("neighbors")
        def resolve_neighbors(node, *_):
            with self.driver.session() as session:
                query = "MATCH (n {id: $id})--(neighbor) RETURN neighbor"
                result = session.run(query, id=node["id"])
                return [dict(record["neighbor"]) for record in result]
        
        @node.field("relationships")
        def resolve_relationships(node, *_):
            with self.driver.session() as session:
                query = "MATCH (n {id: $id})-[r]-(other) RETURN r, other"
                result = session.run(query, id=node["id"])
                relationships = []
                for record in result:
                    rel = dict(record["r"])
                    rel["source"] = node
                    rel["target"] = dict(record["other"])
                    relationships.append(rel)
                return relationships
        
        # 变更解析器
        @mutation.field("createNode")
        def resolve_create_node(*_, input):
            with self.driver.session() as session:
                query = """
                CREATE (n:Node {
                    id: randomUUID(),
                    name: $name,
                    type: $type,
                    description: $description,
                    properties: $properties
                })
                RETURN n
                """
                result = session.run(query, **input)
                record = result.single()
                return dict(record["n"])
        
        @mutation.field("updateNode")
        def resolve_update_node(*_, id, input):
            with self.driver.session() as session:
                query = """
                MATCH (n {id: $id})
                SET n += $properties
                RETURN n
                """
                properties = {k: v for k, v in input.items() if v is not None}
                result = session.run(query, id=id, properties=properties)
                record = result.single()
                return dict(record["n"]) if record else None
        
        @mutation.field("deleteNode")
        def resolve_delete_node(*_, id):
            with self.driver.session() as session:
                query = "MATCH (n {id: $id}) DETACH DELETE n"
                session.run(query, id=id)
                return True
        
        @mutation.field("createRelationship")
        def resolve_create_relationship(*_, input):
            with self.driver.session() as session:
                query = """
                MATCH (source {id: $sourceId}), (target {id: $targetId})
                CREATE (source)-[r:$type $properties]->(target)
                RETURN r, source, target
                """
                result = session.run(query, **input)
                record = result.single()
                if record:
                    rel = dict(record["r"])
                    rel["source"] = dict(record["source"])
                    rel["target"] = dict(record["target"])
                    return rel
                return None
        
        # 创建可执行schema
        self.schema = make_executable_schema(type_defs, query, mutation, node, relationship)
    
    def create_app(self):
        """创建GraphQL应用"""
        return GraphQL(self.schema, debug=True)
```

## 3. WebSocket实时API

### WebSocket服务实现

```python
# WebSocket实时API
import asyncio
import websockets
import json
from typing import Dict, Set, Any
import logging

logger = logging.getLogger(__name__)

class WebSocketService:
    """WebSocket实时服务"""
    
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.subscriptions: Dict[str, Set[websockets.WebSocketServerProtocol]] = {}
    
    async def register(self, websocket: websockets.WebSocketServerProtocol):
        """注册客户端"""
        self.clients.add(websocket)
        logger.info(f"客户端连接: {websocket.remote_address}")
    
    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        """注销客户端"""
        self.clients.remove(websocket)
        # 清理订阅
        for topic, subscribers in self.subscriptions.items():
            subscribers.discard(websocket)
        logger.info(f"客户端断开: {websocket.remote_address}")
    
    async def subscribe(self, websocket: websockets.WebSocketServerProtocol, topic: str):
        """订阅主题"""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        self.subscriptions[topic].add(websocket)
        await websocket.send(json.dumps({
            "type": "subscription",
            "topic": topic,
            "status": "subscribed"
        }))
    
    async def unsubscribe(self, websocket: websockets.WebSocketServerProtocol, topic: str):
        """取消订阅"""
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(websocket)
        await websocket.send(json.dumps({
            "type": "subscription",
            "topic": topic,
            "status": "unsubscribed"
        }))
    
    async def broadcast(self, message: Dict[str, Any], topic: str = None):
        """广播消息"""
        if topic and topic in self.subscriptions:
            # 发送到特定主题的订阅者
            disconnected = set()
            for client in self.subscriptions[topic]:
                try:
                    await client.send(json.dumps(message))
                except websockets.ConnectionClosed:
                    disconnected.add(client)
            
            # 清理断开的连接
            for client in disconnected:
                await self.unregister(client)
        else:
            # 发送到所有客户端
            disconnected = set()
            for client in self.clients:
                try:
                    await client.send(json.dumps(message))
                except websockets.ConnectionClosed:
                    disconnected.add(client)
            
            # 清理断开的连接
            for client in disconnected:
                await self.unregister(client)
    
    async def handle_message(self, websocket: websockets.WebSocketServerProtocol, message: Dict[str, Any]):
        """处理客户端消息"""
        try:
            msg_type = message.get("type")
            
            if msg_type == "subscribe":
                topic = message.get("topic")
                if topic:
                    await self.subscribe(websocket, topic)
            
            elif msg_type == "unsubscribe":
                topic = message.get("topic")
                if topic:
                    await self.unsubscribe(websocket, topic)
            
            elif msg_type == "query":
                query = message.get("query")
                if query:
                    result = await self.execute_query(query)
                    await websocket.send(json.dumps({
                        "type": "query_result",
                        "query": query,
                        "result": result
                    }))
            
            elif msg_type == "search":
                search_query = message.get("query")
                search_type = message.get("type", "fuzzy")
                if search_query:
                    result = await self.execute_search(search_query, search_type)
                    await websocket.send(json.dumps({
                        "type": "search_result",
                        "query": search_query,
                        "result": result
                    }))
            
            elif msg_type == "analysis":
                analysis_type = message.get("analysis_type")
                parameters = message.get("parameters", {})
                if analysis_type:
                    result = await self.execute_analysis(analysis_type, parameters)
                    await websocket.send(json.dumps({
                        "type": "analysis_result",
                        "analysis_type": analysis_type,
                        "result": result
                    }))
            
            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"未知消息类型: {msg_type}"
                }))
        
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": str(e)
            }))
    
    async def execute_query(self, query: str) -> Dict[str, Any]:
        """执行查询"""
        try:
            with self.driver.session() as session:
                result = session.run(query)
                records = [dict(record) for record in result]
                return {"success": True, "data": records}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_search(self, query: str, search_type: str) -> Dict[str, Any]:
        """执行搜索"""
        try:
            with self.driver.session() as session:
                if search_type == "fuzzy":
                    cypher_query = """
                    MATCH (n)
                    WHERE n.name CONTAINS $query OR n.description CONTAINS $query
                    RETURN n
                    LIMIT 50
                    """
                else:
                    cypher_query = "MATCH (n {name: $query}) RETURN n"
                
                result = session.run(cypher_query, query=query)
                nodes = [dict(record["n"]) for record in result]
                return {"success": True, "data": nodes}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_analysis(self, analysis_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行分析"""
        try:
            with self.driver.session() as session:
                if analysis_type == "centrality":
                    centrality_type = parameters.get("type", "degree")
                    if centrality_type == "degree":
                        query = """
                        MATCH (n)
                        RETURN n.name, size((n)--()) as degree
                        ORDER BY degree DESC
                        LIMIT 20
                        """
                    else:
                        query = f"""
                        CALL gds.{centrality_type}.stream('knowledge-graph')
                        YIELD nodeId, score
                        RETURN gds.util.asNode(nodeId).name as name, score
                        ORDER BY score DESC
                        LIMIT 20
                        """
                
                elif analysis_type == "communities":
                    query = """
                    CALL gds.louvain.stream('knowledge-graph')
                    YIELD nodeId, communityId
                    RETURN communityId, collect(gds.util.asNode(nodeId).name) as members
                    ORDER BY size(collect(gds.util.asNode(nodeId).name)) DESC
                    """
                
                else:
                    return {"success": False, "error": f"未知分析类型: {analysis_type}"}
                
                result = session.run(query)
                data = [dict(record) for record in result]
                return {"success": True, "data": data}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def websocket_handler(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """WebSocket处理器"""
        await self.register(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "无效的JSON格式"
                    }))
        except websockets.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    async def start_server(self, host: str = "localhost", port: int = 8765):
        """启动WebSocket服务器"""
        server = await websockets.serve(
            self.websocket_handler,
            host,
            port
        )
        logger.info(f"WebSocket服务器启动: ws://{host}:{port}")
        
        # 启动定期广播任务
        asyncio.create_task(self.periodic_broadcast())
        
        await server.wait_closed()
    
    async def periodic_broadcast(self):
        """定期广播任务"""
        while True:
            try:
                # 广播系统状态
                status_message = {
                    "type": "system_status",
                    "timestamp": asyncio.get_event_loop().time(),
                    "clients_count": len(self.clients),
                    "subscriptions_count": len(self.subscriptions)
                }
                await self.broadcast(status_message)
                
                await asyncio.sleep(30)  # 每30秒广播一次
            
            except Exception as e:
                logger.error(f"定期广播失败: {e}")
                await asyncio.sleep(5)

# 使用示例
async def start_websocket_service():
    """启动WebSocket服务"""
    from neo4j import GraphDatabase
    
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    service = WebSocketService(driver)
    
    await service.start_server()
```

## 4. API文档和测试

### API文档生成

```python
# API文档生成器
from fastapi.openapi.utils import get_openapi
import yaml

class APIDocumentationGenerator:
    """API文档生成器"""
    
    def __init__(self, app: FastAPI):
        self.app = app
    
    def generate_openapi_schema(self) -> Dict[str, Any]:
        """生成OpenAPI Schema"""
        return get_openapi(
            title=self.app.title,
            version=self.app.version,
            description=self.app.description,
            routes=self.app.routes,
        )
    
    def export_openapi_json(self, filepath: str):
        """导出OpenAPI JSON"""
        schema = self.generate_openapi_schema()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
    
    def export_openapi_yaml(self, filepath: str):
        """导出OpenAPI YAML"""
        schema = self.generate_openapi_schema()
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(schema, f, default_flow_style=False, allow_unicode=True)
    
    def generate_postman_collection(self, filepath: str):
        """生成Postman集合"""
        schema = self.generate_openapi_schema()
        
        collection = {
            "info": {
                "name": "知识图谱API",
                "description": "数据科学知识图谱API集合",
                "version": "1.0.0"
            },
            "item": []
        }
        
        for path, methods in schema["paths"].items():
            for method, operation in methods.items():
                item = {
                    "name": operation.get("summary", f"{method.upper()} {path}"),
                    "request": {
                        "method": method.upper(),
                        "header": [],
                        "url": {
                            "raw": f"{{base_url}}{path}",
                            "host": ["{{base_url}}"],
                            "path": path.strip("/").split("/")
                        }
                    }
                }
                
                # 添加参数
                if "parameters" in operation:
                    item["request"]["url"]["query"] = []
                    for param in operation["parameters"]:
                        if param["in"] == "query":
                            item["request"]["url"]["query"].append({
                                "key": param["name"],
                                "value": "",
                                "description": param.get("description", "")
                            })
                
                collection["item"].append(item)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(collection, f, ensure_ascii=False, indent=2)
```

### API测试工具

```python
# API测试工具
import pytest
from httpx import AsyncClient
import asyncio

class APITestSuite:
    """API测试套件"""
    
    def __init__(self, app: FastAPI):
        self.app = app
    
    async def test_get_nodes(self):
        """测试获取节点"""
        async with AsyncClient(app=self.app, base_url="http://test") as ac:
            response = await ac.get("/api/nodes")
            assert response.status_code == 200
            data = response.json()
            assert "nodes" in data
            assert "count" in data
    
    async def test_get_node(self):
        """测试获取单个节点"""
        async with AsyncClient(app=self.app, base_url="http://test") as ac:
            # 先获取一个节点ID
            nodes_response = await ac.get("/api/nodes?limit=1")
            nodes_data = nodes_response.json()
            
            if nodes_data["nodes"]:
                node_id = nodes_data["nodes"][0]["id"]
                response = await ac.get(f"/api/nodes/{node_id}")
                assert response.status_code == 200
                data = response.json()
                assert "node" in data
                assert data["node"]["id"] == node_id
    
    async def test_search_nodes(self):
        """测试搜索节点"""
        async with AsyncClient(app=self.app, base_url="http://test") as ac:
            response = await ac.get("/api/search?query=机器学习")
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert "count" in data
    
    async def test_centrality_analysis(self):
        """测试中心性分析"""
        async with AsyncClient(app=self.app, base_url="http://test") as ac:
            response = await ac.get("/api/analysis/centrality?centrality_type=degree")
            assert response.status_code == 200
            data = response.json()
            assert "centrality" in data
            assert "type" in data
    
    async def test_community_analysis(self):
        """测试社区分析"""
        async with AsyncClient(app=self.app, base_url="http://test") as ac:
            response = await ac.get("/api/analysis/communities")
            assert response.status_code == 200
            data = response.json()
            assert "communities" in data
            assert "count" in data
    
    async def run_all_tests(self):
        """运行所有测试"""
        tests = [
            self.test_get_nodes,
            self.test_get_node,
            self.test_search_nodes,
            self.test_centrality_analysis,
            self.test_community_analysis
        ]
        
        results = []
        for test in tests:
            try:
                await test()
                results.append({"test": test.__name__, "status": "PASS"})
            except Exception as e:
                results.append({"test": test.__name__, "status": "FAIL", "error": str(e)})
        
        return results

# 使用示例
async def run_api_tests():
    """运行API测试"""
    api = KnowledgeGraphAPI(
        neo4j_uri="bolt://localhost:7687",
        username="neo4j",
        password="password"
    )
    
    test_suite = APITestSuite(api.app)
    results = await test_suite.run_all_tests()
    
    for result in results:
        print(f"{result['test']}: {result['status']}")
        if result['status'] == 'FAIL':
            print(f"  错误: {result['error']}")
```

## 5. 工具与平台

### API工具

1. **FastAPI**：现代Python Web框架
2. **GraphQL**：查询语言和运行时
3. **WebSocket**：实时通信协议
4. **Postman**：API测试工具

### 文档工具

1. **Swagger UI**：交互式API文档
2. **ReDoc**：API文档生成器
3. **OpenAPI**：API规范标准
4. **Postman**：API集合管理

### 测试工具

1. **pytest**：Python测试框架
2. **httpx**：异步HTTP客户端
3. **pytest-asyncio**：异步测试支持
4. **coverage**：代码覆盖率工具

## 6. 最佳实践

### API设计

1. **RESTful原则**：遵循REST架构风格
2. **版本控制**：API版本管理
3. **错误处理**：统一的错误响应格式
4. **文档完整**：详细的API文档

### 性能优化

1. **缓存策略**：Redis缓存
2. **分页处理**：大数据集分页
3. **异步处理**：非阻塞操作
4. **连接池**：数据库连接管理

### 安全考虑

1. **认证授权**：JWT令牌
2. **输入验证**：参数验证
3. **SQL注入防护**：参数化查询
4. **CORS配置**：跨域请求处理
