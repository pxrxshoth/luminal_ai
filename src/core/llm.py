from langchain_openai import ChatOpenAI
from src.core.config import settings

def get_llm():
    return ChatOpenAI(
        model_name="gpt-4-turbo",
        temperature=0.2,
        openai_api_key=settings.OPENAI_API_KEY
    )
