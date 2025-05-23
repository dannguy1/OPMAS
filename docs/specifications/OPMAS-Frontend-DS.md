# OPMAS Frontend UI Design Specification (OPMAS-Frontend-DS)

## 1. Introduction

This document outlines the design for the web-based Management UI of OPMAS, transitioning from a file-based configuration to a database-centric architecture. The frontend provides a user-friendly interface for monitoring system status, managing configurations, and viewing analysis results. It interacts with the Management API to perform all operations, ensuring a clean separation of concerns.

## 2. Goals

* Provide an intuitive, responsive web interface
* Enable efficient system monitoring and management
* Support configuration of agents, rules, and playbooks
* Display findings and intended actions clearly
* Ensure consistent user experience
* Support future enhancements and scalability
* Centralize configuration in database
* Improve modularity and maintainability

## 3. Architecture Overview

### 3.1. System Components

* **Database (PostgreSQL):** Central repository for configuration and results
  * Stores core config, agent definitions, rules, playbooks
  * Maintains findings and intended actions history
  * Provides structured, queryable data storage
* **Management API (FastAPI):** Intermediary between Frontend and Database
  * Handles all CRUD operations
  * Manages system control
  * Provides data access endpoints
* **Frontend UI (React):** User interface for system interaction
  * Displays system status and controls
  * Manages configurations
  * Shows analysis results
* **OPMAS Core Components:** Agents, Orchestrator, Log API
  * Read configurations from database
  * Publish findings to NATS
  * Write results to database
* **Message Bus (NATS):** For real-time event communication
  * Handles ParsedLogEvent messages
  * Distributes AgentFinding messages
  * Manages action commands

### 3.2. Data Flow

1. Log API publishes `ParsedLogEvent` to NATS
2. Agent processes event, publishes `AgentFinding` to NATS
3. Orchestrator receives finding, writes to database
4. Orchestrator processes playbook, writes intended actions
5. Management API reads data from database
6. Frontend displays data to user

### 3.3. Database Schema

* **Configuration Tables:**
  * `opmas_config`: Core system settings
  * `agents`: Agent definitions and status
  * `agent_rules`: Agent-specific rules
  * `playbooks`: Action playbooks
  * `playbook_steps`: Playbook steps
* **Operational Tables:**
  * `findings`: Detected issues
  * `intended_actions`: Planned actions

## 4. Technology Stack

* **Framework:** React with TypeScript
* **Build Tool:** Vite
* **Styling:** Tailwind CSS
* **State Management:** React Query (for API data)
* **Routing:** React Router
* **HTTP Client:** Axios
* **Component Library:** Headless UI (integrated with Tailwind)
* **Testing:** Jest + React Testing Library

## 5. Application Structure

### 5.1. Directory Structure

```
ui/
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── common/       # Shared components
│   │   ├── forms/        # Form components
│   │   ├── tables/       # Table components
│   │   └── modals/       # Modal components
│   ├── pages/            # Page components
│   │   ├── Dashboard/
│   │   ├── Agents/
│   │   ├── Findings/
│   │   └── ...
│   ├── services/         # API integration
│   │   ├── api.ts        # API client setup
│   │   └── endpoints/    # API endpoint definitions
│   ├── hooks/            # Custom React hooks
│   ├── utils/            # Utility functions
│   ├── types/            # TypeScript type definitions
│   └── context/          # React context providers
├── public/               # Static assets
└── tests/               # Test files
```

### 5.2. Key Components

#### 5.2.1. Layout Components

* `MainLayout`: Primary application layout with navigation
* `PageHeader`: Consistent page header with title and actions
* `Sidebar`: Navigation sidebar
* `ContentArea`: Main content container

#### 5.2.2. Common Components

* `Button`: Standardized button component
* `Input`: Form input component
* `Select`: Dropdown select component
* `Table`: Data table component
* `Modal`: Modal dialog component
* `Toast`: Notification component

#### 5.2.3. Page Components

* `DashboardPage`: System status and controls
* `AgentsPage`: Agent management
* `FindingsPage`: Findings display
* `IntendedActionsPage`: Actions display
* `ConfigurationPage`: System configuration

