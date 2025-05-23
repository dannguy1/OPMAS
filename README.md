# OPMAS (Open Platform Management and Security)

OPMAS is a comprehensive platform for managing and securing network infrastructure, providing centralized control, monitoring, and automation capabilities.

## Components

- **Management API** (`/management_api`): RESTful API for system management
- **Backend Services** (`/backend`): Core services for device management and security
- **Frontend** (`/frontend`): Web interface for system administration
- **Agents** (`/agents`): Security and monitoring agents for network devices
- **Documentation** (`/docs`): System documentation and guides

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 13+
- Redis
- NATS Server
- Docker & Docker Compose

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/your-org/opmas.git
cd opmas
```

2. Set up the Management API:
```bash
cd management_api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp example.env .env
./setup.sh
```

3. Set up the Frontend:
```bash
cd frontend
npm install
cp .env.example .env
```

4. Start the development environment:
```bash
docker-compose up -d
```

## Development Workflow

1. Create a new branch for your feature:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit them:
```bash
git add .
git commit -m "Description of your changes"
```

3. Push your changes:
```bash
git push origin feature/your-feature-name
```

4. Create a Pull Request

## Project Structure

```
opmas/
├── management_api/     # Management API service
├── backend/           # Core backend services
├── frontend/          # Web interface
├── agents/            # Security and monitoring agents
├── docs/             # Documentation
└── k8s/              # Kubernetes manifests
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Your Name - your.email@example.com

Project Link: [https://github.com/your-org/opmas](https://github.com/your-org/opmas) 