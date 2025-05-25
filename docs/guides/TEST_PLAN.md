# OPMAS Test Plan

## 1. Test Scope and Objectives

### 1.1 Core Backend Testing
- Database models and migrations
- Log ingestion and parsing
- Agent implementations
- Orchestrator logic
- Message bus integration
- Error handling and recovery
- Rule evaluation
- State management
- Message handling

### 1.2 Management API Testing
- Authentication and authorization
- CRUD operations
- API endpoints
- Input validation
- Error handling
- Rate limiting
- Database operations
- External service integration

### 1.3 Frontend Testing
- Component rendering
- State management
- API integration
- User interactions
- Error handling
- Responsive design
- Layout verification
- Accessibility testing
- Cross-browser compatibility

## 2. Test Types and Implementation

### 2.1 Unit Testing
- **Tools:**
  - Python: pytest
  - JavaScript: Jest
  - Coverage: pytest-cov, Jest coverage
- **Requirements:**
  - Minimum 80% code coverage
  - All critical paths tested
  - Edge cases covered

```python
# Example: Core Backend Unit Test
def test_log_parser():
    parser = LogParser()
    log_entry = "Apr 18 15:02:17 OpenWRT-Router1 hostapd: wlan0: STA authenticated"
    result = parser.parse(log_entry)
    assert result.event_type == "wifi"
    assert result.device_hostname == "OpenWRT-Router1"
    assert result.process_name == "hostapd"

# Example: Management API Unit Test
def test_agent_creation():
    agent_data = {
        "name": "test-agent",
        "type": "wifi",
        "status": "active"
    }
    agent = create_agent(agent_data)
    assert agent.name == "test-agent"
    assert agent.type == "wifi"
```

### 2.2 Integration Testing
- **Tools:**
  - pytest with fixtures
  - Postman/Newman
  - Database test containers
- **Requirements:**
  - All API endpoints tested
  - Database operations verified
  - Error handling validated

```python
# Example: Core-Mgmt API Integration
def test_agent_management_flow():
    # Create agent through management API
    agent = create_agent_via_api(agent_data)

    # Verify agent is registered in core backend
    core_agent = get_agent_from_core(agent.id)
    assert core_agent.status == "active"

    # Test agent operations
    result = execute_agent_operation(agent.id)
    assert result.success == True
```

### 2.3 End-to-End Testing
- **Tools:**
  - Cypress
  - Selenium
  - Playwright
- **Requirements:**
  - Critical user journeys
  - Cross-browser testing
  - Mobile responsiveness

```python
# Example: Complete System Test
def test_log_processing_workflow():
    # Send test log
    send_test_log(log_data)

    # Verify log parsing
    parsed_log = get_parsed_log()
    assert parsed_log is not None

    # Verify agent processing
    finding = get_agent_finding()
    assert finding.severity == "warning"

    # Verify action execution
    action = get_executed_action()
    assert action.status == "completed"
```

### 2.4 Performance Testing
- **Tools:**
  - k6
  - Locust
  - JMeter
- **Requirements:**
  - Response time targets
  - Throughput requirements
  - Resource utilization

```python
# Example: Load Test
def test_system_load():
    # Simulate multiple devices
    for i in range(100):
        send_log_from_device(f"device-{i}")

    # Measure processing time
    processing_time = measure_processing_time()
    assert processing_time < 5.0  # seconds

    # Verify system stability
    system_metrics = get_system_metrics()
    assert system_metrics.cpu_usage < 80
    assert system_metrics.memory_usage < 80
```

## 3. Test Environment Setup

### 3.1 Environment Configuration
- **Development:**
  - Local Docker containers
  - Mock services
  - Test databases
- **Staging:**
  - Production-like setup
  - Isolated network
  - Test data

### 3.2 Test Database
```python
# conftest.py
@pytest.fixture(scope="session")
def test_db():
    # Create test database
    db = create_test_database()
    yield db
    # Cleanup
    db.drop_all()

@pytest.fixture(scope="function")
def db_session(test_db):
    # Create session
    session = test_db.create_session()
    yield session
    # Rollback changes
    session.rollback()
```

### 3.3 Mock Services
```python
# test_utils.py
class MockNATSServer:
    def __init__(self):
        self.messages = []

    def publish(self, subject, message):
        self.messages.append((subject, message))

    def subscribe(self, subject, callback):
        pass

@pytest.fixture
def mock_nats():
    return MockNATSServer()
```

### 3.4 Test Data Management
- **Data Generation:**
  - Factory patterns
  - Faker library
  - Custom generators
- **Data Cleanup:**
  - Automatic cleanup
  - Database resets
  - State management

```python
# test_data.py
def generate_test_logs(count=100):
    logs = []
    for i in range(count):
        log = {
            "timestamp": datetime.now(),
            "device": f"device-{i}",
            "message": f"Test log {i}"
        }
        logs.append(log)
    return logs
```

## 4. Test Execution and Reporting

### 4.1 Test Execution
- **Automated Tests:**
  - CI/CD pipeline
  - Scheduled runs
  - On-demand execution
- **Manual Tests:**
  - Exploratory testing
  - Usability testing
  - Security testing

```bash
# Run all tests
pytest

# Run specific test types
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=src tests/
```

### 4.2 Test Reporting
- **Metrics:**
  - Test coverage
  - Pass/fail rates
  - Performance metrics
- **Documentation:**
  - Test results
  - Bug reports
  - Improvement suggestions

```python
# pytest.ini
[pytest]
addopts = --html=report.html --self-contained-html
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

## 5. Test Maintenance

### 5.1 Code Review Checklist
- [ ] Test coverage meets requirements (>80%)
- [ ] Tests are independent and isolated
- [ ] Test data is properly managed
- [ ] Error cases are covered
- [ ] Performance requirements are tested
- [ ] Security requirements are tested
- [ ] Test reliability
- [ ] Test maintainability
- [ ] Test efficiency

### 5.2 Test Documentation
- Test case descriptions
- Test data requirements
- Environment setup instructions
- Known limitations
- Troubleshooting guide
- Best practices
- Training materials

## 6. Success Criteria

### 6.1 Coverage Requirements
- Unit tests: >80% coverage
- Integration tests: All critical paths
- E2E tests: All user workflows
- Performance tests: All SLAs met

### 6.2 Quality Gates
- All tests passing
- No critical security issues
- Performance requirements met
- Documentation complete
- Code quality metrics met
- Test quality metrics met

## 7. Security Testing

### 7.1 Vulnerability Testing
- **Tools:**
  - OWASP ZAP
  - SonarQube
  - Dependency scanners
- **Scope:**
  - API security
  - Authentication
  - Authorization

### 7.2 Penetration Testing
- **Scope:**
  - External access
  - Internal access
  - API endpoints
- **Frequency:**
  - Quarterly
  - After major changes
  - On demand

## 8. Next Steps

1. Implement missing test cases
2. Set up CI/CD pipeline
3. Configure test reporting
4. Create test data generators
5. Implement performance tests
6. Add security tests
7. Set up monitoring and alerts
8. Implement automated test maintenance
9. Create test documentation templates
10. Set up test environment automation
