from src.db.vector_store import vector_store
from src.db.neo4j_client import neo4j_client
from src.core.llm import get_llm
from langchain.prompts import PromptTemplate

class HybridRAG:
    def __init__(self):
        self.llm = get_llm()
        self.prompt = PromptTemplate(
            input_variables=["context", "graph_context", "question"],
            template="Context: {context}\nGraph Context: {graph_context}\nQuestion: {question}\nAnswer:"
        )

    def answer_question(self, question: str, target_concept: str):
        semantic_results = vector_store.search(question)
        context = " ".join([doc.page_content for doc in semantic_results])
        
        related_concepts = neo4j_client.get_related_concepts(target_concept)
        graph_context = ", ".join(related_concepts)
        
        formatted_prompt = self.prompt.format(
            context=context,
            graph_context=graph_context,
            question=question
        )
        
        response = self.llm.invoke(formatted_prompt)
        return response.content
