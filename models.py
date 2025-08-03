from pydantic import BaseModel, Field
from typing import Optional, Any, List
from datetime import datetime

class AppFile(BaseModel):
    """App file model for listing files"""
    id: str = Field(..., description="File ID (UUID)")
    app_id: str = Field(..., description="App ID this file belongs to")
    filename: str = Field(..., description="Name of the file")
    file_type: str = Field(..., description="Type of file (json, lua, manifest, vdf)")
    size: int = Field(..., description="File size in bytes")
    uploaded_at: str = Field(..., description="Upload timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "5d1fcc24-ce86-4600-9494-81c10fa4d6bf",
                "app_id": "1245623",
                "filename": "appinfo.json",
                "file_type": "json",
                "size": 2048,
                "uploaded_at": "2025-08-02T17:13:33.110Z"
            }
        }

class FileInfo(BaseModel):
    """File information model"""
    filename: str = Field(..., description="Name of the file")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type of the file")
    upload_date: datetime = Field(..., description="Date when file was uploaded")
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "document.pdf",
                "size": 1024000,
                "content_type": "application/pdf",
                "upload_date": "2025-08-02T17:13:33.110Z"
            }
        }

class FileUploadResponse(BaseModel):
    """File upload response model"""
    success: bool = Field(..., description="Whether the upload was successful")
    message: str = Field(..., description="Response message")
    file_info: Optional[FileInfo] = Field(None, description="Uploaded file information")
    file_id: Optional[str] = Field(None, description="Unique identifier for the uploaded file")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "File uploaded successfully",
                "file_info": {
                    "filename": "document.pdf",
                    "size": 1024000,
                    "content_type": "application/pdf",
                    "upload_date": "2025-08-02T17:13:33.110Z"
                },
                "file_id": "file_123456"
            }
        }

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