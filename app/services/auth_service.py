"""
Business logic for authentication operations.
"""
from fastapi import HTTPException, status
from app.utils.hash import verify_password
from typing import Optional, Dict, Any


class AuthService:
    """Service class for authentication operations."""
    
    async def admin_login(
        self,
        db,
        email: str,
        password: str
    ) -> Dict[str, Any]:
        """
        Authenticate an admin user and return admin data.
        
        Args:
            db: Master database instance
            email: Admin email address
            password: Plain text password
            
        Returns:
            Dictionary containing admin document and org_collection name
            
        Raises:
            HTTPException: If email or password is invalid
        """
        # Find admin by email
        admin = await db.admins.find_one({"email": email})
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(password, admin["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Return admin data (exclude password)
        return {
            "admin_id": str(admin["_id"]),
            "email": admin["email"],
            "organization_name": admin["organization_name"],
            "org_collection": admin["org_collection"],
            "created_at": admin["created_at"]
        }


# Create a singleton instance for easy import
auth_service = AuthService()
