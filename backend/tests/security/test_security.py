import pytest
from datetime import datetime, timedelta
from jose import jwt
from core.auth.jwt import AuthHandler
from core.models.user import User
from core.schemas.auth import TokenData

@pytest.fixture
def auth_handler(test_config):
    """Provide an auth handler instance."""
    return AuthHandler(test_config)

def test_jwt_token_creation(auth_handler):
    """Test JWT token creation and validation."""
    # Create token
    token_data = {"sub": "testuser", "role": "admin"}
    token = auth_handler.create_access_token(token_data)
    
    # Verify token
    payload = jwt.decode(
        token,
        auth_handler.secret_key,
        algorithms=[auth_handler.algorithm]
    )
    assert payload["sub"] == "testuser"
    assert payload["role"] == "admin"
    assert "exp" in payload

def test_token_expiration(auth_handler):
    """Test token expiration handling."""
    # Create expired token
    token_data = {"sub": "testuser"}
    expired_token = jwt.encode(
        {
            **token_data,
            "exp": datetime.utcnow() - timedelta(minutes=1)
        },
        auth_handler.secret_key,
        algorithm=auth_handler.algorithm
    )
    
    # Verify token is rejected
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(
            expired_token,
            auth_handler.secret_key,
            algorithms=[auth_handler.algorithm]
        )

def test_password_hashing(auth_handler):
    """Test password hashing and verification."""
    # Hash password
    password = "testpassword123"
    hashed = auth_handler.get_password_hash(password)
    
    # Verify password
    assert auth_handler.verify_password(password, hashed)
    assert not auth_handler.verify_password("wrongpassword", hashed)

@pytest.mark.asyncio
async def test_authentication_flow(async_client, test_db):
    """Test complete authentication flow."""
    # 1. Register user
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    
    # 2. Login
    response = await async_client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    
    # 3. Access protected endpoint
    token = data["access_token"]
    response = await async_client.get(
        "/api/v1/devices",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_authorization_roles(async_client, auth_handler):
    """Test role-based authorization."""
    # Create tokens for different roles
    admin_token = auth_handler.create_access_token({"sub": "admin", "role": "admin"})
    user_token = auth_handler.create_access_token({"sub": "user", "role": "user"})
    
    # Test admin-only endpoint
    response = await async_client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    response = await async_client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403

def test_rate_limiting(async_client):
    """Test API rate limiting."""
    # Make multiple requests in quick succession
    for _ in range(10):
        response = async_client.get("/api/v1/devices")
    
    # Verify rate limit is enforced
    response = async_client.get("/api/v1/devices")
    assert response.status_code == 429  # Too Many Requests

@pytest.mark.asyncio
async def test_security_headers(async_client):
    """Test security headers are properly set."""
    response = await async_client.get("/api/v1/health")
    headers = response.headers
    
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-XSS-Protection"] == "1; mode=block"
    assert "Strict-Transport-Security" in headers 