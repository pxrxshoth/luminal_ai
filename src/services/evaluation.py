from src.core.llm import get_llm
from langchain.prompts import PromptTemplate

class GapDetectionEngine:
    def __init__(self):
        self.llm = get_llm()
        self.eval_prompt = PromptTemplate(
            input_variables=["user_history", "current_topic"],
            template="History: {user_history}\nTopic: {current_topic}\nIdentify knowledge gaps and generate a targeted question to test understanding."
        )

    def generate_targeted_question(self, user_history: str, current_topic: str):
        prompt = self.eval_prompt.format(
            user_history=user_history,
            current_topic=current_topic
        )
        response = self.llm.invoke(prompt)
        return response.content
