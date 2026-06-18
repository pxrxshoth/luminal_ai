from typing import List, Dict
import asyncio
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)

class ActiveGapDetector:
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.5,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.eval_prompt = PromptTemplate(
            input_variables=["interaction_log", "current_topic"],
            template="""Analyze the following recent interaction history of the user concerning the topic '{current_topic}'.
            
Interaction History:
{interaction_log}

Based on this history, identify a subtle knowledge gap or a conceptual leap the user might have missed. 
Formulate a single, highly targeted Socratic question to challenge their understanding.
Do not provide the answer. ONLY output the question.
"""
        )

    async def async_generate_targeted_question(self, interaction_history: List[Dict[str, str]], current_topic: str) -> str:
        history_text = "\n".join([f"User: {entry['user']}\nSystem: {entry['system']}" for entry in interaction_history[-3:]])
        
        prompt = self.eval_prompt.format(
            interaction_log=history_text,
            current_topic=current_topic
        )
        
        try:
            logger.info("Generating targeted gap-detection question", extra={"topic": current_topic})
            response = await self.llm.ainvoke(prompt)
            return response.content.strip()
        except Exception as e:
            logger.error("Failed to generate targeted question", exc_info=True)
            return "Could you explain the relationship between these core concepts in your own words?"

gap_detector = ActiveGapDetector()
