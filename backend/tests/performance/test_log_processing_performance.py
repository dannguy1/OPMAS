import time
from datetime import datetime

import pytest

from opmas.core.agent import AgentManager
from opmas.core.orchestrator import Orchestrator
from opmas.core.parser import LogParser

# from opmas.models import AgentStatus, FindingSeverity


def test_log_processing_throughput(db_session, mock_nats, test_agent_data):
    """Test the throughput of log processing system."""
    # Setup components
    parser = LogParser()
    agent_manager = AgentManager(db_session)
    orchestrator = Orchestrator(db_session, mock_nats)

    # Create agent with simple rule
    agent = agent_manager.create_agent(test_agent_data)
    agent_manager.add_rule(
        agent.id,
        {
            "name": "high-cpu",
            "condition": "cpu_usage > 80",
            "action": "restart_service",
            "severity": FindingSeverity.WARNING,
        },
    )

    # Generate test logs
    num_logs = 1000
    log_entries = [
        f"Apr 18 15:02:{i:02d} OpenWRT-Router1 kernel: [12345.678] CPU temperature above threshold, cpu_usage=85"
        for i in range(num_logs)
    ]

    # Measure processing time
    start_time = time.time()

    # Process logs
    for log_entry in log_entries:
        parsed_log = parser.parse(log_entry)
        mock_nats.publish("logs.raw", parsed_log.dict())
        orchestrator.process_logs()

    end_time = time.time()
    processing_time = end_time - start_time

    # Calculate throughput
    throughput = num_logs / processing_time

    # Verify performance metrics
    assert throughput >= 100  # Minimum 100 logs per second
    assert processing_time < 10  # Maximum 10 seconds for 1000 logs

    # Verify all logs were processed
    findings = orchestrator.get_findings(agent.id)
    assert len(findings) == num_logs


def test_concurrent_agent_processing(db_session, mock_nats, test_agent_data):
    """Test concurrent processing by multiple agents."""
    # Setup components
    parser = LogParser()
    agent_manager = AgentManager(db_session)
    orchestrator = Orchestrator(db_session, mock_nats)

    # Create multiple agents
    num_agents = 10
    agents = []
    for i in range(num_agents):
        agent = agent_manager.create_agent(
            {**test_agent_data, "name": f"agent-{i}", "type": "system"}
        )
        agent_manager.add_rule(
            agent.id,
            {
                "name": f"rule-{i}",
                "condition": "cpu_usage > 80",
                "action": "restart_service",
                "severity": FindingSeverity.WARNING,
            },
        )
        agents.append(agent)

    # Generate test logs
    num_logs = 100
    log_entries = [
        f"Apr 18 15:02:{i:02d} OpenWRT-Router1 kernel: [12345.678] CPU temperature above threshold, cpu_usage=85"
        for i in range(num_logs)
    ]

    # Measure processing time
    start_time = time.time()

    # Process logs
    for log_entry in log_entries:
        parsed_log = parser.parse(log_entry)
        mock_nats.publish("logs.raw", parsed_log.dict())
        orchestrator.process_logs()

    end_time = time.time()
    processing_time = end_time - start_time

    # Calculate throughput
    throughput = (num_logs * num_agents) / processing_time

    # Verify performance metrics
    assert throughput >= 50  # Minimum 50 logs per second per agent
    assert processing_time < 20  # Maximum 20 seconds for 1000 total logs

    # Verify all agents processed their logs
    for agent in agents:
        findings = orchestrator.get_findings(agent.id)
        assert len(findings) == num_logs


def test_memory_usage(db_session, mock_nats, test_agent_data):
    """Test memory usage during log processing."""
    import os

    import psutil

    # Setup components
    parser = LogParser()
    agent_manager = AgentManager(db_session)
    orchestrator = Orchestrator(db_session, mock_nats)

    # Create agent
    agent = agent_manager.create_agent(test_agent_data)
    agent_manager.add_rule(
        agent.id,
        {
            "name": "high-cpu",
            "condition": "cpu_usage > 80",
            "action": "restart_service",
            "severity": FindingSeverity.WARNING,
        },
    )

    # Get initial memory usage
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    # Generate and process logs
    num_logs = 10000
    log_entries = [
        f"Apr 18 15:02:{i:02d} OpenWRT-Router1 kernel: [12345.678] CPU temperature above threshold, cpu_usage=85"
        for i in range(num_logs)
    ]

    for log_entry in log_entries:
        parsed_log = parser.parse(log_entry)
        mock_nats.publish("logs.raw", parsed_log.dict())
        orchestrator.process_logs()

    # Get final memory usage
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory

    # Verify memory usage
    assert memory_increase < 100 * 1024 * 1024  # Maximum 100MB increase

    # Verify all logs were processed
    findings = orchestrator.get_findings(agent.id)
    assert len(findings) == num_logs


def test_error_handling_performance(db_session, mock_nats, test_agent_data):
    """Test performance of error handling during log processing."""
    # Setup components
    parser = LogParser()
    agent_manager = AgentManager(db_session)
    orchestrator = Orchestrator(db_session, mock_nats)

    # Create agent with invalid rule
    agent = agent_manager.create_agent(test_agent_data)
    agent_manager.add_rule(
        agent.id,
        {
            "name": "invalid-rule",
            "condition": "invalid_condition",
            "action": "restart_service",
            "severity": FindingSeverity.WARNING,
        },
    )

    # Generate test logs
    num_logs = 1000
    log_entries = [
        f"Apr 18 15:02:{i:02d} OpenWRT-Router1 kernel: [12345.678] CPU temperature above threshold"
        for i in range(num_logs)
    ]

    # Measure processing time
    start_time = time.time()

    # Process logs
    for log_entry in log_entries:
        parsed_log = parser.parse(log_entry)
        mock_nats.publish("logs.raw", parsed_log.dict())
        orchestrator.process_logs()

    end_time = time.time()
    processing_time = end_time - start_time

    # Calculate throughput
    throughput = num_logs / processing_time

    # Verify performance metrics
    assert throughput >= 50  # Minimum 50 logs per second with error handling
    assert processing_time < 20  # Maximum 20 seconds for 1000 logs

    # Verify errors were logged
    errors = orchestrator.get_errors(agent.id)
    assert len(errors) == num_logs
