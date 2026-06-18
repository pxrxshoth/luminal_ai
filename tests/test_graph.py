import pytest
import asyncio
from unittest.mock import patch, MagicMock
from src.core.exceptions import GraphTraversalError

@pytest.fixture
def mock_neo4j_session():
    with patch("src.db.neo4j_client.Neo4jAsyncClient.async_session") as mock_session:
        yield mock_session

@pytest.mark.asyncio
async def test_extract_subgraph_success(mock_neo4j_session):
    from src.db.neo4j_client import Neo4jAsyncClient
    
    client = Neo4jAsyncClient()
    
    async def mock_execute(*args, **kwargs):
        class MockRecord:
            def __init__(self, data_dict):
                self._data = data_dict
            def get(self, key, default=None):
                return self._data.get(key, default)
        
        class MockNode:
            element_id = "123"
            labels = ["Concept"]
            def get(self, key):
                return "AI"
                
        return [MockRecord({"nodes": [MockNode()], "edges": []})]
        
    with patch.object(client, "execute_query", side_effect=mock_execute):
        result = await client.extract_subgraph("AI", depth=1)
        assert len(result["nodes"]) == 1
        assert result["nodes"][0]["name"] == "AI"

@pytest.mark.asyncio
async def test_extract_subgraph_failure():
    from src.db.neo4j_client import Neo4jAsyncClient
    
    client = Neo4jAsyncClient()
    
    async def mock_execute_fail(*args, **kwargs):
        raise Exception("DB Connection Refused")
        
    with patch.object(client, "execute_query", side_effect=mock_execute_fail):
        with pytest.raises(GraphTraversalError):
            await client.extract_subgraph("AI", depth=1)
