"""
Integration tests for organization management flow.
"""
import pytest
from httpx import AsyncClient
from app.main import app
from app.database import connect_db, close_db, master_db
import os


@pytest.fixture(scope="module")
async def setup_db():
    """Setup and teardown database connection for tests."""
    await connect_db()
    yield
    await close_db()


@pytest.fixture(scope="function")
async def cleanup_db():
    """Cleanup test data after each test."""
    yield
    # Clean up test data
    if master_db:
        await master_db.organizations.delete_many({"organization_name": {"$regex": "^TestOrg"}})
        await master_db.admins.delete_many({"email": {"$regex": "^test@"}})
        # Drop test collections
        collections = await master_db.list_collection_names()
        for coll_name in collections:
            if coll_name.startswith("org_test"):
                await master_db.drop_collection(coll_name)


@pytest.mark.asyncio
async def test_create_organization(setup_db, cleanup_db):
    """Test creating a new organization."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/org/create",
            json={
                "organization_name": "TestOrg1",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["organization_name"] == "TestOrg1"
        assert data["admin_email"] == "test@example.com"
        assert "collection_name" in data
        assert data["collection_name"].startswith("org_")
        assert "created_at" in data


@pytest.mark.asyncio
async def test_get_organization(setup_db, cleanup_db):
    """Test retrieving an organization."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First create an organization
        create_response = await client.post(
            "/org/create",
            json={
                "organization_name": "TestOrg2",
                "email": "test2@example.com",
                "password": "password123"
            }
        )
        assert create_response.status_code == 201
        
        # Then retrieve it
        get_response = await client.get("/org/TestOrg2")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["organization_name"] == "TestOrg2"
        assert data["admin_email"] == "test2@example.com"


@pytest.mark.asyncio
async def test_login(setup_db, cleanup_db):
    """Test admin login and JWT token generation."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create an organization
        create_response = await client.post(
            "/org/create",
            json={
                "organization_name": "TestOrg3",
                "email": "test3@example.com",
                "password": "password123"
            }
        )
        assert create_response.status_code == 201
        
        # Login
        login_response = await client.post(
            "/admin/login",
            json={
                "email": "test3@example.com",
                "password": "password123"
            }
        )
        
        assert login_response.status_code == 200
        data = login_response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "admin" in data
        assert data["admin"]["email"] == "test3@example.com"
        assert data["admin"]["organization_name"] == "TestOrg3"


@pytest.mark.asyncio
async def test_get_nonexistent_organization(setup_db, cleanup_db):
    """Test retrieving a non-existent organization returns 404."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/org/NonExistentOrg")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_organization_name(setup_db, cleanup_db):
    """Test that creating duplicate organization names fails."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create first organization
        response1 = await client.post(
            "/org/create",
            json={
                "organization_name": "TestOrg4",
                "email": "test4a@example.com",
                "password": "password123"
            }
        )
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = await client.post(
            "/org/create",
            json={
                "organization_name": "TestOrg4",
                "email": "test4b@example.com",
                "password": "password123"
            }
        )
        assert response2.status_code == 400

