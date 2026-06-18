from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.db.postgres import get_db, InteractionLog
from src.services.rag import HybridRAG
from src.services.evaluation import GapDetectionEngine
from src.services.ingestion import IngestionPipeline

router = APIRouter()
rag_system = HybridRAG()
gap_engine = GapDetectionEngine()
ingestion_pipeline = IngestionPipeline()

class QueryRequest(BaseModel):
    question: str
    target_concept: str

class IngestionRequest(BaseModel):
    text: str
    relations: list[dict]

@router.post("/query")
def ask_question(request: QueryRequest, db: Session = Depends(get_db)):
    answer = rag_system.answer_question(request.question, request.target_concept)
    
    log_entry = InteractionLog(
        user_query=request.question,
        system_response=answer,
        intent="query"
    )
    db.add(log_entry)
    db.commit()
    
    return {"answer": answer}

@router.post("/evaluate")
def evaluate_understanding(history: str, topic: str):
    question = gap_engine.generate_targeted_question(history, topic)
    return {"targeted_question": question}

@router.post("/ingest")
def ingest_data(request: IngestionRequest):
    ingestion_pipeline.process_document(request.text, request.relations)
    return {"status": "success"}
