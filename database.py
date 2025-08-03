import os
import asyncio
from typing import List, Dict, Optional
from libsql_client import create_client_sync
from libsql_client.sync import Client
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.client: Optional[Client] = None
        self.database_url = os.getenv("TURSO_DATABASE_URL")
        self.auth_token = os.getenv("TURSO_AUTH_TOKEN")
        
        if not self.database_url or not self.auth_token:
            raise ValueError("TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set in environment variables")
    
    async def initialize(self):
        """Initialize the database connection and create tables"""
        try:
            # Create synchronous client (libsql-client doesn't have async support yet)
            self.client = create_client_sync(
                url=self.database_url,
                auth_token=self.auth_token
            )
            
            # Create tables if they don't exist
            await self._create_tables()
            print("Database initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            raise
    
    async def _create_tables(self):
        """Create necessary tables"""
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            steam_id TEXT UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Run in thread pool since libsql-client is synchronous
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.client.execute, create_users_table)
    
    async def test_connection(self):
        """Test database connection"""
        if not self.client:
            raise Exception("Database not initialized")
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            self.client.execute, 
            "SELECT 1 as test"
        )
        return result
    
    async def create_user(self, username: str, email: str, steam_id: Optional[str] = None) -> int:
        """Create a new user"""
        if not self.client:
            raise Exception("Database not initialized")
        
        query = """
        INSERT INTO users (username, email, steam_id) 
        VALUES (?, ?, ?)
        """
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.client.execute,
            query,
            [username, email, steam_id]
        )
        
        return result.last_insert_rowid
    
    async def get_all_users(self) -> List[Dict]:
        """Get all users"""
        if not self.client:
            raise Exception("Database not initialized")
        
        query = "SELECT * FROM users ORDER BY created_at DESC"
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.client.execute, query)
        
        # Convert rows to dictionaries
        users = []
        for row in result.rows:
            user = {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "steam_id": row[3],
                "created_at": row[4],
                "updated_at": row[5]
            }
            users.append(user)
        
        return users
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get a user by ID"""
        if not self.client:
            raise Exception("Database not initialized")
        
        query = "SELECT * FROM users WHERE id = ?"
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.client.execute,
            query,
            [user_id]
        )
        
        if not result.rows:
            return None
        
        row = result.rows[0]
        return {
            "id": row[0],
            "username": row[1],
            "email": row[2],
            "steam_id": row[3],
            "created_at": row[4],
            "updated_at": row[5]
        }
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID"""
        if not self.client:
            raise Exception("Database not initialized")
        
        query = "DELETE FROM users WHERE id = ?"
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.client.execute,
            query,
            [user_id]
        )
        
        return result.rows_affected > 0
    
    async def close(self):
        """Close database connection"""
        if self.client:
            # libsql-client doesn't require explicit closing
            self.client = None
            print("Database connection closed")