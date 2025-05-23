# OPMAS Deployment Architecture

## Development Environment

```mermaid
graph TB
    subgraph "Development Machine"
        subgraph "Docker Containers"
            Core[Core Backend]
            MgmtAPI[Management API]
            Frontend[Frontend UI]
            NATS[NATS Server]
            Postgres[PostgreSQL]
            TestDB[Test Database]
        end

        subgraph "Development Tools"
            IDE[VS Code]
            Git[Git]
            Docker[Docker]
            Node[Node.js]
            Python[Python]
            Pytest[Pytest]
        end
    end

    subgraph "Test Devices"
        Device1[OpenWRT Device 1]
        Device2[OpenWRT Device 2]
    end

    Core -->|HTTP| Device1
    Core -->|HTTP| Device2
    Core -->|Pub/Sub| NATS
    Core -->|DB| Postgres
    Core -->|Test| TestDB
    MgmtAPI -->|DB| Postgres
    Frontend -->|HTTP| MgmtAPI
    Pytest -->|Test| Core
    Pytest -->|Test| MgmtAPI
    Pytest -->|Test| Frontend

    classDef container fill:#bbf,stroke:#333,stroke-width:2px
    classDef tool fill:#bfb,stroke:#333,stroke-width:2px
    classDef device fill:#f9f,stroke:#333,stroke-width:2px
    classDef test fill:#fbf,stroke:#333,stroke-width:2px

    class Core,MgmtAPI,Frontend,NATS,Postgres container
    class IDE,Git,Docker,Node,Python tool
    class Device1,Device2 device
    class TestDB,Pytest test
```

## Production Environment

```mermaid
graph TB
    subgraph "Production Server"
        subgraph "Docker Swarm/Kubernetes"
            subgraph "Core Services"
                Core1[Core Backend 1]
                Core2[Core Backend 2]
                CoreN[Core Backend N]
            end

            subgraph "API Services"
                MgmtAPI1[Management API 1]
                MgmtAPI2[Management API 2]
            end

            subgraph "Frontend Services"
                Frontend1[Frontend UI 1]
                Frontend2[Frontend UI 2]
            end

            subgraph "Infrastructure"
                NATS[NATS Cluster]
                Postgres[PostgreSQL Cluster]
                Redis[Redis Cache]
                Nginx[Nginx Load Balancer]
            end
        end
    end

    subgraph "Production Devices"
        Device1[OpenWRT Device 1]
        Device2[OpenWRT Device 2]
        DeviceN[OpenWRT Device N]
    end

    %% Core Services Connections
    Core1 -->|Pub/Sub| NATS
    Core2 -->|Pub/Sub| NATS
    CoreN -->|Pub/Sub| NATS
    Core1 -->|DB| Postgres
    Core2 -->|DB| Postgres
    CoreN -->|DB| Postgres

    %% API Services Connections
    MgmtAPI1 -->|DB| Postgres
    MgmtAPI2 -->|DB| Postgres
    MgmtAPI1 -->|Cache| Redis
    MgmtAPI2 -->|Cache| Redis

    %% Frontend Services Connections
    Frontend1 -->|HTTP| Nginx
    Frontend2 -->|HTTP| Nginx
    Nginx -->|HTTP| MgmtAPI1
    Nginx -->|HTTP| MgmtAPI2

    %% Device Connections
    Device1 -->|Syslog| Nginx
    Device2 -->|Syslog| Nginx
    DeviceN -->|Syslog| Nginx
    Nginx -->|Syslog| Core1
    Nginx -->|Syslog| Core2
    Nginx -->|Syslog| CoreN

    classDef service fill:#bbf,stroke:#333,stroke-width:2px
    classDef infra fill:#fbb,stroke:#333,stroke-width:2px
    classDef device fill:#f9f,stroke:#333,stroke-width:2px

    class Core1,Core2,CoreN,MgmtAPI1,MgmtAPI2,Frontend1,Frontend2 service
    class NATS,Postgres,Redis,Nginx infra
    class Device1,Device2,DeviceN device
```

## Deployment Configuration

### 1. Docker Compose (Development)

```yaml
version: '3.8'
services:
  core:
    build: ./core
    ports:
      - "8000:8000"
    environment:
      - NATS_URL=nats://nats:4222
      - DB_URL=postgresql://opmas:password@postgres:5432/opmas
      - TEST_DB_URL=postgresql://opmas:password@testdb:5432/opmas_test
    depends_on:
      - nats
      - postgres
      - testdb

  management_api:
    build: ./management_api
    ports:
      - "8001:8001"
    environment:
      - DB_URL=postgresql://opmas:password@postgres:5432/opmas
      - TEST_DB_URL=postgresql://opmas:password@testdb:5432/opmas_test
    depends_on:
      - postgres
      - testdb

  frontend:
    build: ./ui
    ports:
      - "3000:80"
    environment:
      - API_URL=http://localhost:8001
    depends_on:
      - management_api

  nats:
    image: nats:latest
    ports:
      - "4222:4222"

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=opmas
      - POSTGRES_USER=opmas
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  testdb:
    image: postgres:14
    environment:
      - POSTGRES_DB=opmas_test
      - POSTGRES_USER=opmas
      - POSTGRES_PASSWORD=password
    volumes:
      - testdb_data:/var/lib/postgresql/data

volumes:
  postgres_data:
  testdb_data:
```

### 2. Kubernetes (Production)

```yaml
# Core Backend Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opmas-core
spec:
  replicas: 3
  selector:
    matchLabels:
      app: opmas-core
  template:
    metadata:
      labels:
        app: opmas-core
    spec:
      containers:
      - name: core
        image: opmas/core:latest
        ports:
        - containerPort: 8000
        env:
        - name: NATS_URL
          value: nats://nats:4222
        - name: DB_URL
          valueFrom:
            secretKeyRef:
              name: opmas-secrets
              key: db-url

# Management API Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opmas-management-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: opmas-management-api
  template:
    metadata:
      labels:
        app: opmas-management-api
    spec:
      containers:
      - name: management-api
        image: opmas/management-api:latest
        ports:
        - containerPort: 8001
        env:
        - name: DB_URL
          valueFrom:
            secretKeyRef:
              name: opmas-secrets
              key: db-url

# Frontend Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opmas-frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: opmas-frontend
  template:
    metadata:
      labels:
        app: opmas-frontend
    spec:
      containers:
      - name: frontend
        image: opmas/frontend:latest
```

## Deployment Process

```mermaid
flowchart TB
    subgraph "Deployment Pipeline"
        Build[Build Images]
        Test[Run Tests]
        Push[Push to Registry]
        Deploy[Deploy to Environment]
        Verify[Verify Deployment]
    end

    subgraph "Environment"
        Dev[Development]
        Staging[Staging]
        Prod[Production]
    end

    Build -->|Success| Test
    Test -->|Success| Push
    Push -->|Success| Deploy
    Deploy -->|Success| Verify

    Deploy -->|Dev| Dev
    Deploy -->|Staging| Staging
    Deploy -->|Prod| Prod

    classDef process fill:#bbf,stroke:#333,stroke-width:2px
    classDef env fill:#bfb,stroke:#333,stroke-width:2px

    class Build,Test,Push,Deploy,Verify process
    class Dev,Staging,Prod env
```
