# Troubleshooting Guide

## Common Issues and Solutions

### Development Environment

#### Docker Issues
1. **Container Won't Start**
   ```bash
   # Check container logs
   docker logs <container-name>

   # Check container status
   docker ps -a

   # Restart container
   docker-compose restart <service-name>
   ```

2. **Port Conflicts**
   ```bash
   # Check port usage
   sudo lsof -i :<port>

   # Kill process using port
   sudo kill -9 <PID>
   ```

#### Database Issues
1. **Connection Refused**
   ```bash
   # Check PostgreSQL status
   docker exec opmas-postgres-1 pg_isready

   # Check connection settings
   cat management_api/.env | grep DATABASE_URL
   ```

2. **Migration Errors**
   ```bash
   # Check migration status
   cd management_api
   alembic current

   # Reset migrations
   alembic downgrade base
   alembic upgrade head
   ```

### Frontend Issues

#### Build Problems
1. **TypeScript Errors**
   ```bash
   # Clear TypeScript cache
   rm -rf ui/node_modules/.cache/typescript

   # Rebuild
   cd ui
   npm run build
   ```

2. **Dependency Issues**
   ```bash
   # Clean install
   cd ui
   rm -rf node_modules
   rm package-lock.json
   npm install
   ```

#### Runtime Issues
1. **API Connection**
   - Check API URL in `.env`
   - Verify CORS settings
   - Check network tab in browser dev tools

2. **State Management**
   - Clear browser cache
   - Check Redux DevTools
   - Verify context providers

### Backend Issues

#### Python Environment
1. **Import Errors**
   ```bash
   # Check Python path
   python -c "import sys; print(sys.path)"

   # Reinstall package
   pip install -e .
   ```

2. **Virtual Environment**
   ```bash
   # Recreate venv
   cd management_api
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

#### API Issues
1. **500 Errors**
   - Check application logs
   - Verify database connection
   - Check environment variables

2. **Authentication**
   - Verify token generation
   - Check token expiration
   - Validate JWT secret

### Performance Issues

#### Slow Response Times
1. **Database Queries**
   ```sql
   -- Enable query logging
   ALTER DATABASE opmas_mgmt SET log_statement = 'all';

   -- Check slow queries
   SELECT * FROM pg_stat_activity WHERE state = 'active';
   ```

2. **API Performance**
   - Enable request logging
   - Check response times
   - Monitor memory usage

#### Memory Issues
1. **Memory Leaks**
   ```bash
   # Check container memory
   docker stats

   # Restart service
   docker-compose restart <service>
   ```

2. **High CPU Usage**
   ```bash
   # Check process usage
   top

   # Profile Python code
   python -m cProfile -o output.prof script.py
   ```

### Security Issues

#### Authentication
1. **Token Issues**
   - Check token expiration
   - Verify JWT secret
   - Check token format

2. **Permission Issues**
   - Verify user roles
   - Check permission settings
   - Review access logs

#### Data Security
1. **Sensitive Data**
   - Check for exposed credentials
   - Verify encryption
   - Review access controls

2. **API Security**
   - Check rate limiting
   - Verify input validation
   - Review security headers

## Debugging Tools

### Frontend
1. **Browser DevTools**
   - Network tab for API calls
   - Console for errors
   - React DevTools for components

2. **Logging**
   ```javascript
   // Add debug logging
   console.debug('Debug info:', data);
   ```

### Backend
1. **Python Debugger**
   ```python
   import pdb; pdb.set_trace()
   ```

2. **Logging**
   ```python
   import logging
   logging.debug('Debug info: %s', data)
   ```

### Database
1. **Query Analysis**
   ```sql
   EXPLAIN ANALYZE SELECT * FROM table;
   ```

2. **Performance Monitoring**
   ```sql
   SELECT * FROM pg_stat_activity;
   ```

## Monitoring

### System Metrics
1. **Resource Usage**
   ```bash
   # CPU and Memory
   top

   # Disk usage
   df -h
   ```

2. **Network**
   ```bash
   # Check connections
   netstat -tulpn

   # Monitor traffic
   tcpdump
   ```

### Application Metrics
1. **Logs**
   ```bash
   # Application logs
   tail -f management_api/logs/app.log

   # Access logs
   tail -f management_api/logs/access.log
   ```

2. **Performance**
   - Monitor response times
   - Track error rates
   - Check resource usage

## Getting Help

### Internal Resources
- Check [Recovery Guide](recovery-guide.md)
- Review [Development Workflow](workflow.md)
- Consult team documentation

### External Resources
- Stack Overflow
- GitHub Issues
- Documentation

### Support Channels
- Team Slack
- Email support
- Issue tracker
