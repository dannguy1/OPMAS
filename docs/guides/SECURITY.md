# OPMAS Security Documentation

## Overview

This document outlines the security measures and best practices implemented in the OPMAS system. It covers authentication, authorization, data protection, and secure communication protocols.

## 1. Authentication

### 1.1 JWT Authentication
- **Token Format:** JWT with RS256 algorithm
- **Token Structure:**
  ```json
  {
    "sub": "user_id",
    "exp": "expiration_timestamp",
    "iat": "issued_at_timestamp",
    "roles": ["role1", "role2"]
  }
  ```
- **Token Lifetime:**
  - Access Token: 24 hours
  - Refresh Token: 30 days
- **Token Storage:**
  - Access Token: Memory only
  - Refresh Token: Secure HTTP-only cookie

### 1.2 SSH Authentication
- **Key Types:** RSA, Ed25519
- **Key Storage:** Encrypted in database
- **Key Rotation:** Every 90 days
- **Access Control:**
  - Limited privilege users on OpenWRT devices
  - Command allowlist enforcement

## 2. Authorization

### 2.1 Role-Based Access Control (RBAC)
- **Roles:**
  - Admin: Full system access
  - Operator: Device management and monitoring
  - Viewer: Read-only access
  - Agent: System component access

### 2.2 Permission Matrix
| Role    | Devices | Agents | Rules | Playbooks | Actions | Config |
|---------|---------|--------|-------|-----------|---------|--------|
| Admin   | CRUD    | CRUD   | CRUD  | CRUD      | CRUD    | CRUD   |
| Operator| CRUD    | R      | R     | R         | CRUD    | R      |
| Viewer  | R       | R      | R     | R         | R       | R      |
| Agent   | R       | R      | R     | R         | R       | R      |

### 2.3 Resource Access Control
- **Device Access:**
  - Ownership-based access
  - Group-based access
  - IP-based restrictions
- **API Access:**
  - Rate limiting
  - IP allowlisting
  - Request validation

## 3. Data Protection

### 3.1 Encryption
- **At Rest:**
  - Database encryption
  - File system encryption
  - SSH key encryption
- **In Transit:**
  - TLS 1.3 for all communications
  - Certificate-based authentication
  - Perfect forward secrecy

### 3.2 Sensitive Data Handling
- **SSH Keys:**
  - Encrypted storage
  - Secure key rotation
  - Access logging
- **Configuration:**
  - Encrypted sensitive values
  - Access audit logging
  - Version control

## 4. Network Security

### 4.1 API Security
- **TLS Configuration:**
  - Minimum TLS 1.2
  - Strong cipher suites
  - Certificate validation
- **Rate Limiting:**
  - Per IP: 100 requests/minute
  - Per User: 1000 requests/hour
  - Burst handling

### 4.2 Firewall Rules
- **Inbound:**
  - API access: 443/tcp
  - Syslog: 514/udp, 514/tcp
  - SSH: 22/tcp (restricted)
- **Outbound:**
  - NATS: 4222/tcp
  - Database: 5432/tcp
  - External APIs: 443/tcp

## 5. Secure Development

### 5.1 Code Security
- **Input Validation:**
  - Schema validation
  - Parameter sanitization
  - Type checking
- **Output Encoding:**
  - HTML encoding
  - SQL parameterization
  - JSON sanitization

### 5.2 Dependency Management
- **Package Security:**
  - Regular updates
  - Vulnerability scanning
  - License compliance
- **Container Security:**
  - Base image scanning
  - Layer optimization
  - Security context

## 6. Monitoring and Logging

### 6.1 Security Logging
- **Audit Logs:**
  - Authentication attempts
  - Authorization decisions
  - Configuration changes
  - Action executions
- **Log Protection:**
  - Encrypted storage
  - Access control
  - Retention policy

### 6.2 Security Monitoring
- **Alerts:**
  - Failed authentication
  - Rate limit exceeded
  - Configuration changes
  - Unauthorized access
- **Metrics:**
  - Authentication success rate
  - API usage patterns
  - Error rates

## 7. Incident Response

### 7.1 Security Incidents
- **Detection:**
  - Automated monitoring
  - Manual reporting
  - External notifications
- **Response:**
  - Incident classification
  - Containment procedures
  - Recovery steps
  - Post-incident review

### 7.2 Recovery Procedures
- **Data Recovery:**
  - Backup restoration
  - State recovery
  - Configuration recovery
- **Service Recovery:**
  - Component restart
  - Failover procedures
  - Service verification

## 8. Compliance

### 8.1 Security Standards
- **Implementation:**
  - OWASP Top 10
  - CWE Top 25
  - NIST guidelines
- **Documentation:**
  - Security policies
  - Procedures
  - Guidelines

### 8.2 Regular Audits
- **Internal:**
  - Code reviews
  - Security testing
  - Configuration audits
- **External:**
  - Penetration testing
  - Vulnerability assessment
  - Compliance verification

## 9. Security Updates

### 9.1 Update Process
- **Regular Updates:**
  - Security patches
  - Dependency updates
  - Configuration updates
- **Emergency Updates:**
  - Critical vulnerabilities
  - Zero-day exploits
  - Security incidents

### 9.2 Update Verification
- **Testing:**
  - Security testing
  - Regression testing
  - Performance testing
- **Deployment:**
  - Staged rollout
  - Rollback capability
  - Monitoring 