**Project Title:** OpenWRT Proactive Monitoring Agentic System (OPMAS)

**Version:** 1.0

**Date:** 2024-03-20

**Goal:** Develop a modular, agent-based system to ingest and analyze logs from OpenWRT devices. The system will detect potential problems, anomalies, and security issues, enabling preventive actions and improving device stability and security. The initial implementation will focus on a rule-based approach within agents, with the architecture allowing for future integration of AI/ML models.

**Target Platform:** OpenWRT devices (various versions, focus on recent releases). Log analysis and agent orchestration will primarily run on a central server/platform, not directly on resource-constrained OpenWRT devices (except for log forwarding).

---

**1\. Core Architecture**

The system employs a multi-agent architecture composed of the following core components communicating primarily via a Message Queue:

* **Log Forwarder (on OpenWRT):** Configures OpenWRT's syslog daemon to forward logs. (Configuration task, not a custom component to build initially).  
* **Log Ingestor:** Receives forwarded logs.  
* **Log Parser:** Structures the raw log messages.  
* **Message Queue (MQ):** Facilitates communication between components using topic-based publish/subscribe.  
* **Domain Agents (run centrally):** Specialized agents subscribing to relevant parsed logs.  
  * Wi-Fi Agent (AgentType.WIFI)
  * Network Security Agent (AgentType.SECURITY)
  * Device Health Agent (AgentType.HEALTH)
  * WAN/Connectivity Agent (AgentType.WAN)
* **Orchestrator Agent (run centrally):** Correlates findings from Domain Agents and decides on actions.  
* **Knowledge Base (KB):** Stores configurations, rules, state, and action playbooks. Accessed by Orchestrator and Agents.  
* **Action Executor (run centrally):** Executes commands securely on target OpenWRT devices.  
* **(Future)** Monitoring & UI: Interface for viewing status, alerts, and managing the system. (Out of scope for initial core implementation).

**High-Level Data Flow:**

1. OpenWRT Device syslog → (Network Syslog) → Log Ingestor  
2. Log Ingestor → (Raw Log + Metadata) → Log Parser  
3. Log Parser → (Structured Log JSON) → Message Queue (topic: logs.parsed.raw)  
4. Message Queue → (Filtered Structured Logs) → Relevant Domain Agent(s) (e.g., topic logs.wifi, logs.security)  
5. Domain Agent → (Finding JSON) → Message Queue (topic: findings.<domain>)  
6. Message Queue → (Finding JSON) → Orchestrator Agent  
7. Orchestrator Agent → (Queries/Reads) → Knowledge Base  
8. Orchestrator Agent → (Action Command JSON) → Message Queue (topic: actions.execute)  
9. Message Queue → (Action Command JSON) → Action Executor  
10. Action Executor → (SSH Command) → OpenWRT Device  
11. Action Executor → (Action Result JSON) → Message Queue (topic: actions.results)  
12. Message Queue → (Action Result JSON) → Orchestrator Agent (for logging/state update)

---

**2\. Component Specifications**

**2.1. Database Models**

* **Purpose:** Define data structures and relationships
* **Implementation:**
  * Base model with TimestampMixin for created_at/updated_at
  * LogEntry model for log storage
  * Agent model with type and status enums
  * Relationships and indexes for efficient querying
  * Comprehensive test suite

**2.2. Log Forwarder (Configuration)**

* **Purpose:** Ensure logs from OpenWRT are sent to the central Log Ingestor.  
* **Implementation:** Configure the standard OpenWRT syslog facility (logd or syslog-ng).  
  * Set remote server IP/hostname (Log Ingestor address).  
  * Set remote server port (e.g., UDP/514 or TCP/514 - TCP preferred for reliability if supported, potentially with TLS).  
  * Ensure relevant logs (logd, dmesg, hostapd, firewall, etc.) are captured by syslog.  
* **Output:** Syslog messages (RFC 3164 or RFC 5424 format) sent over the network.

**2.3. Log Ingestor**

* **Purpose:** Listen for incoming syslog messages, timestamp them upon arrival, add source IP metadata, and pass them to the parser.  
* **Input:** Syslog messages via network (UDP or TCP socket).  
* **Output:** Raw log message string + metadata (arrival timestamp, source IP) sent to Log Parser (e.g., via direct function call or internal queue).  
* **Core Logic:**  
  * Bind to the configured network port(s) (UDP/TCP).  
  * Receive syslog messages.  
  * Record arrival timestamp (UTC).  
  * Identify source IP address of the message.  
  * Forward data immediately to the Log Parser component.  
  * Handle potential connection issues (for TCP).  
