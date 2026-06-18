import uuid
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.routes import router
from src.core.config import settings
from src.core.logger import get_logger
from src.core.exceptions import LuminalError
from src.services.ingestion import ingestion_queue
from src.db.neo4j_client import neo4j_client

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Luminal AI microservices...")
    await neo4j_client.connect()
    await ingestion_queue.start_workers(num_workers=3)
    yield
    logger.info("Shutting down Luminal AI microservices...")
    await ingestion_queue.stop_workers()
    await neo4j_client.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent RAG & Graph-Based Learning System - Enterprise Edition",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()
        
        try:
            response = await call_next(request)
            latency = (time.time() - start_time) * 1000
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "latency_ms": latency
                }
            )
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            logger.error(
                "Unhandled exception during request",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "latency_ms": latency
                }
            )
            raise

app.add_middleware(RequestLoggingMiddleware)

@app.exception_handler(LuminalError)
async def luminal_error_handler(request: Request, exc: LuminalError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.error_code, "message": exc.message}},
    )

app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}