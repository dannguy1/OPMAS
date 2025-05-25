# Docker Development Environment Setup

This guide will help you set up the OPMAS Management API development environment using Docker.

## Prerequisites

- Docker Engine (version 20.10.0 or later)
- Docker Compose (version 2.0.0 or later)
- Git

## Container Networking

All services run in containers and communicate through the `opmas-network` Docker network:

1. **Service Discovery**:
   - Services can communicate using their service names as hostnames
   - Example: `db:5432` resolves to the PostgreSQL container
   - Example: `nats:4222` resolves to the NATS container

2. **Port Mappings**:
   - `"host_port:container_port"` format
   - Host ports are for accessing services from your machine
   - Container ports are for internal container communication
   - Services within the Docker network use container ports

3. **Connection Examples**:
   - From API container to PostgreSQL: `db:5432`
   - From your machine to PostgreSQL: `localhost:5432`
   - From pgAdmin container to PostgreSQL: `db:5432`

## Setup Steps

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd opmas/management_api
   ```

2. **Environment Configuration**
   Create a `.env` file in the `management_api` directory:
   ```bash
   # Database - uses 'db' as hostname within Docker network
   DATABASE_URL=postgresql://postgres:postgres@db:5432/opmas

   # NATS - uses 'nats' as hostname within Docker network
   NATS_URL=nats://nats:4222

   # JWT
   JWT_SECRET_KEY=your-secret-key-here
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   ```

3. **Start the Services**
   ```bash
   docker-compose up -d
   ```
   This will start:
   - Management API (port 8000)
   - PostgreSQL database (port 5432)
   - NATS server (ports 4222, 8222)
   - pgAdmin (port 5050)

4. **Verify the Setup**
   - API Health Check: http://localhost:8000/health
   - API Documentation: http://localhost:8000/docs
   - pgAdmin: http://localhost:5050

## Development Workflow

1. **Running Tests**
   ```bash
   docker-compose exec api pytest
   ```

2. **Database Migrations**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

3. **Viewing Logs**
   ```bash
   docker-compose logs -f api
   ```

4. **Accessing Services**
   - PostgreSQL:
     ```bash
     # From host machine
     psql -h localhost -p 5432 -U postgres -d opmas

     # From within Docker network
     docker-compose exec db psql -U postgres -d opmas
     ```
   - NATS Monitoring:
     ```bash
     docker-compose exec nats nats-server --help
     ```

## Common Issues

1. **Port Conflicts**
   If you see port conflicts, check if any services are already running on the required ports:
   - 8000 (API)
   - 5432 (PostgreSQL)
   - 4222, 8222 (NATS)
   - 5050 (pgAdmin)

   Note: If you have a local PostgreSQL instance running on port 5432, you can:
   - Stop the local PostgreSQL service
   - Or modify the port mapping in docker-compose.yml to use a different host port

2. **Database Connection Issues**
   - Ensure the database container is running: `docker-compose ps`
   - Check database logs: `docker-compose logs db`
   - Verify database connection string in `.env`
   - Remember: The database is accessible on port 5432 from both:
     - Inside Docker containers (using hostname `db`)
     - Host machine (using `localhost`)

3. **NATS Connection Issues**
   - Check NATS container status: `docker-compose ps nats`
   - View NATS logs: `docker-compose logs nats`
   - Verify NATS URL in `.env`

## Development Tips

1. **Hot Reloading**
   The API service is configured with hot reloading. Changes to the source code will automatically restart the service.

2. **Database Management**
   - Use pgAdmin (http://localhost:5050) for database management
   - Default credentials:
     - Email: admin@opmas.com
     - Password: admin
   - When connecting to PostgreSQL from pgAdmin, use:
     - Host: db (when connecting from within Docker network)
     - Port: 5432
     - Database: opmas
     - Username: postgres
     - Password: postgres

3. **API Testing**
   - Use the Swagger UI (http://localhost:8000/docs) for API testing
   - Generate a JWT token using the `/api/v1/auth/token` endpoint

4. **WebSocket Testing**
   - Use a WebSocket client (e.g., wscat) to test WebSocket connections:
     ```bash
     wscat -c "ws://localhost:8000/api/v1/ws/devices?token=your-jwt-token"
     ```

## Cleanup

1. **Stop Services**
   ```bash
   docker-compose down
   ```

2. **Remove Volumes**
   ```bash
   docker-compose down -v
   ```

3. **Remove Images**
   ```bash
   docker-compose down --rmi all
   ```

## Security Notes

1. **Development Environment**
   - The provided configuration is for development only
   - Do not use default credentials in production
   - Change the JWT secret key in production

2. **Database**
   - Change default PostgreSQL credentials in production
   - Use strong passwords
   - Consider using secrets management

3. **NATS**
   - Configure authentication for NATS in production
   - Use TLS for NATS connections in production

## Next Steps

1. Review the [API Documentation](../api/README.md)
2. Check the [WebSocket Documentation](../api/websocket.md)
3. Read the [Contribution Guide](../development/contributing.md)