* **Interface:** Network socket listener.

**2.4. Log Parser**

* **Purpose:** Parse raw log messages into a structured JSON format. Enrich with hostname if possible. Route to appropriate MQ topic.  
* **Input:** Raw log string + metadata (arrival timestamp, source IP) from Log Ingestor.  
* **Output:** Structured JSON log event published to Message Queue on relevant topics.  
* **Core Logic:**  
  * Use regular expressions and potentially known format definitions (e.g., for hostapd, iptables) to parse the raw message.  
  * Extract key fields: original timestamp, hostname (if present), process name, PID, log level (if discernible), core message content.  
  * Attempt to identify the log source type (e.g., 'system', 'kernel', 'wifi', 'firewall', 'dhcp').  
  * Construct a standard JSON object (See Section 3.1).  
  * Publish the JSON object to a general topic (e.g., logs.parsed.raw) AND a specific topic based on source type (e.g., logs.wifi, logs.security). *Initial routing can be simple based on process name*.  
* **Interface:** Receives data from Ingestor, publishes to MQ.

**2.5. Message Queue (MQ)**

* **Purpose:** Decouple components, enable pub/sub communication.  
* **Implementation:** Choose a suitable MQ system (e.g., NATS, Redis Streams, RabbitMQ). Must support topic-based routing.  
* **Topics (Initial):**  
  * logs.parsed.raw (All structured logs)  
  * logs.wifi (Parsed logs likely from hostapd, wireless drivers)  
  * logs.security (Parsed logs likely from firewall, dropbear, auth)  
  * logs.health (Parsed logs likely from kernel, system)  
  * logs.connectivity (Parsed logs likely from netifd, ppp, dhcp client)  
  * findings.<domain> (e.g., findings.wifi, findings.security) - Output from Domain Agents  
  * actions.execute - Commands for the Action Executor  
  * actions.results - Results from the Action Executor  
* **Interface:** Provide standard client libraries for publishers and subscribers.

**2.6. Domain Agents (General)**

* **Purpose:** Subscribe to relevant log topics, analyze logs according to domain logic, detect anomalies/patterns, and publish findings.  
* **Input:** Structured JSON log events from MQ. Potentially query KB or request data via Action Executor.  
* **Output:** Structured JSON 'Finding' events to MQ (topic: findings.<domain>).  
* **Core Logic:**  
  * Maintain internal state relevant to detection logic (e.g., recent failure counts, connection states).  
  * Apply rules/heuristics to incoming logs and internal state.  
  * *Initial Implementation:* Focus on rule-based logic (thresholds, sequence detection, specific error matching). Define interfaces where ML models could be added later.  
  * Generate 'Finding' JSON (See Section 3.2) when a pattern/anomaly is detected. Include severity, details, and potentially references to triggering log events.

**2.6.1. Wi-Fi Agent**

* **Subscribes to:** logs.wifi  
* **Detection Logic (Rule-based examples):**  
  * High authentication failure rate for a specific client MAC or overall (e.g., > N failures in M seconds).  
  * Excessive deauthentication/disassociation events (flooding detection).  
  * Frequent DFS radar detection events on a specific channel.  
  * Logs indicating kernel driver crashes or errors related to Wi-Fi interfaces.  
  * Reports of very low signal strength (if available in logs).  
* **Publishes to:** findings.wifi

**2.6.2. Network Security Agent**

* **Subscribes to:** logs.security  
* **Detection Logic (Rule-based examples):**  
  * Repeated failed login attempts (SSH/HTTP/LuCI) from the same source IP (brute-force detection).  
  * Firewall logs showing excessive connection drops/rejects from a single source IP (port scan detection).  
  * Firewall logs showing denied outbound connections to known malicious IPs/domains (requires external feed integration via KB/Orchestrator later).  
  * DHCP server logs indicating lease pool exhaustion.  
  * Unexpected changes in firewall rules (if logged).  
* **Publishes to:** findings.security

**2.6.3. Device Health Agent**

