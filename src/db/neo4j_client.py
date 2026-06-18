from neo4j import GraphDatabase
from src.core.config import settings

class Neo4jClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def create_concept_relationship(self, concept_a: str, concept_b: str, relation: str):
        query = (
            "MERGE (a:Concept {name: $concept_a}) "
            "MERGE (b:Concept {name: $concept_b}) "
            "MERGE (a)-[r:RELATION {type: $relation}]->(b)"
        )
        with self.driver.session() as session:
            session.run(query, concept_a=concept_a, concept_b=concept_b, relation=relation)

    def get_related_concepts(self, concept: str):
        query = (
            "MATCH (a:Concept {name: $concept})-[:RELATION]->(b:Concept) "
            "RETURN b.name AS related_concept"
        )
        with self.driver.session() as session:
            result = session.run(query, concept=concept)
            return [record["related_concept"] for record in result]

neo4j_client = Neo4jClient()
