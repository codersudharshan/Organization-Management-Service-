"""
Database connection and utilities for MongoDB.

This module uses lazy imports for motor to avoid import-time compatibility issues.
Motor is imported only when connect_db() is called, not at module import time.
This ensures compatibility with different pymongo/motor version combinations.
"""
from app.config import settings
from typing import Optional
import re

# Module-level placeholders - motor is NOT imported here
client = None
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
    """
    Connect to MongoDB database.
    
    Lazy imports AsyncIOMotorClient to avoid import-time compatibility issues.
    This function should be called during application startup, not at module import.
    
    Returns:
        Tuple of (client, master_db) for convenience
    """
    global client, master_db
    
    # Lazy import motor - only when this function is called
    from motor.motor_asyncio import AsyncIOMotorClient
    
    client = AsyncIOMotorClient(settings.MONGO_URI)
    master_db = client["org_master_db"]
    
    # Test connection
    await client.admin.command('ping')
    
    return client, master_db


async def close_db():
    """
    Close MongoDB connection.
    
    Safely closes the client if it exists.
    """
    global client
    if client:
        client.close()
        client = None
