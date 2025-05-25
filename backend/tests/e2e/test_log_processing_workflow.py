from datetime import datetime

import pytest

from opmas.core.agent import AgentManager
from opmas.core.orchestrator import Orchestrator
from opmas.core.parser import LogParser

# from opmas.models import AgentStatus, FindingSeverity


def test_complete_log_processing_workflow(db_session, mock_nats, test_agent_data):
    """Test the complete log processing workflow from ingestion to action execution."""
    # Setup components
    parser = LogParser()
    agent_manager = AgentManager(db_session)
    orchestrator = Orchestrator(db_session, mock_nats)

    # Create and configure agent
    agent = agent_manager.create_agent(test_agent_data)
    rule = {
        "name": "high-cpu-usage",
        "condition": "cpu_usage > 80",
        "action": "restart_service",
        "severity": FindingSeverity.WARNING,
    }
    agent_manager.add_rule(agent.id, rule)

    # Simulate log ingestion
    log_entry = "Apr 18 15:02:17 OpenWRT-Router1 kernel: [12345.678] CPU temperature above threshold, cpu_usage=85"
    parsed_log = parser.parse(log_entry)

    # Publish log to NATS
    mock_nats.publish("logs.raw", parsed_log.dict())

    # Wait for processing (simulate async processing)
    orchestrator.process_logs()

    # Verify agent received and processed the log
    agent = agent_manager.get_agent(agent.id)
    assert agent.status == AgentStatus.ACTIVE

    # Verify finding was created
    findings = orchestrator.get_findings(agent.id)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.severity == FindingSeverity.WARNING
    assert finding.rule_name == "high-cpu-usage"

    # Verify action was created
    actions = orchestrator.get_actions(agent.id)
    assert len(actions) == 1
    action = actions[0]
    assert action.type == "restart_service"
    assert action.status == "pending"


def test_log_processing_with_multiple_agents(db_session, mock_nats, test_agent_data):
    """Test log processing with multiple agents and rules."""
    # Setup components
    parser = LogParser()
    agent_manager = AgentManager(db_session)
    orchestrator = Orchestrator(db_session, mock_nats)

    # Create multiple agents with different rules
    agent1 = agent_manager.create_agent({**test_agent_data, "name": "cpu-agent", "type": "system"})
    agent2 = agent_manager.create_agent(
        {**test_agent_data, "name": "network-agent", "type": "network"}
    )

    # Add rules to agents
    agent_manager.add_rule(
        agent1.id,
        {
            "name": "high-cpu",
            "condition": "cpu_usage > 80",
            "action": "restart_service",
            "severity": FindingSeverity.WARNING,
        },
    )

    agent_manager.add_rule(
        agent2.id,
        {
            "name": "network-error",
            "condition": "network_error",
            "action": "reset_interface",
            "severity": FindingSeverity.ERROR,
        },
    )

    # Simulate multiple log entries
    log_entries = [
        "Apr 18 15:02:17 OpenWRT-Router1 kernel: [12345.678] CPU temperature above threshold, cpu_usage=85",
        "Apr 18 15:02:18 OpenWRT-Router1 network: [12345.679] Network interface error on eth0",
    ]

    # Process logs
    for log_entry in log_entries:
        parsed_log = parser.parse(log_entry)
        mock_nats.publish("logs.raw", parsed_log.dict())
        orchestrator.process_logs()

    # Verify findings for both agents
    findings1 = orchestrator.get_findings(agent1.id)
    findings2 = orchestrator.get_findings(agent2.id)

    assert len(findings1) == 1
    assert len(findings2) == 1
    assert findings1[0].rule_name == "high-cpu"
    assert findings2[0].rule_name == "network-error"

    # Verify actions for both agents
    actions1 = orchestrator.get_actions(agent1.id)
    actions2 = orchestrator.get_actions(agent2.id)

    assert len(actions1) == 1
    assert len(actions2) == 1
    assert actions1[0].type == "restart_service"
    assert actions2[0].type == "reset_interface"


def test_log_processing_error_handling(db_session, mock_nats, test_agent_data):
    """Test error handling in log processing workflow."""
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
            "condition": "invalid_condition",  # Invalid condition
            "action": "restart_service",
            "severity": FindingSeverity.WARNING,
        },
    )

    # Simulate log ingestion
    log_entry = (
        "Apr 18 15:02:17 OpenWRT-Router1 kernel: [12345.678] CPU temperature above threshold"
    )
    parsed_log = parser.parse(log_entry)

    # Publish log to NATS
    mock_nats.publish("logs.raw", parsed_log.dict())

    # Process logs
    orchestrator.process_logs()

    # Verify agent status reflects error
    agent = agent_manager.get_agent(agent.id)
    assert agent.status == AgentStatus.ERROR

    # Verify error was logged
    errors = orchestrator.get_errors(agent.id)
    assert len(errors) == 1
    assert "invalid_condition" in errors[0].message
