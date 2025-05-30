"""Custom exceptions for the base agent package."""


class AgentError(Exception):
    """Base exception for agent-related errors."""

    pass


class ValidationError(AgentError):
    """Raised when validation fails."""

    pass


class AuthenticationError(AgentError):
    """Raised when authentication fails."""

    pass


class ResourceError(AgentError):
    """Raised when a resource operation fails."""

    pass


class CommunicationError(AgentError):
    """Raised when agent communication fails."""

    pass


class ProcessingError(AgentError):
    """Raised when agent fails to process an event."""

    pass


class ConfigurationError(AgentError):
    """Raised when agent configuration is invalid or missing."""

    pass


class DependencyError(AgentError):
    """Raised when agent dependencies are not met."""

    pass


class StateError(AgentError):
    """Raised when agent is in an invalid state for an operation."""

    pass
