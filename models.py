from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any, List
from datetime import datetime

class CreateUserRequest(BaseModel):
    """Request model for creating a new user"""
    username: str = Field(..., min_length=3, max_length=50, description="Username must be between 3 and 50 characters")
    email: EmailStr = Field(..., description="Valid email address")
    steam_id: Optional[str] = Field(None, max_length=100, description="Steam ID (optional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "gamer123",
                "email": "gamer123@example.com",
                "steam_id": "76561198000000000"
            }
        }

class User(BaseModel):
    """User model"""
    id: int
    username: str
    email: str
    steam_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "gamer123",
                "email": "gamer123@example.com",
                "steam_id": "76561198000000000",
                "created_at": "2025-01-27T10:30:00Z",
                "updated_at": "2025-01-27T10:30:00Z"
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