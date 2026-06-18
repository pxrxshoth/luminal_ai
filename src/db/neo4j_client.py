import asyncio
from neo4j import AsyncGraphDatabase, AsyncSession
from neo4j.exceptions import ServiceUnavailable, CypherSyntaxError
from typing import List, Dict, Any, Optional
from src.core.config import settings
from src.core.logger import get_logger
from src.core.exceptions import GraphTraversalError

logger = get_logger(__name__)

class Neo4jAsyncClient:
    def __init__(self):
        self._driver = None

    async def connect(self):
        try:
            self._driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_timeout=10.0
            )
            await self._driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j Async Driver")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise

    async def close(self):
        if self._driver:
            await self._driver.close()
            logger.info("Neo4j connection closed")

    async def async_session(self) -> AsyncSession:
        if not self._driver:
            await self.connect()
        return self._driver.session()

    async def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        parameters = parameters or {}
        try:
            async with await self.async_session() as session:
                result = await session.run(query, parameters)
                records = await result.data()
                return records
        except ServiceUnavailable as e:
            logger.error("Neo4j service is unavailable during query execution", exc_info=True)
            raise GraphTraversalError("Neo4j service unavailable") from e
        except CypherSyntaxError as e:
            logger.error(f"Cypher Syntax Error: {str(e)}")
            raise GraphTraversalError("Invalid Cypher syntax") from e
        except Exception as e:
            logger.error(f"Unexpected error executing Cypher query: {str(e)}", exc_info=True)
            raise GraphTraversalError(f"Query execution failed: {str(e)}") from e

    async def extract_subgraph(self, root_concept: str, depth: int = 2, max_nodes: int = 50) -> Dict[str, Any]:
        query = """
        MATCH path = (root:Concept {name: $root_concept})-[*1..%d]-(related:Concept)
        WITH path, nodes(path) AS ns, relationships(path) AS rs
        UNWIND ns AS n
        UNWIND rs AS r
        RETURN collect(DISTINCT n) AS nodes, collect(DISTINCT r) AS edges
        LIMIT $max_nodes
        """ % depth
        
        start_time = asyncio.get_event_loop().time()
        try:
            records = await self.execute_query(query, {"root_concept": root_concept, "max_nodes": max_nodes})
            latency = (asyncio.get_event_loop().time() - start_time) * 1000
            
            if not records:
                return {"nodes": [], "edges": []}
                
            nodes = [{"id": n.element_id, "name": n.get("name"), "labels": list(n.labels)} for n in records[0].get("nodes", [])]
            edges = [{"id": r.element_id, "source": r.start_node.element_id, "target": r.end_node.element_id, "type": r.type} for r in records[0].get("edges", [])]
            
            logger.info("Extracted subgraph", extra={"root_concept": root_concept, "nodes_count": len(nodes), "latency_ms": latency})
            return {"nodes": nodes, "edges": edges}
            
        except Exception as e:
            logger.error(f"Failed to extract subgraph for {root_concept}")
            raise GraphTraversalError("Sub-graph extraction failed") from e

    async def batch_merge_entities(self, entities: List[Dict[str, Any]], relations: List[Dict[str, Any]]):
        entity_query = """
        UNWIND $entities AS entity
        MERGE (n:Concept {name: entity.name})
        SET n += entity.properties
        """
        
        relation_query = """
        UNWIND $relations AS rel
        MATCH (source:Concept {name: rel.source_name})
        MATCH (target:Concept {name: rel.target_name})
        CALL apoc.create.relationship(source, rel.type, rel.properties, target) YIELD rel AS r
        RETURN count(r)
        """
        
        try:
            async with await self.async_session() as session:
                tx = await session.begin_transaction()
                await tx.run(entity_query, {"entities": entities})
                if relations:
                    await tx.run(relation_query, {"relations": relations})
                await tx.commit()
                logger.info(f"Successfully batch merged {len(entities)} entities and {len(relations)} relationships")
        except Exception as e:
            logger.error("Failed batch merge operation", exc_info=True)
            raise GraphTraversalError("Batch merge failed") from e

neo4j_client = Neo4jAsyncClient()
