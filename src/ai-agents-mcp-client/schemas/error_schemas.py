from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime

class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    MCP_CONNECTION_ERROR = "MCP_CONNECTION_ERROR"
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"
    VECTOR_DB_ERROR = "VECTOR_DB_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str
    error_code: str

class StandardErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    errors: Optional[List[ErrorDetail]] = None
    timestamp: str = None
    request_id: Optional[str] = None
    
    def __init__(self, **kwargs):
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.utcnow().isoformat()
        super().__init__(**kwargs)

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = None
    request_id: Optional[str] = None
    
    def __init__(self, **kwargs):
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.utcnow().isoformat()
        super().__init__(**kwargs)