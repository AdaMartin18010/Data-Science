-- 图与递归示例

-- AGE Cypher
CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';
SELECT * FROM create_graph('g');

SELECT * FROM cypher('g', $$
  CREATE (a:User {id:1})-[:FOLLOWS]->(b:User {id:2})
$$) as (v agtype);

SELECT * FROM cypher('g', $$
  MATCH (a:User {id:1})-[:FOLLOWS*1..3]->(x)
  RETURN x LIMIT 10
$$) as (x agtype);

-- 递归CTE
WITH RECURSIVE reach(id, depth, path) AS (
  SELECT 1, 0, ARRAY[1]
  UNION ALL
  SELECT e.dst, r.depth + 1, r.path || e.dst
  FROM reach r
  JOIN edges e ON e.src = r.id
  WHERE r.depth < 3 AND NOT e.dst = ANY(r.path)
)
SELECT * FROM reach;


