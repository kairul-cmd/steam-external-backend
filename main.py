from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import os
import asyncio
import httpx
import zipfile
import io
from datetime import datetime
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from database import DatabaseManager
from models import App, ApiResponse, AppFile
from typing import List

# Load environment variables
load_dotenv()

# Global database manager instance
db_manager = DatabaseManager()

# Keep-alive task to prevent Render free tier sleep
async def keep_alive_task():
    """Background task to ping the server every 10 minutes to prevent sleep"""
    while True:
        try:
            await asyncio.sleep(600)  # Wait 10 minutes
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/ping", timeout=10.0)
                print(f"Keep-alive ping: {response.status_code} at {datetime.now()}")
        except Exception as e:
            print(f"Keep-alive ping failed: {e}")
            # Continue the loop even if ping fails

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db_manager.initialize()
    # Start keep-alive task
    keep_alive_task_handle = asyncio.create_task(keep_alive_task())
    yield
    # Shutdown
    keep_alive_task_handle.cancel()
    await db_manager.close()

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Steam External Backend API",
    description="FastAPI backend for Steam apps data connected to Turso database",
    version="1.0.0",
    lifespan=lifespan
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# FastAPI app already created above with rate limiter

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=ApiResponse)
async def root():
    """Root endpoint"""
    return ApiResponse(
        success=True,
        message="Steam External Backend API is running!",
        data={"version": "1.0.0"}
    )

@app.get("/health", response_model=ApiResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        await db_manager.test_connection()
        return ApiResponse(
            success=True,
            message="API and database are healthy",
            data={"status": "healthy"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}"
        )

@app.get("/ping")
async def ping():
    """Lightweight ping endpoint to keep server alive"""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "message": "Server is active"
    }

@app.get("/apps", response_model=ApiResponse)
async def get_apps():
    """Get all apps"""
    try:
        apps = await db_manager.get_all_apps()
        return ApiResponse(
            success=True,
            message="Apps retrieved successfully",
            data={"apps": apps}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve apps: {str(e)}"
        )

@app.get("/apps/{app_id}", response_model=ApiResponse)
async def get_app(app_id: str):
    """Get a specific app by app_id"""
    try:
        app = await db_manager.get_app_by_id(app_id)
        if not app:
            raise HTTPException(
                status_code=404,
                detail="App not found"
            )
        return ApiResponse(
            success=True,
            message="App retrieved successfully",
            data={"app": app}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# File download endpoints
# These endpoints preserve binary integrity by avoiding unnecessary base64 conversions
# and returning files in their original format to prevent size inflation

def get_file_extension(file_type: str) -> str:
    """Get file extension based on file type"""
    extensions = {
        'json': '.json',
        'lua': '.lua', 
        'manifest': '.manifest',
        'vdf': '.vdf'
    }
    return extensions.get(file_type, '.txt')

def get_mime_type(file_type: str) -> str:
    """Get MIME type based on file type"""
    mime_types = {
        'json': 'application/json',
        'lua': 'text/plain',
        'manifest': 'text/plain', 
        'vdf': 'text/plain'
    }
    return mime_types.get(file_type, 'text/plain')

@app.get("/files/{app_id}", response_model=ApiResponse)
async def list_files(app_id: str):
    """List all files for a specific app_id"""
    try:
        # Validate app_id is numeric
        if not app_id.isdigit():
            raise HTTPException(
                status_code=400,
                detail="Invalid app_id format. Must be numeric."
            )
        
        files = await db_manager.get_files_by_app_id(app_id)
        
        # Convert to AppFile models
        app_files = []
        for file_data in files:
            app_files.append(AppFile(
                id=file_data['id'],
                app_id=file_data['app_id'],
                filename=file_data['filename'],
                file_type=file_data['file_type'],
                size=file_data['size'],
                uploaded_at=file_data['uploaded_at']
            ))
        
        return ApiResponse(
            success=True,
            message=f"Found {len(app_files)} files for app {app_id}",
            data={"files": [file.dict() for file in app_files]}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/download/file/{file_id}")
@limiter.limit("1/2minutes")
async def download_file(request: Request, file_id: str, file_type: str):
    """Download a specific file by ID and type"""
    try:
        # Validate file_type
        valid_types = ['json', 'lua', 'manifest', 'vdf']
        if file_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file_type. Must be one of: {', '.join(valid_types)}"
            )
        
        file_data = await db_manager.get_file_by_id(file_id, file_type)
        
        if not file_data:
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        # Get file extension and ensure filename has it
        extension = get_file_extension(file_type)
        filename = file_data['filename']
        if not filename.endswith(extension):
            filename += extension
        
        # Return original file content without any encoding conversion
        # This preserves the exact binary data and file size
        original_content = file_data['content']
        
        # Convert to bytes only if it's a string (for text files)
        if isinstance(original_content, str):
            content_bytes = original_content.encode('utf-8')
        else:
            # If it's already bytes, use as-is
            content_bytes = original_content
        
        # Create streaming response with original binary data
        def generate():
            yield content_bytes
        
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Length': str(len(content_bytes)),
            'Content-Type': 'application/octet-stream',  # Use binary type to preserve data
            'Cache-Control': 'no-cache'
        }
        
        return StreamingResponse(
            generate(),
            media_type='application/octet-stream',  # Binary download to preserve integrity
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/download/app/{app_id}")
@limiter.limit("1/2minutes")
async def download_app_files(request: Request, app_id: str):
    """Download all files for an app as a ZIP archive"""
    try:
        # Validate app_id is numeric
        if not app_id.isdigit():
            raise HTTPException(
                status_code=400,
                detail="Invalid app_id format. Must be numeric."
            )
        
        files = await db_manager.get_all_files_content_by_app_id(app_id)
        
        if not files:
            raise HTTPException(
                status_code=404,
                detail=f"No files found for app {app_id}"
            )
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_data in files:
                # Get file extension and ensure filename has it
                extension = get_file_extension(file_data['file_type'])
                filename = file_data['filename']
                if not filename.endswith(extension):
                    filename += extension
                
                # Preserve original file content without conversion
                original_content = file_data['content']
                
                # Handle content based on its type to preserve binary integrity
                if isinstance(original_content, str):
                    # For text files, encode to bytes
                    file_bytes = original_content.encode('utf-8')
                else:
                    # For binary files, use as-is
                    file_bytes = original_content
                
                # Add file to ZIP with original binary data
                zip_file.writestr(filename, file_bytes)
        
        zip_buffer.seek(0)
        
        # Create streaming response with binary integrity preservation
        def generate():
            while True:
                chunk = zip_buffer.read(8192)
                if not chunk:
                    break
                yield chunk
        
        headers = {
            'Content-Disposition': f'attachment; filename="app_{app_id}_files.zip"',
            'Content-Length': str(zip_buffer.getbuffer().nbytes),
            'Content-Type': 'application/zip',
            'Cache-Control': 'no-cache'
        }
        
        return StreamingResponse(
            generate(),
            media_type='application/zip',
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)