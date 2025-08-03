from pydantic import BaseModel, Field
from typing import Optional, Any, List
from datetime import datetime

class App(BaseModel):
    """App model"""
    app_id: str
    name: Optional[str] = None
    type: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "app_id": "1245623",
                "name": "ELDEN RING",
                "type": "Game",
                "created_at": "2025-08-02T17:13:33.110Z",
                "updated_at": "2025-08-02T17:13:37.782Z"
            }
        }

class ApiResponse(BaseModel):
    """Standard API response model"""
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {"key": "value"}
            }
        }

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Any] = Field(None, description="Additional error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "An error occurred",
                "error_code": "VALIDATION_ERROR",
                "details": {"field": "username", "issue": "already exists"}
            }
        }