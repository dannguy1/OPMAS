# Deployment Guide

## Overview
This guide provides comprehensive instructions for deploying the OPMAS Management API in various environments, from development to production.

## Deployment Environments

### 1. Development Environment
- Single server setup
- Local services
- Development tools
- Debugging enabled

### 2. Staging Environment
- Production-like setup
- Isolated services
- Monitoring enabled
- Testing tools

### 3. Production Environment
- High availability setup
- Load balancing
- Full monitoring
- Security hardening

## Prerequisites

### System Requirements
- Linux server (Ubuntu 20.04+ or RHEL 8+)
- 4+ CPU cores
- 8GB+ RAM
- 50GB+ storage
- Network connectivity

### Software Requirements
- Python 3.8+
- PostgreSQL 14+
- Redis 6+
- NATS Server
- Docker 20.10+
- Docker Compose 2.0+
- Nginx 1.18+

## Deployment Steps

### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.8 python3.8-venv python3.8-dev \
    postgresql-14 postgresql-client-14 \
    redis-server nginx

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.0.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Application Setup
```bash
# Clone repository
git clone https://github.com/your-org/opmas.git
cd opmas/management_api

# Create virtual environment
python3.8 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
```bash
# Create production configuration
cp .env.example .env.prod

# Edit configuration
nano .env.prod

# Required settings
DATABASE_URL=postgresql://user:password@localhost:5432/opmas
REDIS_URL=redis://localhost:6379/0
NATS_URL=nats://localhost:4222
JWT_SECRET=your-secure-secret
API_HOST=0.0.0.0
API_PORT=8001
```

### 4. Database Setup
```bash
# Create database
sudo -u postgres createdb opmas

# Run migrations
alembic upgrade head

# Create initial user
python scripts/create_admin.py
```

### 5. Service Configuration

#### Nginx Configuration
```nginx
# /etc/nginx/sites-available/opmas
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Systemd Service
```ini
# /etc/systemd/system/opmas-api.service
[Unit]
Description=OPMAS Management API
After=network.target postgresql.service redis.service

[Service]
User=opmas
Group=opmas
WorkingDirectory=/opt/opmas/management_api
Environment="PATH=/opt/opmas/management_api/venv/bin"
ExecStart=/opt/opmas/management_api/venv/bin/uvicorn opmas_mgmt_api.main:app --host 0.0.0.0 --port 8001 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

### 6. Security Setup

#### SSL/TLS Configuration
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.example.com
```

#### Firewall Configuration
```bash
# Configure UFW
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8001/tcp
sudo ufw enable
```

### 7. Monitoring Setup

#### Prometheus Configuration
```yaml
# /etc/prometheus/prometheus.yml
scrape_configs:
  - job_name: 'opmas-api'
    static_configs:
      - targets: ['localhost:8001']
```

#### Grafana Dashboard
- Import dashboard from `deployment/grafana/dashboard.json`
- Configure data source
- Set up alerts

### 8. Backup Configuration

#### Database Backup
```bash
# Create backup script
cat > /opt/opmas/scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/opmas/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump -U opmas -d opmas > "$BACKUP_DIR/opmas_$TIMESTAMP.sql"
find "$BACKUP_DIR" -type f -mtime +7 -delete
EOF

# Make executable
chmod +x /opt/opmas/scripts/backup.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 0 * * * /opt/opmas/scripts/backup.sh") | crontab -
```

## Deployment Verification

### 1. Health Checks
```bash
# Check API health
curl https://api.example.com/health

# Check database connection
psql -h localhost -U opmas -d opmas -c "SELECT 1"

# Check Redis connection
redis-cli ping

# Check NATS connection
nats-pub test "Hello World"
```

### 2. Performance Testing
```bash
# Run load test
locust -f tests/performance/locustfile.py --host=https://api.example.com
```

### 3. Security Testing
```bash
# Run security scan
zap-cli quick-scan --self-contained --start-options "-config api.disablekey=true" https://api.example.com
```

## Maintenance Procedures

### 1. Updates
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Restart service
sudo systemctl restart opmas-api
```

### 2. Monitoring
- Check system metrics
- Review application logs
- Monitor error rates
- Track performance

### 3. Backup Verification
```bash
# Verify backup
pg_restore -l /opt/opmas/backups/latest.sql

# Test restore
pg_restore -U opmas -d opmas_test /opt/opmas/backups/latest.sql
```

## Troubleshooting

### Common Issues
1. Database connection failures
2. Service startup issues
3. Performance problems
4. Security incidents

### Recovery Procedures
1. Service restart
2. Database recovery
3. Configuration fixes
4. Security remediation

## Support Resources

### Documentation
- [API Documentation](../api/overview.md)
- [Development Guide](../development/setup.md)
- [Troubleshooting Guide](../maintenance/troubleshooting.md)

### Contact
- Technical Support: support@example.com
- Emergency Contact: emergency@example.com
- Security Team: security@example.com 