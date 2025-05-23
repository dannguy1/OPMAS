# OPMAS Management API Deployment Guide

## Prerequisites

- Docker 20.10+
- Kubernetes 1.20+
- Helm 3.0+
- kubectl configured with cluster access
- PostgreSQL 12+
- Redis 6+

## Deployment Steps

### 1. Build Docker Image

```bash
# Build the image
docker build -t opmas-management-api:latest .

# Tag the image for your registry
docker tag opmas-management-api:latest your-registry/opmas-management-api:latest

# Push to registry
docker push your-registry/opmas-management-api:latest
```

### 2. Configure Secrets

Create a Kubernetes secret for sensitive data:

```bash
kubectl create secret generic opmas-secrets \
  --from-literal=database-url='postgresql://user:password@postgres:5432/opmas' \
  --from-literal=jwt-secret='your-jwt-secret' \
  --from-literal=redis-url='redis://redis:6379/0'
```

### 3. Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace opmas

# Apply configurations
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/monitoring.yaml
```

### 4. Verify Deployment

```bash
# Check deployment status
kubectl get pods -n opmas

# Check service status
kubectl get svc -n opmas

# Check ingress status
kubectl get ingress -n opmas
```

## Monitoring Setup

### 1. Install Prometheus Stack

```bash
# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

### 2. Configure Grafana

1. Access Grafana dashboard:
   ```bash
   kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
   ```

2. Login with default credentials:
   - Username: admin
   - Password: prom-operator

3. Import the OPMAS dashboard:
   - Go to Dashboards > Import
   - Upload the dashboard JSON from `k8s/monitoring.yaml`

## Health Checks

The API includes the following health check endpoints:

- `/health`: Basic health check
- `/metrics`: Prometheus metrics endpoint

## Monitoring Metrics

The following metrics are collected:

### HTTP Metrics
- `http_requests_total`: Total number of HTTP requests
- `http_request_duration_seconds`: Request duration histogram

### Playbook Metrics
- `playbook_execution_total`: Total playbook executions
- `playbook_execution_duration_seconds`: Execution duration histogram
- `active_playbooks`: Number of active playbooks

### Database Metrics
- `db_operation_duration_seconds`: Database operation duration histogram

## Alerts

The following alerts are configured:

1. High Error Rate
   - Triggered when error rate exceeds 10%
   - Severity: Warning

2. High Latency
   - Triggered when 95th percentile latency exceeds 1 second
   - Severity: Warning

3. Playbook Execution Failure
   - Triggered when playbook executions fail
   - Severity: Critical

## Backup and Recovery

### Database Backup

```bash
# Create backup
kubectl exec -n opmas deploy/postgres -- pg_dump -U postgres opmas > backup.sql

# Restore from backup
kubectl exec -i -n opmas deploy/postgres -- psql -U postgres opmas < backup.sql
```

### Configuration Backup

```bash
# Backup Kubernetes resources
kubectl get all -n opmas -o yaml > k8s-backup.yaml
kubectl get configmap,secret -n opmas -o yaml > config-backup.yaml
```

## Troubleshooting

### Common Issues

1. Pod CrashLoopBackOff
   ```bash
   # Check pod logs
   kubectl logs -n opmas deploy/opmas-management-api
   
   # Check pod events
   kubectl describe pod -n opmas -l app=opmas-management-api
   ```

2. Database Connection Issues
   ```bash
   # Check database pod
   kubectl logs -n opmas deploy/postgres
   
   # Test database connection
   kubectl exec -n opmas deploy/opmas-management-api -- python -c "from opmas_mgmt_api.database import get_db; next(get_db())"
   ```

3. Monitoring Issues
   ```bash
   # Check Prometheus targets
   kubectl port-forward svc/prometheus-operated 9090:9090 -n monitoring
   # Access http://localhost:9090/targets
   
   # Check Grafana data source
   kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
   # Access http://localhost:3000/datasources
   ```

## Maintenance

### Regular Tasks

1. Update Dependencies
   ```bash
   # Update Python dependencies
   pip-compile requirements.in
   
   # Rebuild and deploy
   docker build -t opmas-management-api:latest .
   kubectl rollout restart deploy/opmas-management-api -n opmas
   ```

2. Log Rotation
   ```bash
   # Configure log rotation in Kubernetes
   kubectl apply -f k8s/logging.yaml
   ```

3. Certificate Renewal
   ```bash
   # Check certificate status
   kubectl get certificate -n opmas
   
   # Force certificate renewal
   kubectl delete secret opmas-tls -n opmas
   ```

## Security Considerations

1. Network Policies
   ```bash
   # Apply network policies
   kubectl apply -f k8s/network-policies.yaml
   ```

2. Pod Security Policies
   ```bash
   # Apply pod security policies
   kubectl apply -f k8s/pod-security-policies.yaml
   ```

3. Regular Security Updates
   ```bash
   # Update base image
   docker build --no-cache -t opmas-management-api:latest .
   
   # Deploy updates
   kubectl rollout restart deploy/opmas-management-api -n opmas
   ``` 