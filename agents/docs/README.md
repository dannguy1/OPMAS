# OPMAS Agent Documentation

Welcome to the OPMAS agent documentation. This documentation provides comprehensive information about the OPMAS agent system, its architecture, API, and usage.

## Documentation Structure

- [Design](design/agent_architecture.md) - System architecture and design decisions
- [Agent Package Structure](design/agent_package_structure.md) - How to create and structure agent packages
- [API Reference](api/agent_api.md) - Detailed API documentation
- [Examples](examples/quickstart.md) - Quickstart guide and examples

## Quick Links

- [Quickstart Guide](examples/quickstart.md)
- [Agent Architecture](design/agent_architecture.md)
- [Agent Package Structure](design/agent_package_structure.md)
- [API Reference](api/agent_api.md)

## Getting Started

1. Install the package:
```bash
pip install opmas_agents
```

2. Create a basic configuration:
```yaml
common:
  log_level: INFO
  heartbeat_interval: 30
  metrics_interval: 60

security:
  agent_id: security-001
  name: SecurityAgent
  type: security
  version: 1.0.0
```

3. Run an agent:
```python
from opmas.agents.security.security_agent import SecurityAgent

agent = SecurityAgent("security-001", config)
await agent.start()
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For support, please:
1. Check the documentation
2. Search existing issues
3. Create a new issue if needed

## License

This project is licensed under the MIT License - see the LICENSE file for details. 