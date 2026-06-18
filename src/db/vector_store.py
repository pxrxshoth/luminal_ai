from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from src.core.config import settings

class VectorStoreManager:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        self.index = None

    def initialize_index(self, texts):
        self.index = FAISS.from_texts(texts, self.embeddings)

    def add_texts(self, texts):
        if self.index is None:
            self.initialize_index(texts)
        else:
            self.index.add_texts(texts)

    def search(self, query: str, k: int = 3):
        if self.index is None:
            return []
        return self.index.similarity_search(query, k=k)

vector_store = VectorStoreManager()
