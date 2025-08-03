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
            self.api_url = self.database_url.replace("libsql://", "https://") + "/v2/pipeline"
        else:
            self.api_url = self.database_url.rstrip('/') + "/v2/pipeline"
    
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
    
    def _format_turso_params(self, params: Optional[List]) -> List[Dict[str, Any]]:
        """Format parameters for Turso v2 API - each param must be a type-value object"""
        if not params:
            return []
        
        formatted_params = []
        for param in params:
            if param is None:
                formatted_params.append({"type": "null", "value": None})
            elif isinstance(param, str):
                formatted_params.append({"type": "text", "value": param})
            elif isinstance(param, int):
                formatted_params.append({"type": "integer", "value": str(param)})
            elif isinstance(param, float):
                formatted_params.append({"type": "real", "value": str(param)})
            else:
                # Default to text for other types
                formatted_params.append({"type": "text", "value": str(param)})
        
        return formatted_params
    
    async def _execute_query(self, query: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Execute a query using Turso HTTP API v2"""
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        # Build the statement object
        stmt = {"sql": query}
        if params:
            stmt["args"] = self._format_turso_params(params)
        
        # Build the payload with proper v2 structure
        payload = {
            "requests": [
                {"type": "execute", "stmt": stmt},
                {"type": "close"}
            ]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Database query failed: {response.status_code} - {response.text}")
            
            result = response.json()
            
            # Extract the actual result from the v2 response structure
            if "results" in result and len(result["results"]) > 0:
                first_result = result["results"][0]
                if first_result.get("type") == "ok" and "response" in first_result:
                    return first_result["response"].get("result", {})
                elif first_result.get("type") == "error":
                    raise Exception(f"Database query error: {first_result.get('error', 'Unknown error')}")
            
            return result
    
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
    
    async def get_all_apps(self) -> List[Dict]:
        """Get all apps"""
        query = "SELECT * FROM apps ORDER BY created_at DESC"
        
        result = await self._execute_query(query)
        
        # Convert rows to dictionaries
        apps = []
        if "rows" in result:
            for row in result["rows"]:
                # Extract values from Turso v2 format
                app = {
                    "app_id": self._extract_value(row[0]),
                    "created_at": self._extract_value(row[1]),
                    "updated_at": self._extract_value(row[2]),
                    "name": self._extract_value(row[3]),
                    "type": self._extract_value(row[4])
                }
                apps.append(app)
        
        return apps
    
    async def get_app_by_id(self, app_id: str) -> Optional[Dict]:
        """Get an app by app_id"""
        query = "SELECT * FROM apps WHERE app_id = ?"
        
        result = await self._execute_query(query, [app_id])
        
        if not result.get("rows") or len(result["rows"]) == 0:
            return None
        
        row = result["rows"][0]
        return {
            "app_id": self._extract_value(row[0]),
            "created_at": self._extract_value(row[1]),
            "updated_at": self._extract_value(row[2]),
            "name": self._extract_value(row[3]),
            "type": self._extract_value(row[4])
        }
    
    def _extract_value(self, turso_value):
        """Extract value from Turso v2 API response format"""
        if isinstance(turso_value, dict) and "value" in turso_value:
            return turso_value["value"]
        return turso_value
    
    async def close(self):
        """Close database connection"""
        print("Database connection closed")