* **Subscribes to:** logs.health  
* **Detection Logic (Rule-based examples):**  
  * Kernel messages indicating OOM (Out Of Memory) kills.  
  * Filesystem errors (JFFS2/UBIFS warnings/errors).  
  * Logs indicating unexpected reboots (detecting boot sequences without corresponding shutdown logs).  
  * High temperature warnings (if sensors and logging exist).  
  * CPU usage warnings (if specific processes log high usage or if obtainable via periodic checks - requires Action Executor).  
* **Publishes to:** findings.health

**2.6.4. WAN/Connectivity Agent**

* **Subscribes to:** logs.connectivity  
* **Detection Logic (Rule-based examples):**  
  * Frequent WAN interface up/down events (flapping).  
  * DHCP client failures (unable to obtain lease, NAKs).  
  * PPP connection failures (authentication errors, timeouts).  
  * Logs indicating DNS resolution failures.  
  * (Future: Could trigger periodic pings/probes via Action Executor and analyze results).  
* **Publishes to:** findings.connectivity

**2.7. Orchestrator Agent**

* **Purpose:** Consume findings from all domain agents, correlate them, consult the KB for rules/playbooks, decide on appropriate preventive/diagnostic actions, and dispatch action commands.  
* **Input:** Finding JSON messages from MQ (subscribes to findings.*). Action Result JSON from MQ (subscribes to actions.results).  
* **Output:** Action Command JSON to MQ (topic: actions.execute). Logs/updates to KB. Potential alerts to external systems (future).  
* **Core Logic:**  
  * Maintain state about ongoing issues per device.  
  * Receive findings and correlate them (e.g., finding A + finding B within time T might indicate root cause C). *Initial correlation rules can be simple, defined in KB.*  
  * Consult KB:  
    * Check device configuration/context.  
    * Look up 'playbooks' associated with specific findings or correlated events. Playbooks define potential actions.  
    * Check cooldown periods for actions to avoid flapping/loops.  
  * Decision Engine:  
    * Prioritize findings based on severity.  
    * Select appropriate action(s) based on playbook and current state. Actions can be diagnostic (e.g., "get CPU usage") or preventive (e.g., "restart wifi", "block IP").  
    * *Initial actions should be non-disruptive diagnostics or very safe preventive steps.*  
  * Dispatch selected actions by publishing Action Command JSON (See Section 3.3) to MQ.  
  * Log decisions and received action results. Update device state in KB.  
* **Interface:** MQ subscriber/publisher, KB reader/writer.

**2.8. Knowledge Base (KB)**

* **Purpose:** Store configuration, rules, state, and playbooks needed by the system.  
* **Implementation:** Start simple. Can be a combination of:  
  * **Configuration Files (YAML/JSON):** For agent rules (thresholds, patterns), correlation rules, action playbooks.  
  * **Database (PostgreSQL):** For device inventory (IP, hostname, model, SSH keys/creds), dynamic device state (ongoing issues, last action times), historical findings/actions log.  
* **Interface:** Provide functions/APIs for agents (read-only for rules) and orchestrator (read/write) to access data.

**2.9. Action Executor**

* **Purpose:** Securely execute commands on target OpenWRT devices based on commands received from the Orchestrator.  
* **Input:** Action Command JSON from MQ (subscribes to actions.execute).  
* **Output:** Action Result JSON to MQ (topic: actions.results).  
* **Core Logic:**  
  * Receive Action Command.  
  * Validate the command (allowed commands, target device exists in KB).  
  * Retrieve credentials/keys for the target device from KB (securely!).  
  * Connect to the device using **SSH**.  
  * Execute the specified command (e.g., logread -l 10, uci show wifi-iface, iptables -I INPUT ..., /etc/init.d/network restart). **Crucially, sanitize inputs and restrict allowed commands.**  
  * Capture command output (stdout, stderr) and exit code.  
  * Disconnect SSH session.  
  * Publish Action Result JSON (See Section 3.4) indicating success/failure and including output.  
* **Interface:** MQ subscriber/publisher, KB reader, SSH client.

---

**3\. Data Formats (JSON)**

*(Define clear JSON schemas)*

**3.1. Parsed Log Event (Example)**

