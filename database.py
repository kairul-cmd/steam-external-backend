import os
import asyncio
import httpx
import json
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv("TURSO_DATABASE_URL")
        self.auth_token = os.getenv("TURSO_AUTH_TOKEN")
        
        if not self.database_url or not self.auth_token:
            raise ValueError("TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set in environment variables")
        
        # Convert libsql:// to https:// for HTTP API
        if self.database_url.startswith("libsql://"):
            self.api_url = self.database_url.replace("libsql://", "https://") + "/v1/execute"
        else:
            self.api_url = self.database_url.rstrip('/') + "/v1/execute"
    
    async def initialize(self):
        """Initialize the database connection and create tables"""
        try:
            # Test connection
            await self.test_connection()
            
            # Create tables if they don't exist
            await self._create_tables()
            print("Database initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            raise
    
    async def _execute_query(self, query: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Execute a query using Turso HTTP API"""
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "stmt": query
        }
        
        if params:
            payload["args"] = params
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Database query failed: {response.status_code} - {response.text}")
            
            return response.json()
    
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
        
        await self._execute_query(create_users_table)
    
    async def test_connection(self):
        """Test database connection"""
        result = await self._execute_query("SELECT 1 as test")
        return result
    
    async def create_user(self, username: str, email: str, steam_id: Optional[str] = None) -> int:
        """Create a new user"""
        query = """
        INSERT INTO users (username, email, steam_id) 
        VALUES (?, ?, ?)
        """
        
        result = await self._execute_query(query, [username, email, steam_id])
        
        return result.get("last_insert_rowid", 0)
    
    async def get_all_users(self) -> List[Dict]:
        """Get all users"""
        query = "SELECT * FROM users ORDER BY created_at DESC"
        
        result = await self._execute_query(query)
        
        # Convert rows to dictionaries
        users = []
        if "rows" in result:
            for row in result["rows"]:
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
        query = "SELECT * FROM users WHERE id = ?"
        
        result = await self._execute_query(query, [user_id])
        
        if not result.get("rows") or len(result["rows"]) == 0:
            return None
        
        row = result["rows"][0]
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
        query = "DELETE FROM users WHERE id = ?"
        
        result = await self._execute_query(query, [user_id])
        
        return result.get("rows_affected", 0) > 0
    
    async def close(self):
        """Close database connection"""
        print("Database connection closed")