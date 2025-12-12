"""
Business logic for organization management operations.
"""
from fastapi import HTTPException, status
from app.database import master_db, get_org_collection_name
from app.utils.hash import hash_password, verify_password
from datetime import datetime
from bson import ObjectId
from typing import Optional, Dict, Any


async def create_organization(
    db,
    organization_name: str,
    email: str,
    password: str
) -> Dict[str, Any]:
    """
    Create a new organization with admin user.
    
    Steps:
    1. Normalize organization name and check uniqueness
    2. Create admin user with hashed password
    3. Create organization collection
    4. Insert organization metadata
    
    Args:
        db: Master database instance
        organization_name: Name of the organization
        email: Admin email address
        password: Admin password (will be hashed)
        
    Returns:
        Dictionary containing organization metadata (excludes password)
        
    Raises:
        HTTPException: If organization name or email already exists
    """
    # Normalize organization name
    normalized_name = organization_name.strip()
    collection_name = get_org_collection_name(normalized_name)
    
    # Check if organization name already exists
    existing_org = await db.organizations.find_one({
        "organization_name": normalized_name
    })
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization '{normalized_name}' already exists"
        )
    
    # Check if email already exists
    existing_admin = await db.admins.find_one({"email": email})
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{email}' is already registered"
        )
    
    # Hash password
    hashed_password = hash_password(password)
    
    # Create admin document
    admin_doc = {
        "email": email,
        "hashed_password": hashed_password,
        "organization_name": normalized_name,
        "org_collection": collection_name,
        "created_at": datetime.utcnow()
    }
    
    # Insert admin
    admin_result = await db.admins.insert_one(admin_doc)
    admin_id = admin_result.inserted_id
    
    # Create organization collection (touch it by inserting and deleting a dummy doc)
    org_collection = db[collection_name]
    
    # Create collection by inserting a dummy document and deleting it
    dummy_doc = {"_dummy": True, "created_at": datetime.utcnow()}
    await org_collection.insert_one(dummy_doc)
    await org_collection.delete_one({"_dummy": True})
    
    # Create organization metadata
    org_doc = {
        "organization_name": normalized_name,
        "collection_name": collection_name,
        "admin_id": admin_id,
        "admin_email": email,
        "created_at": datetime.utcnow()
    }
    
    # Insert organization metadata
    await db.organizations.insert_one(org_doc)
    
    # Return organization metadata (exclude password)
    return {
        "organization_name": normalized_name,
        "collection_name": collection_name,
        "admin_email": email,
        "created_at": org_doc["created_at"]
    }


async def get_organization_by_name(
    db,
    organization_name: str
) -> Optional[Dict[str, Any]]:
    """
    Get organization metadata by name.
    
    Args:
        db: Master database instance
        organization_name: Name of the organization
        
    Returns:
        Organization metadata dictionary or None if not found
    """
    org = await db.organizations.find_one({
        "organization_name": organization_name.strip()
    })
    
    if org:
        return {
            "organization_name": org["organization_name"],
            "collection_name": org["collection_name"],
            "admin_email": org["admin_email"],
            "created_at": org["created_at"]
        }
    return None


async def update_organization(
    db,
    old_name: str,
    new_name: Optional[str] = None,
    email: Optional[str] = None,
    password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update organization name and/or admin credentials.
    
    If organization name changes:
    - Validates new name uniqueness
    - Creates new collection name
    - Copies all documents from old collection to new
    - Updates master record
    
    Args:
        db: Master database instance
        old_name: Current organization name
        new_name: New organization name (optional)
        email: New admin email (optional)
        password: New admin password (optional)
        
    Returns:
        Updated organization metadata
        
    Raises:
        HTTPException: If organization not found or new name already exists
    """
    # Find existing organization
    org = await db.organizations.find_one({
        "organization_name": old_name.strip()
    })
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization '{old_name}' not found"
        )
    
    admin_id = org["admin_id"]
    old_collection_name = org["collection_name"]
    update_data = {}
    
    # Handle organization name change
    if new_name and new_name.strip() != old_name.strip():
        normalized_new_name = new_name.strip()
        new_collection_name = get_org_collection_name(normalized_new_name)
        
        # Check if new name already exists
        existing_org = await db.organizations.find_one({
            "organization_name": normalized_new_name
        })
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization '{normalized_new_name}' already exists"
            )
        
        # Copy documents from old collection to new
        old_collection = db[old_collection_name]
        new_collection = db[new_collection_name]
        
        # Batch copy documents to avoid memory issues
        async for doc in old_collection.find({}):
            # Remove _id to allow MongoDB to generate new one
            doc.pop("_id", None)
            await new_collection.insert_one(doc)
        
        # Drop old collection
        await db.drop_collection(old_collection_name)
        
        # Update collection name in metadata
        update_data["organization_name"] = normalized_new_name
        update_data["collection_name"] = new_collection_name
    
    # Handle email change
    if email:
        # Check if email already exists for another admin
        existing_admin = await db.admins.find_one({
            "email": email,
            "_id": {"$ne": admin_id}
        })
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{email}' is already registered"
            )
        update_data["admin_email"] = email
    
    # Handle password change
    if password:
        hashed_password = hash_password(password)
        await db.admins.update_one(
            {"_id": admin_id},
            {"$set": {"hashed_password": hashed_password}}
        )
    
    # Update admin document
    if email or (new_name and new_name.strip() != old_name.strip()):
        admin_update = {}
        if email:
            admin_update["email"] = email
        if new_name and new_name.strip() != old_name.strip():
            admin_update["organization_name"] = update_data.get("organization_name")
            admin_update["org_collection"] = update_data.get("collection_name")
        
        if admin_update:
            await db.admins.update_one(
                {"_id": admin_id},
                {"$set": admin_update}
            )
    
    # Update organization metadata
    if update_data:
        await db.organizations.update_one(
            {"organization_name": old_name.strip()},
            {"$set": update_data}
        )
    
    # Fetch updated organization
    updated_org = await db.organizations.find_one({
        "_id": org["_id"]
    })
    
    return {
        "organization_name": updated_org["organization_name"],
        "collection_name": updated_org["collection_name"],
        "admin_email": updated_org["admin_email"],
        "created_at": updated_org["created_at"]
    }


async def delete_organization(
    db,
    organization_name: str,
    requesting_admin_id: ObjectId
) -> Dict[str, Any]:
    """
    Delete an organization and all its data.
    
    Steps:
    1. Verify requesting admin owns the organization
    2. Drop organization collection
    3. Delete organization metadata
    4. Delete admin document
    
    Args:
        db: Master database instance
        organization_name: Name of organization to delete
        requesting_admin_id: ID of admin requesting deletion
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If organization not found or admin doesn't own it
    """
    # Find organization
    org = await db.organizations.find_one({
        "organization_name": organization_name.strip()
    })
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization '{organization_name}' not found"
        )
    
    # Verify admin ownership
    if org["admin_id"] != requesting_admin_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the organization admin can delete this organization"
        )
    
    collection_name = org["collection_name"]
    admin_id = org["admin_id"]
    
    # Drop organization collection
    await db.drop_collection(collection_name)
    
    # Delete organization metadata
    await db.organizations.delete_one({"_id": org["_id"]})
    
    # Delete admin document
    await db.admins.delete_one({"_id": admin_id})
    
    return {
        "message": f"Organization '{organization_name}' and all associated data deleted successfully"
    }

