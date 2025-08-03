from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from database import DatabaseManager
from models import App, ApiResponse
from typing import List

# Load environment variables
load_dotenv()

# Initialize database manager
db_manager = DatabaseManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db_manager.initialize()
    yield
    # Shutdown
    await db_manager.close()

# Create FastAPI app
app = FastAPI(
    title="Steam External Backend API",
    description="FastAPI backend for Steam apps data connected to Turso database",
    version="1.0.0",
    lifespan=lifespan
)

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
            detail=f"Failed to retrieve app: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)