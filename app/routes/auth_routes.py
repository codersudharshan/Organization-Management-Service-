"""
REST API routes for authentication.
"""
from fastapi import APIRouter, status
from app.database import master_db
from app.models.admin_model import AdminLogin, TokenResponse, AdminOut
from app.services.auth_service import admin_login
from app.utils.jwt_handler import create_access_token

router = APIRouter()


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(credentials: AdminLogin):
    """
    Authenticate admin and return JWT token.
    
    - **email**: Admin email address
    - **password**: Admin password
    
    Returns JWT token with admin_id and org_collection in payload.
    """
    try:
        admin_data = await admin_login(
            master_db,
            credentials.email,
            credentials.password
        )
        
        # Create JWT token with admin_id and org_collection
        token_data = {
            "admin_id": admin_data["admin_id"],
            "org_collection": admin_data["org_collection"]
        }
        access_token = create_access_token(data=token_data)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            admin=AdminOut(**admin_data)
        )
    except Exception as e:
        raise e

