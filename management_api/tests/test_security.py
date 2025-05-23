import pytest
from fastapi.testclient import TestClient
from opmas_mgmt_api.main import app
from opmas_mgmt_api.security import RateLimiter, InputValidator
from opmas_mgmt_api.core.exceptions import OPMASException

client = TestClient(app)

def test_rate_limiting():
    # Test rate limiting
    rate_limiter = RateLimiter(requests_per_minute=2)
    client_ip = "127.0.0.1"
    
    # First request should pass
    assert not rate_limiter.is_rate_limited(client_ip)
    
    # Second request should pass
    assert not rate_limiter.is_rate_limited(client_ip)
    
    # Third request should be limited
    assert rate_limiter.is_rate_limited(client_ip)

def test_security_headers():
    response = client.get("/health")
    headers = response.headers
    
    # Check security headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Strict-Transport-Security" in headers
    assert "Content-Security-Policy" in headers
    assert "Referrer-Policy" in headers

def test_input_validation():
    validator = InputValidator()
    
    # Test IP address validation
    assert validator.validate_ip_address("192.168.1.1")
    assert not validator.validate_ip_address("256.168.1.1")
    assert not validator.validate_ip_address("192.168.1")
    assert not validator.validate_ip_address("192.168.1.1.1")
    
    # Test hostname validation
    assert validator.validate_hostname("example.com")
    assert validator.validate_hostname("sub.example.com")
    assert not validator.validate_hostname("invalid hostname")
    assert not validator.validate_hostname("example.com/")
    
    # Test input sanitization
    input_str = "<script>alert('xss')</script>"
    sanitized = validator.sanitize_input(input_str)
    assert "<script>" not in sanitized
    assert "alert" not in sanitized

def test_json_schema_validation():
    validator = InputValidator()
    schema = {
        "name": str,
        "age": int,
        "active": bool
    }
    
    # Valid data
    valid_data = {
        "name": "John",
        "age": 30,
        "active": True
    }
    assert validator.validate_json_schema(valid_data, schema)
    
    # Invalid data
    invalid_data = {
        "name": "John",
        "age": "30",  # Should be int
        "active": True
    }
    assert not validator.validate_json_schema(invalid_data, schema)

def test_error_handling():
    # Test custom exception handling
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert "detail" in response.json()
    
    # Test rate limit error
    for _ in range(61):  # Exceed rate limit
        client.get("/health")
    response = client.get("/health")
    assert response.status_code == 429
    assert "Too many requests" in response.json()["detail"]

def test_method_validation():
    # Test allowed methods
    assert client.get("/health").status_code == 200
    assert client.post("/health").status_code == 405  # Method not allowed

def test_host_validation():
    # Test host header validation
    response = client.get("/health", headers={"Host": "invalid.host"})
    assert response.status_code == 400
    assert "Invalid host header" in response.json()["detail"] 