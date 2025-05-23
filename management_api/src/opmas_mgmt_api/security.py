from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from typing import Callable, Dict, List, Optional
import time
import re
from .core.exceptions import OPMASException
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = {}
        self.cleanup_interval = 60  # seconds
        self.last_cleanup = time.time()

    def is_rate_limited(self, client_ip: str) -> bool:
        current_time = time.time()
        
        # Cleanup old requests
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_requests(current_time)
            self.last_cleanup = current_time
        
        # Initialize client's request list if not exists
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Remove requests older than 1 minute
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < 60
        ]
        
        # Check if rate limit exceeded
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return True
        
        # Add current request
        self.requests[client_ip].append(current_time)
        return False

    def _cleanup_old_requests(self, current_time: float):
        for client_ip in list(self.requests.keys()):
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < 60
            ]
            if not self.requests[client_ip]:
                del self.requests[client_ip]

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        rate_limiter: RateLimiter,
        allowed_hosts: List[str] = None,
        allowed_methods: List[str] = None,
        allowed_headers: List[str] = None
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.allowed_hosts = allowed_hosts or ["*"]
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allowed_headers = allowed_headers or ["*"]
        
        # Security headers
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; font-src 'self' https://fonts.gstatic.com; img-src 'self' https://fastapi.tiangolo.com; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; worker-src 'self' blob:; connect-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check host header
        if not self._is_valid_host(request):
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid host header"}
            )

        # Check rate limit
        client_ip = request.client.host
        if self.rate_limiter.is_rate_limited(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"}
            )

        # Validate request method
        if request.method not in self.allowed_methods:
            return JSONResponse(
                status_code=405,
                content={"detail": "Method not allowed"}
            )

        # Process request
        try:
            response = await call_next(request)
            
            # Add security headers
            for header, value in self.security_headers.items():
                response.headers[header] = value
            
            return response
        except Exception as e:
            logger.error(f"Request processing error: {str(e)}", exc_info=True)
            if isinstance(e, OPMASException):
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail},
                    headers=e.headers
                )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )

    def _is_valid_host(self, request: Request) -> bool:
        if "*" in self.allowed_hosts:
            return True
        
        host = request.headers.get("host", "").split(":")[0]
        return any(
            re.match(pattern.replace("*", ".*"), host)
            for pattern in self.allowed_hosts
        )

class InputValidator:
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        
        return all(0 <= int(x) <= 255 for x in ip.split('.'))

    @staticmethod
    def validate_hostname(hostname: str) -> bool:
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(pattern, hostname))

    @staticmethod
    def sanitize_input(input_str: str) -> str:
        # Remove potentially dangerous characters
        return re.sub(r'[<>{}[\]\\]', '', input_str)

    @staticmethod
    def validate_json_schema(data: dict, schema: dict) -> bool:
        # Basic JSON schema validation
        for key, value in schema.items():
            if key not in data:
                return False
            if not isinstance(data[key], value):
                return False
        return True 