```json
{
  "event_id": "uuid-...",
  "arrival_ts_utc": "2025-04-18T22:02:18.123Z",
  "source_ip": "192.168.1.1",
  "original_ts": "Apr 18 15:02:17",
  "hostname": "OpenWRT-Router1",
  "process_name": "hostapd",
  "pid": "1234",
  "log_level": "INFO",
  "message": "wlan0: STA aa:bb:cc:dd:ee:ff IEEE 802.11: authenticated",
  "parser_name": "hostapd_parser_v1",
  "log_source_type": "wifi",
  "structured_fields": {
    "interface": "wlan0",
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "event": "auth_success"
  }
}
```

**3.2. Agent Finding (Example)**

```json
{
  "finding_id": "uuid-...",
  "agent_name": "WiFiAgent",
  "finding_ts_utc": "2025-04-18T22:05:00.000Z",
  "device_hostname": "OpenWRT-Router1",
  "device_ip": "192.168.1.1",
  "severity": "Warning",
  "finding_type": "HighAuthFailureRate",
  "description": "High rate of authentication failures for client aa:bb:cc:dd:ee:ff on wlan0",
  "details": {
    "interface": "wlan0",
    "client_mac": "aa:bb:cc:dd:ee:ff",
    "failure_count": 25,
    "time_window_seconds": 60
  },
  "evidence_event_ids": ["uuid-...", "uuid-..."]
}
```

**3.3. Action Command (Example)**

```json
{
  "action_id": "uuid-...",
  "command_ts_utc": "2025-04-18T22:10:00.000Z",
  "device_hostname": "OpenWRT-Router1",
  "device_ip": "192.168.1.1",
  "action_type": "run_command",
  "command": "hostapd_cli -i wlan0 list_sta",
  "timeout_seconds": 30,
  "retry_count": 3,
  "retry_delay_seconds": 5
}
```

**3.4. Action Result (Example)**

```json
{
  "action_id": "uuid-...",
  "result_ts_utc": "2025-04-18T22:10:05.000Z",
  "device_hostname": "OpenWRT-Router1",
  "device_ip": "192.168.1.1",
  "status": "success",
  "exit_code": 0,
  "stdout": "Connected to hostapd interface 'wlan0'\n...",
  "stderr": "",
  "execution_time_ms": 120
}
```

---

**4\. Testing Framework**

**4.1. Test Configuration**

* Database fixtures
  * Test database engine
  * Session management
  * Transaction handling
* Test data fixtures
  * Test agent
  * Test log entry
* Configuration fixtures
  * Database config
  * Logging config

**4.2. Test Structure**

* Unit tests for models
* Integration tests for workflows
* Performance tests
* Security tests

---

**5\. Implementation Status**

**5.1. Completed Components**

* Database Models
  * Base model with TimestampMixin
  * LogEntry model
  * Agent model with enums
  * Test suite

**5.2. In Progress**

* Testing Framework
  * Test database configuration
  * Test fixtures
  * Basic model tests

**5.3. Pending**

* Log Ingestion API
* Log Parser
* Domain Agents
* Orchestrator
* Action Executor

---

**6\. Next Steps**

1. Complete Testing Framework
   * Add more test utilities
   * Configure coverage reporting
   * Create integration tests
   * Set up CI/CD pipeline

2. Implement Log Ingestion API
   * Set up FastAPI application
   * Implement syslog server
   * Add log validation
   * Configure NATS integration

3. Develop Log Parser
   * Create parsing rules
   * Implement structured log extraction
   * Set up log classification
   * Add log enrichment

4. Build Domain Agents
   * Create base agent class
   * Implement specialized agents
   * Add rule-based analysis
   * Set up NATS integration

5. Create Orchestrator
   * Implement rule evaluation
   * Add playbook management
   * Set up action planning
   * Create state management

6. Develop Action Executor
   * Set up SSH connection management
   * Implement command execution
   * Add result handling
   * Create retry mechanisms

---

## Related Documents

- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md): System architecture overview
- [DEVELOPMENT_SETUP.md](../guides/DEVELOPMENT_SETUP.md): Development environment setup
- [API_DOCUMENTATION.md](../api/API_DOCUMENTATION.md): API reference

---

This specification provides a detailed blueprint. The AI Coder should focus on implementing the core components, communication flow via the MQ, and the initial rule-based logic for agents and the orchestrator, ensuring the architecture is modular and ready for future AI enhancements.