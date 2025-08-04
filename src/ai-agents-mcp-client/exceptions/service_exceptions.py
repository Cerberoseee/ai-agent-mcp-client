from typing import Optional, Dict, Any

class ServiceError(Exception):
    """Base exception for service errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}

class AIServiceError(ServiceError):
    """Raised when AI service calls fail"""
    pass

class MCPConnectionError(ServiceError):
    """Raised when MCP connection fails"""
    pass

class ConfigurationError(ServiceError):
    """Raised when configuration is invalid"""
    pass

class ValidationError(ServiceError):
    """Raised when input validation fails"""
    pass

class TimeoutError(ServiceError):
    """Raised when operations timeout"""
    pass

class VectorDatabaseError(ServiceError):
    """Raised when vector database operations fail"""
    pass