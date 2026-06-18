import asyncio
from typing import AsyncGenerator, Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from src.db.vector_store import vector_store
from src.db.neo4j_client import neo4j_client
from src.core.config import settings
from src.core.logger import get_logger
from src.core.exceptions import LLMTimeoutError, IntentParsingError

logger = get_logger(__name__)

class SemanticRouter:
    def __init__(self):
        self.router_llm = ChatOpenAI(
            model_name="gpt-4o",
            temperature=0.0,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.intent_prompt = PromptTemplate(
            input_variables=["query"],
            template="""Analyze the user query: '{query}'. 
Classify the intent as one of the following exact strings:
- FACTUAL_RETRIEVAL: Query asks for specific facts or document quotes.
- RELATIONAL_SYNTHESIS: Query asks about relationships, concepts, architectures, or 'how X relates to Y'.
- GENERAL_CHAT: Query is conversational (e.g. hello, thanks).

Output ONLY the exact string intent."""
        )

    async def route_query(self, query: str) -> str:
        prompt = self.intent_prompt.format(query=query)
        try:
            response = await self.router_llm.ainvoke([HumanMessage(content=prompt)])
            intent = response.content.strip().upper()
            if intent not in ["FACTUAL_RETRIEVAL", "RELATIONAL_SYNTHESIS", "GENERAL_CHAT"]:
                raise IntentParsingError(f"Unknown intent returned: {intent}")
            logger.info("Query routed", extra={"query": query, "intent": intent})
            return intent
        except Exception as e:
            logger.error("Routing failed, defaulting to RELATIONAL_SYNTHESIS", exc_info=True)
            return "RELATIONAL_SYNTHESIS"

class AsyncHybridRAGAgent:
    def __init__(self):
        self.router = SemanticRouter()
        self.generation_llm = ChatOpenAI(
            model_name="gpt-4-turbo",
            temperature=0.3,
            streaming=True,
            openai_api_key=settings.OPENAI_API_KEY
        )

    async def _gather_context(self, query: str, intent: str, target_concept: str) -> Dict[str, Any]:
        context = {"semantic": [], "graph": []}
        
        async def fetch_semantic():
            docs = await vector_store.async_hybrid_search(query, k=5)
            context["semantic"] = [d.page_content for d in docs]
            
        async def fetch_graph():
            if target_concept:
                subgraph = await neo4j_client.extract_subgraph(target_concept, depth=2)
                context["graph"] = subgraph.get("nodes", [])
                
        tasks = []
        if intent in ["FACTUAL_RETRIEVAL", "RELATIONAL_SYNTHESIS"]:
            tasks.append(fetch_semantic())
        if intent == "RELATIONAL_SYNTHESIS" and target_concept:
            tasks.append(fetch_graph())
            
        if tasks:
            await asyncio.gather(*tasks)
            
        return context

    async def stream_answer(self, query: str, target_concept: str) -> AsyncGenerator[str, None]:
        intent = await self.router.route_query(query)
        
        context = await self._gather_context(query, intent, target_concept)
        
        system_prompt = f"""You are Luminal AI, a highly advanced interactive learning assistant.
Intent detected: {intent}
Semantic Context: {' | '.join(context['semantic']) if context['semantic'] else 'None'}
Graph Context: {', '.join([n.get('name', '') for n in context['graph']]) if context['graph'] else 'None'}

Synthesize the context to provide a deeply reasoned, accurate answer. If no context is provided, rely on your general knowledge but admit that it is outside the ingested database."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]
        
        try:
            async for chunk in self.generation_llm.astream(messages):
                if chunk.content:
                    yield chunk.content
        except asyncio.TimeoutError as e:
            raise LLMTimeoutError() from e
        except Exception as e:
            logger.error("Error during LLM streaming", exc_info=True)
            yield f"\n[Error: Connection interrupted. {str(e)}]"

rag_agent = AsyncHybridRAGAgent()
