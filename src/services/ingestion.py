import asyncio
import re
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.db.vector_store import vector_store
from src.db.neo4j_client import neo4j_client
from src.core.logger import get_logger

logger = get_logger(__name__)

class AsyncIngestionQueue:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=250,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        self._queue = asyncio.Queue(maxsize=100)
        self._workers = []

    async def start_workers(self, num_workers: int = 3):
        for i in range(num_workers):
            task = asyncio.create_task(self._worker_loop(i))
            self._workers.append(task)
        logger.info(f"Started {num_workers} ingestion background workers")

    async def stop_workers(self):
        for task in self._workers:
            task.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)

    def _extract_pseudo_entities(self, text: str) -> List[Dict[str, Any]]:
        words = set(re.findall(r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)*\b', text))
        words = {w for w in words if len(w) > 3}
        entities = [{"name": w, "properties": {"type": "ExtractedEntity"}} for w in words]
        return entities

    async def _worker_loop(self, worker_id: int):
        while True:
            try:
                task_payload = await self._queue.get()
                document_id = task_payload.get("document_id")
                raw_text = task_payload.get("text", "")
                explicit_relations = task_payload.get("relations", [])
                
                logger.info(f"Worker {worker_id} processing document {document_id}")
                
                chunks = self.text_splitter.split_text(raw_text)
                docs = [Document(page_content=chunk, metadata={"document_id": document_id, "chunk_idx": i}) for i, chunk in enumerate(chunks)]
                
                await vector_store.async_add_documents(docs)
                
                entities = self._extract_pseudo_entities(raw_text)
                
                if explicit_relations:
                    formatted_relations = [
                        {"source_name": r["source"], "target_name": r["target"], "type": r.get("type", "RELATES_TO"), "properties": {}}
                        for r in explicit_relations
                    ]
                    
                    sources = [{"name": r["source"], "properties": {"type": "Concept"}} for r in explicit_relations]
                    targets = [{"name": r["target"], "properties": {"type": "Concept"}} for r in explicit_relations]
                    entities.extend(sources + targets)
                    
                    unique_entities = {e["name"]: e for e in entities}.values()
                    await neo4j_client.batch_merge_entities(list(unique_entities), formatted_relations)
                
                logger.info(f"Worker {worker_id} finished processing {document_id}")
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} encountered an error", exc_info=True)

    async def enqueue_document(self, document_id: str, text: str, relations: List[Dict[str, Any]]):
        await self._queue.put({
            "document_id": document_id,
            "text": text,
            "relations": relations
        })
        logger.info(f"Enqueued document {document_id} for background processing")

ingestion_queue = AsyncIngestionQueue()
