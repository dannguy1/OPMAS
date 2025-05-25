# Recovery Guide

## Session Recovery

### AI Session Recovery
1. **Initial Assessment**
   - Review current codebase state
   - Check pending changes
   - Verify running services

2. **Recovery Steps**
   ```bash
   # Check git status
   git status

   # Check running services
   docker-compose ps

   # Check application logs
   docker-compose logs
   ```

3. **Environment Verification**
   ```bash
   # Check database connection
   docker exec opmas-postgres-1 pg_isready

   # Verify environment files
   ls -la management_api/.env
   ls -la ui/.env
   ```

### Common Recovery Scenarios

#### Uncommitted Changes
1. Check for modified files:
   ```bash
   git status
   ```
2. Review changes:
   ```bash
   git diff
   ```
3. Stage and commit if appropriate:
   ```bash
   git add .
   git commit -m "Recovery: Save work after session disruption"
   ```

#### Service Interruption
1. Restart services:
   ```bash
   docker-compose down
   docker-compose up -d
   ```
2. Verify service health:
   ```bash
   docker-compose ps
   docker-compose logs
   ```

## System Recovery

### Database Issues

#### PostgreSQL Recovery
1. **Database Connection Issues**
   ```bash
   # Check PostgreSQL container status
   docker ps | grep postgres

   # View PostgreSQL logs
   docker logs opmas-postgres-1

   # Reset database (if needed)
   docker-compose down -v
   docker-compose up -d
   ```

2. **Migration Issues**
   ```bash
   # Reset migrations
   cd management_api
   rm -rf alembic/versions/*
   alembic revision --autogenerate -m "initial"
   alembic upgrade head
   ```

### Frontend Issues

#### Build and Dependency Issues
1. **Node Modules Corruption**
   ```bash
   cd ui
   rm -rf node_modules
   rm package-lock.json
   npm cache clean --force
   npm install
   ```

2. **TypeScript Compilation Errors**
   ```bash
   # Clear TypeScript cache
   rm -rf ui/node_modules/.cache/typescript
   # Rebuild
   npm run build
   ```

### Backend Issues

#### Python Environment
1. **Virtual Environment Issues**
   ```bash
   # Recreate virtual environment
   cd management_api
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. **Dependency Conflicts**
   ```bash
   # Clean pip cache
   pip cache purge
   # Reinstall dependencies
   pip install --no-cache-dir -r requirements.txt
   ```

### Docker Issues

1. **Container State Recovery**
   ```bash
   # Reset all containers
   docker-compose down
   docker system prune -f
   docker-compose up -d
   ```

2. **Volume Issues**
   ```bash
   # Reset volumes
   docker-compose down -v
   docker volume prune -f
   docker-compose up -d
   ```

## Backup Procedures

### Database Backup
```bash
# Create backup
docker exec opmas-postgres-1 pg_dump -U opmas opmas_mgmt > backup.sql

# Restore from backup
cat backup.sql | docker exec -i opmas-postgres-1 psql -U opmas opmas_mgmt
```

### Configuration Backup
```bash
# Backup environment files
cp management_api/.env management_api/.env.backup
cp ui/.env ui/.env.backup

# Restore from backup
cp management_api/.env.backup management_api/.env
cp ui/.env.backup ui/.env
```

## Emergency Procedures

### Complete System Reset
1. Stop all services
   ```bash
   docker-compose down
   ```

2. Clean all data
   ```bash
   docker system prune -af
   docker volume prune -f
   ```

3. Rebuild from scratch
   ```bash
   docker-compose up -d
   cd management_api
   python run.py
   cd ../ui
   npm run dev
   ```

### Data Recovery
1. **Database Recovery**
   - Use latest backup
   - Contact system administrator for point-in-time recovery

2. **Configuration Recovery**
   - Use version control history
   - Restore from backup files

## Prevention Best Practices

1. **Regular Backups**
   - Schedule automated database backups
   - Version control all configuration files
   - Document all manual changes

2. **Development Workflow**
   - Use feature branches
   - Create pull requests for review
   - Run tests before merging

3. **Monitoring**
   - Set up logging
   - Monitor system resources
   - Configure alerts for critical issues

## Contact Information

- System Administrator: [admin@example.com]
- Development Lead: [dev-lead@example.com]
- Emergency Support: [emergency@example.com]
