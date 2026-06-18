import asyncio
import json
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import FAISS
from langchain_openai import AsyncOpenAIEmbeddings
from langchain_core.documents import Document
from src.core.config import settings
from src.core.logger import get_logger
from src.core.exceptions import VectorStoreSyncError

logger = get_logger(__name__)

class AsyncVectorStoreManager:
    def __init__(self):
        self.embeddings = AsyncOpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-large",
            max_retries=3,
            request_timeout=15.0
        )
        self._index: Optional[FAISS] = None
        self._lock = asyncio.Lock()

    async def _initialize_index(self, documents: List[Document]):
        try:
            self._index = await FAISS.afrom_documents(documents, self.embeddings)
            logger.info("Initialized FAISS vector index", extra={"document_count": len(documents)})
        except Exception as e:
            logger.error("Failed to initialize FAISS index", exc_info=True)
            raise VectorStoreSyncError("Index initialization failed") from e

    async def async_add_documents(self, documents: List[Document]):
        async with self._lock:
            if self._index is None:
                await self._initialize_index(documents)
            else:
                try:
                    await self._index.aadd_documents(documents)
                    logger.info(f"Appended {len(documents)} documents to FAISS index")
                except Exception as e:
                    logger.error("Failed to append documents to FAISS", exc_info=True)
                    raise VectorStoreSyncError("Index append failed") from e

    async def async_similarity_search(self, query: str, k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        if self._index is None:
            logger.warning("Attempted to search an uninitialized vector index")
            return []
            
        start_time = asyncio.get_event_loop().time()
        try:
            results = await self._index.asimilarity_search(query, k=k, filter=filter_metadata)
            latency = (asyncio.get_event_loop().time() - start_time) * 1000
            
            logger.info("Executed vector search", extra={"query": query, "k": k, "results_count": len(results), "latency_ms": latency})
            return results
        except Exception as e:
            logger.error(f"Vector search failed for query: {query}", exc_info=True)
            raise VectorStoreSyncError("Search execution failed") from e

    async def async_hybrid_search(self, query: str, k: int = 5) -> List[Document]:
        dense_results = await self.async_similarity_search(query, k=k * 2)
        
        def keyword_score(doc: Document) -> float:
            content_lower = doc.page_content.lower()
            query_terms = query.lower().split()
            return sum(1 for term in query_terms if term in content_lower) / len(query_terms)

        scored_docs = [(doc, keyword_score(doc)) for doc in dense_results]
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in scored_docs[:k]]

vector_store = AsyncVectorStoreManager()