## 6. Page Designs

### 6.1. Dashboard

* System status overview
* Start/Stop controls
* Component health indicators
* Recent findings summary
* Quick action buttons

### 6.2. Agent Management

* Agent list/grid view
* Enable/disable controls
* Add/Edit/Delete functionality
* Rule management links
* Agent status indicators

### 6.3. Findings View

* Filterable/sortable table
* Severity indicators
* Detailed view modal
* Related actions links
* Export functionality

### 6.4. Configuration

* Core settings editor
* Playbook management
* Rule editor
* System preferences

## 7. API Integration

### 7.1. API Client

* Axios-based client
* Request/response interceptors
* Error handling
* Authentication handling
* Request caching

### 7.2. Data Fetching

* React Query for data management
* Optimistic updates
* Background refetching
* Error boundaries
* Loading states

### 7.3. Key Endpoints

* **System Status & Control:**
  * `GET /api/status`: System component status
  * `POST /api/control/start`: Start system
  * `POST /api/control/stop`: Stop system
* **Configuration Management:**
  * `GET/PUT /api/config/core`: Core configuration
  * `GET/POST/PUT/DELETE /api/config/agents`: Agent management
  * `GET/POST/PUT/DELETE /api/config/agent-rules/{agent_id}`: Agent rules
  * `GET/POST/PUT/DELETE /api/config/playbooks`: Playbook management
  * `GET/POST/PUT/DELETE /api/config/playbook-steps/{playbook_id}`: Playbook steps
* **Operational Data:**
  * `GET /api/findings`: Findings history
  * `GET /api/intended-actions`: Action history
  * `GET /api/logs/{component}`: Component logs

## 8. State Management

* React Query for server state
* React Context for UI state
* Local storage for preferences
* URL state for filters/pagination

## 9. Styling Guidelines

### 9.1. Design System

* Color palette
* Typography
* Spacing
* Component variants
* Responsive breakpoints

### 9.2. Component Styling

* Tailwind utility classes
* Component-specific styles
* Dark mode support
* Responsive design
* Accessibility considerations

## 10. User Experience

### 10.1. Navigation

* Clear navigation structure
* Breadcrumb navigation
* Quick access to common actions
* Context-aware menus

### 10.2. Feedback

* Loading indicators
* Success/error notifications
* Form validation feedback
* Confirmation dialogs
* Progress indicators

## 11. Testing Strategy

### 11.1. Unit Tests

* Component testing
* Hook testing
* Utility function testing
* API client testing

### 11.2. Integration Tests

* Page flow testing
* API integration testing
* State management testing
* Error handling testing

### 11.3. E2E Tests

* Critical user flows
* Configuration workflows
* Error scenarios
* Performance testing

## 12. Performance Considerations

* Code splitting
* Lazy loading
* Image optimization
* Caching strategies
* Bundle size optimization
* Database query optimization
* Response caching
* Connection pooling
* Pagination

## 13. Security

* CSRF protection
* XSS prevention
* Input sanitization
* Secure storage
* Authentication handling
* HTTPS enforcement
* CORS configuration
* Rate limiting
* Data encryption
* Audit logging

## 14. Accessibility

* ARIA labels
* Keyboard navigation
* Screen reader support
* Color contrast
* Focus management

## 15. Deployment

### 15.1. Build Process

* Production build configuration
* Environment variable handling
* Asset optimization
* Source maps

### 15.2. Docker Deployment

* Multi-stage build
* Nginx configuration
* Health checks
* Environment configuration

## 16. Monitoring

* Error tracking
* Performance monitoring
* User analytics
* Usage patterns
* Error reporting
* Request timing
* Resource usage
* Error rates
* Performance metrics

## 17. Future Enhancements

* Real-time updates via WebSockets
* Advanced filtering
* Custom dashboards
* Export/Import functionality
* User preferences
* Theme customization
* Historical data visualization
* More granular process control
* User authentication and role-based access
* GraphQL API support
* Bulk operations
* API versioning strategy 