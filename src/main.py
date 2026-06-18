from fastapi import FastAPI
from src.api.routes import router
from src.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent RAG & Graph-Based Learning System",
    version="1.0.0"
)

app.include_router(router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "healthy"}