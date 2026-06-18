from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.db.vector_store import vector_store
from src.db.neo4j_client import neo4j_client

class IngestionPipeline:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )

    def process_document(self, text: str, concepts_relations: list):
        chunks = self.text_splitter.split_text(text)
        vector_store.add_texts(chunks)
        
        for relation in concepts_relations:
            neo4j_client.create_concept_relationship(
                relation["source"],
                relation["target"],
                relation["type"]
            )
