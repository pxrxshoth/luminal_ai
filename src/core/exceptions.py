class LuminalError(Exception):
    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

class GraphTraversalError(LuminalError):
    def __init__(self, message: str = "Failed to traverse the knowledge graph."):
        super().__init__(message, status_code=500, error_code="GRAPH_TRAVERSAL_ERROR")

class LLMTimeoutError(LuminalError):
    def __init__(self, message: str = "Language model generation timed out."):
        super().__init__(message, status_code=504, error_code="LLM_TIMEOUT")

class VectorStoreSyncError(LuminalError):
    def __init__(self, message: str = "Vector index synchronization failed."):
        super().__init__(message, status_code=500, error_code="VECTOR_SYNC_ERROR")

class IntentParsingError(LuminalError):
    def __init__(self, message: str = "Could not confidently parse the user intent."):
        super().__init__(message, status_code=400, error_code="INTENT_PARSING_ERROR")
