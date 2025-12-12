"""
Database connection and utilities for MongoDB.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from typing import Optional
import re

client: Optional[AsyncIOMotorClient] = None
master_db = None


def get_org_collection_name(org_name: str) -> str:
    """
    Normalize organization name to collection name format.
    
    Rules:
    - Lowercase
    - Trim whitespace
    - Replace spaces and non-alphanumeric characters with underscores
    - Multiple consecutive underscores become single underscore
    
    Args:
        org_name: Original organization name
        
    Returns:
        Normalized collection name prefixed with 'org_'
    """
    # Lowercase and trim
    normalized = org_name.lower().strip()
    
    # Replace spaces and non-alphanumeric with underscores
    normalized = re.sub(r'[^a-z0-9]+', '_', normalized)
    
    # Remove leading/trailing underscores
    normalized = normalized.strip('_')
    
    # Ensure it's not empty
    if not normalized:
        normalized = "default"
    
    return f"org_{normalized}"


async def connect_db():
    """Connect to MongoDB database."""
    global client, master_db
    client = AsyncIOMotorClient(settings.MONGO_URI)
    master_db = client["org_master_db"]
    # Test connection
    await client.admin.command('ping')


async def close_db():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()

