from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from database import DatabaseManager
from models import CreateUserRequest, User, ApiResponse
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
    description="FastAPI backend connected to Turso database",
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

@app.post("/users", response_model=ApiResponse)
async def create_user(user_data: CreateUserRequest):
    """Create a new user"""
    try:
        user_id = await db_manager.create_user(
            username=user_data.username,
            email=user_data.email,
            steam_id=user_data.steam_id
        )
        return ApiResponse(
            success=True,
            message="User created successfully",
            data={"user_id": user_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create user: {str(e)}"
        )

@app.get("/users", response_model=ApiResponse)
async def get_users():
    """Get all users"""
    try:
        users = await db_manager.get_all_users()
        return ApiResponse(
            success=True,
            message="Users retrieved successfully",
            data={"users": users}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve users: {str(e)}"
        )

@app.get("/users/{user_id}", response_model=ApiResponse)
async def get_user(user_id: int):
    """Get a specific user by ID"""
    try:
        user = await db_manager.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        return ApiResponse(
            success=True,
            message="User retrieved successfully",
            data={"user": user}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user: {str(e)}"
        )

@app.delete("/users/{user_id}", response_model=ApiResponse)
async def delete_user(user_id: int):
    """Delete a user by ID"""
    try:
        success = await db_manager.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        return ApiResponse(
            success=True,
            message="User deleted successfully",
            data={"deleted_user_id": user_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete user: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)