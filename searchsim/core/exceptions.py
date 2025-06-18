"""
Core exceptions for SearchSim framework
"""


class SearchSimException(Exception):
    """Base exception for SearchSim framework"""
    pass


class SimulationException(SearchSimException):
    """Exception for simulation-related errors"""
    pass


class InvalidActionException(SearchSimException):
    """Raised when an invalid action is attempted"""
    pass


class EnvironmentException(SearchSimException):
    """Exception for environment-related errors"""
    pass


class AgentException(SearchSimException):
    """Exception for agent-related errors"""
    pass


class PolicyException(SearchSimException):
    """Exception for policy-related errors"""
    pass


class MemoryException(SearchSimException):
    """Exception for memory-related errors"""
    pass


class PersonaException(SearchSimException):
    """Raised when persona operations fail"""
    pass


class ComponentException(SearchSimException):
    """Exception for component-related errors"""
    pass 