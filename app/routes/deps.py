"""
Dependencies for route authentication and authorization.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_master_db
from app.utils.jwt_handler import decode_access_token
from bson import ObjectId

# HTTPBearer for token extraction and Swagger UI
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    """
    Dependency to get current authenticated admin from JWT token.
    
    Args:
        credentials: HTTPBearer credentials containing the token
        
    Returns:
        Dictionary containing admin document from database
        
    Raises:
        HTTPException: If token is invalid or admin not found
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
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
        db = get_master_db()
        admin = await db.admins.find_one({"_id": ObjectId(admin_id)})
        
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
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not available: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

