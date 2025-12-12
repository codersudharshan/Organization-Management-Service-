"""
REST API routes for organization management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import master_db
from app.models.org_model import OrgCreate, OrgUpdate, OrgOut
from app.services.org_service import (
    create_organization,
    get_organization_by_name,
    update_organization,
    delete_organization
)
from app.routes.deps import get_current_admin
from bson import ObjectId

router = APIRouter()


@router.post("/create", response_model=OrgOut, status_code=status.HTTP_201_CREATED)
async def create_org(org_data: OrgCreate):
    """
    Create a new organization with admin user.
    
    - **organization_name**: Name of the organization
    - **email**: Admin email address
    - **password**: Admin password (minimum 6 characters)
    """
    try:
        result = await create_organization(
            master_db,
            org_data.organization_name,
            org_data.email,
            org_data.password
        )
        return OrgOut(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create organization: {str(e)}"
        )


@router.get("/{organization_name}", response_model=OrgOut)
async def get_org(organization_name: str):
    """
    Get organization metadata by name.
    
    - **organization_name**: Name of the organization to retrieve
    """
    org = await get_organization_by_name(master_db, organization_name)
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization '{organization_name}' not found"
        )
    
    return OrgOut(**org)


@router.put("/{organization_name}", response_model=OrgOut)
async def update_org(
    organization_name: str,
    org_update: OrgUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Update organization name and/or admin credentials.
    
    Requires authentication. Only the organization admin can update.
    
    - **organization_name**: Current organization name
    - **new_organization_name**: New organization name (optional)
    - **email**: New admin email (optional)
    - **password**: New admin password (optional)
    """
    # Verify admin owns this organization
    org = await get_organization_by_name(master_db, organization_name)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization '{organization_name}' not found"
        )
    
    # Check if current admin owns this organization
    admin_org = await master_db.organizations.find_one({
        "organization_name": organization_name,
        "admin_id": ObjectId(current_admin["admin_id"])
    })
    
    if not admin_org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the organization admin can update this organization"
        )
    
    try:
        result = await update_organization(
            master_db,
            organization_name,
            org_update.new_organization_name,
            org_update.email,
            org_update.password
        )
        return OrgOut(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization: {str(e)}"
        )


@router.delete("/{organization_name}")
async def delete_org(
    organization_name: str,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Delete an organization and all its data.
    
    Requires authentication. Only the organization admin can delete.
    
    - **organization_name**: Name of the organization to delete
    """
    try:
        result = await delete_organization(
            master_db,
            organization_name,
            ObjectId(current_admin["admin_id"])
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete organization: {str(e)}"
        )

