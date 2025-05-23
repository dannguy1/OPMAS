# OPMAS Management API

The Management API for the Open Platform Management and Security (OPMAS) system. This API provides a centralized interface for managing security agents, devices, rules, and automation workflows.

## Features

- Device Management
- Agent Management
- Security Rules
- Automation Playbooks
- User Authentication & Authorization
- Real-time Monitoring
- API Documentation

## Prerequisites

- Python 3.10+
- PostgreSQL 13+
- Redis
- NATS Server

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/opmas.git
cd opmas/management_api
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp example.env .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
./setup.sh
```

## Development

1. Start the development server:
```bash
python run.py
```

2. Run tests:
```bash
pytest
```

3. Run linting:
```bash
flake8
black .
```

## Project Structure

```
management_api/
├── src/
│   └── opmas_mgmt_api/
│       ├── models/         # Database models
│       ├── api/           # API endpoints
│       ├── core/          # Core functionality
│       └── utils/         # Utility functions
├── tests/                 # Test suite
├── alembic/              # Database migrations
├── docs/                 # Documentation
└── k8s/                  # Kubernetes manifests
```

## API Documentation

API documentation is available at `/docs` when running the server.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Your Name - your.email@example.com

Project Link: [https://github.com/your-org/opmas](https://github.com/your-org/opmas)
