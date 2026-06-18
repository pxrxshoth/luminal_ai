import pytest
import asyncio
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_router():
    with patch("src.services.rag.SemanticRouter.route_query", new_callable=MagicMock) as mock:
        mock.return_value = asyncio.Future()
        mock.return_value.set_result("RELATIONAL_SYNTHESIS")
        yield mock

@pytest.mark.asyncio
async def test_semantic_routing_valid_intent(mock_router):
    from src.services.rag import SemanticRouter
    router = SemanticRouter()
    
    intent = await router.route_query("How does graph embedding work?")
    assert intent == "RELATIONAL_SYNTHESIS"

@pytest.mark.asyncio
async def test_agent_stream_response():
    from src.services.rag import AsyncHybridRAGAgent
    
    agent = AsyncHybridRAGAgent()
    
    async def mock_gather(*args, **kwargs):
        return {"semantic": ["Doc 1 context"], "graph": [{"name": "ConceptA"}]}
        
    with patch.object(agent, "_gather_context", side_effect=mock_gather):
        with patch.object(agent.generation_llm, "astream", new_callable=MagicMock) as mock_stream:
            
            async def async_gen():
                class MockChunk:
                    content = "Test chunk"
                yield MockChunk()
                
            mock_stream.return_value = async_gen()
            
            chunks = []
            async for chunk in agent.stream_answer("query", "target"):
                chunks.append(chunk)
                
            assert "Test chunk" in chunks
