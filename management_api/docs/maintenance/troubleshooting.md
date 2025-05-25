# Troubleshooting Guide

## Common Issues and Solutions

### 1. Authentication Issues

#### Problem: Unable to obtain access token
**Symptoms:**
- 401 Unauthorized error
- Token request fails
- Invalid credentials error

**Solutions:**
1. Verify credentials
```bash
# Check user exists
curl -X POST "http://localhost:8001/api/v1/auth/token" \
     -H "Content-Type: application/json" \
     -d '{"username": "your_username", "password": "your_password"}'
```

2. Check JWT configuration
```python
# Verify JWT settings in .env
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

3. Check token expiration
```python
# Verify token expiration time
from datetime import datetime, timedelta
from jose import jwt

token_data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
exp = datetime.fromtimestamp(token_data['exp'])
```

### 2. Database Issues

#### Problem: Database connection errors
**Symptoms:**
- Connection refused
- Timeout errors
- Authentication failures

**Solutions:**
1. Check database service
```bash
# Check PostgreSQL status
pg_ctl status

# Check connection
psql -h localhost -U user -d opmas
```

2. Verify connection string
```python
# Check DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@localhost:5432/opmas
```

3. Check database logs
```bash
# View PostgreSQL logs
tail -f /var/log/postgresql/postgresql-14-main.log
```

#### Problem: Migration issues
**Symptoms:**
- Migration failures
- Schema mismatch
- Version conflicts

**Solutions:**
1. Check migration status
```bash
# View migration history
alembic history

# Check current version
alembic current
```

2. Fix migration issues
```bash
# Rollback last migration
alembic downgrade -1

# Create new migration
alembic revision --autogenerate -m "fix_migration"

# Apply migration
alembic upgrade head
```

### 3. API Performance Issues

#### Problem: Slow response times
**Symptoms:**
- High latency
- Timeout errors
- Rate limiting

**Solutions:**
1. Check rate limiting
```python
# Verify rate limit settings
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60
```

2. Monitor performance
```bash
# Check API metrics
curl http://localhost:8001/metrics

# Monitor response times
curl -w "%{time_total}\n" -o /dev/null -s http://localhost:8001/health
```

3. Optimize database queries
```python
# Enable query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### 4. Security Issues

#### Problem: Security header issues
**Symptoms:**
- CORS errors
- Security policy violations
- Missing headers

**Solutions:**
1. Check CORS configuration
```python
# Verify CORS settings
CORS_ORIGINS=["http://localhost:3000"]
```

2. Verify security headers
```bash
# Check response headers
curl -I http://localhost:8001/health
```

3. Update security policies
```python
# Review security middleware
from opmas_mgmt_api.security import SecurityMiddleware
```

### 5. Logging Issues

#### Problem: Missing or incorrect logs
**Symptoms:**
- No log files
- Incorrect log levels
- Missing information

**Solutions:**
1. Check log configuration
```python
# Verify logging settings
LOG_LEVEL=DEBUG
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

2. Enable debug logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

3. Check log files
```bash
# View application logs
tail -f logs/app.log

# View error logs
tail -f logs/error.log
```

### 6. Integration Issues

#### Problem: NATS connection issues
**Symptoms:**
- Message delivery failures
- Connection timeouts
- Service unavailability

**Solutions:**
1. Check NATS service
```bash
# Verify NATS status
nats-server -v

# Test connection
nats-pub test "Hello World"
```

2. Verify NATS configuration
```python
# Check NATS settings
NATS_URL=nats://localhost:4222
```

#### Problem: Redis connection issues
**Symptoms:**
- Cache misses
- Connection errors
- Performance degradation

**Solutions:**
1. Check Redis service
```bash
# Verify Redis status
redis-cli ping

# Monitor Redis
redis-cli monitor
```

2. Verify Redis configuration
```python
# Check Redis settings
REDIS_URL=redis://localhost:6379/0
```

## Debugging Procedures

### 1. API Debugging

#### Enable Debug Mode
```python
# Set debug mode
DEBUG=true

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
```

#### Use Debugger
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use Python debugger
python -m pdb -m uvicorn opmas_mgmt_api.main:app
```

### 2. Database Debugging

#### Enable SQL Logging
```python
# Log all SQL queries
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

#### Profile Queries
```python
# Profile slow queries
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 1.0:  # Log slow queries (> 1 second)
        print(f"Slow query ({total:.2f}s): {statement}")
```

### 3. Performance Profiling

#### Profile API Endpoints
```python
# Add timing middleware
from fastapi import Request
import time

@app.middleware("http")
async def add_timing(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

#### Monitor Memory Usage
```python
# Track memory usage
import psutil
import os

def log_memory_usage():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    print(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
```

## Recovery Procedures

### 1. Database Recovery

#### Backup Database
```bash
# Create backup
pg_dump -U user -d opmas > backup.sql

# Restore from backup
psql -U user -d opmas < backup.sql
```

#### Fix Corrupted Database
```bash
# Check database
pg_dump -U user -d opmas > /dev/null

# Repair if needed
pg_repack -U user -d opmas
```

### 2. Service Recovery

#### Restart Services
```bash
# Restart API
pkill -f uvicorn
uvicorn opmas_mgmt_api.main:app --reload

# Restart database
pg_ctl restart

# Restart Redis
redis-cli shutdown
redis-server

# Restart NATS
pkill -f nats-server
nats-server
```

#### Clear Caches
```bash
# Clear Redis cache
redis-cli FLUSHALL

# Clear file cache
sync; echo 3 > /proc/sys/vm/drop_caches
```

## Support Resources

### 1. Documentation
- [API Documentation](../api/overview.md)
- [Development Guide](../development/setup.md)
- [Deployment Guide](../deployment/overview.md)

### 2. Tools
- [Postman Collection](../tools/postman_collection.json)
- [Database Schema](../tools/schema.sql)
- [Configuration Templates](../tools/config_templates)

### 3. Contact
- Technical Support: support@example.com
- Development Team: dev@example.com
- Emergency Contact: emergency@example.com

### 4. Issue Tracking
- [GitHub Issues](https://github.com/your-org/opmas/issues)
- [Bug Report Template](../templates/bug_report.md)
- [Feature Request Template](../templates/feature_request.md)
