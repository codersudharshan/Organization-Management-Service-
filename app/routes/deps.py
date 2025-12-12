"""
Dependencies for route authentication and authorization.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.database import master_db
from app.utils.jwt_handler import decode_access_token
from bson import ObjectId

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")


async def get_current_admin(token: str = Depends(oauth2_scheme)):
    """
    Dependency to get current authenticated admin from JWT token.
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        Dictionary containing admin document from database
        
    Raises:
        HTTPException: If token is invalid or admin not found
    """
    try:
        payload = decode_access_token(token)
        admin_id = payload.get("admin_id")
        
        if admin_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Fetch admin from database
        admin = await master_db.admins.find_one({"_id": ObjectId(admin_id)})
        
        if admin is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Convert ObjectId to string for JSON serialization
        admin["admin_id"] = str(admin["_id"])
        return admin
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

