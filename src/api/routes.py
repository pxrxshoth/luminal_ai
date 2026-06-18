import asyncio
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.postgres import get_db, InteractionLog
from src.services.rag import rag_agent
from src.services.evaluation import gap_detector
from src.services.ingestion import ingestion_queue
from src.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

class QueryRequest(BaseModel):
    question: str
    target_concept: str = ""

class IngestionRequest(BaseModel):
    document_id: str
    text: str
    relations: List[Dict[str, Any]] = []

class EvaluationRequest(BaseModel):
    interaction_history: List[Dict[str, str]]
    current_topic: str

@router.post("/query/stream")
async def stream_question(request: Request, payload: QueryRequest, db: Session = Depends(get_db)):
    logger.info("Received streaming query request", extra={"query": payload.question})
    
    async def event_generator():
        full_response = []
        try:
            async for chunk in rag_agent.stream_answer(payload.question, payload.target_concept):
                if await request.is_disconnected():
                    logger.warning("Client disconnected during stream")
                    break
                full_response.append(chunk)
                yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.error("Streaming error", exc_info=True)
            yield f"data: [Error: {str(e)}]\n\n"
        finally:
            if full_response:
                complete_text = "".join(full_response)
                log_entry = InteractionLog(
                    user_query=payload.question,
                    system_response=complete_text,
                    intent="unknown"
                )
                db.add(log_entry)
                db.commit()
                logger.info("Stream completed and logged")
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/evaluate")
async def evaluate_understanding(payload: EvaluationRequest):
    question = await gap_detector.async_generate_targeted_question(
        payload.interaction_history, 
        payload.current_topic
    )
    return {"targeted_question": question}

@router.post("/ingest")
async def ingest_data(payload: IngestionRequest, background_tasks: BackgroundTasks):
    await ingestion_queue.enqueue_document(
        payload.document_id,
        payload.text,
        payload.relations
    )
    return {"status": "accepted", "message": "Document queued for background processing."}
