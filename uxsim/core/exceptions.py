"""
Core exceptions for UXSim framework
"""


class UXSimException(Exception):
    """Base exception for UXSim framework"""
    pass


class SimulationException(UXSimException):
    """Exception for simulation-related errors"""
    pass


class InvalidActionException(UXSimException):
    """Raised when an invalid action is attempted"""
    pass


class EnvironmentException(UXSimException):
    """Exception for environment-related errors"""
    pass


class AgentException(UXSimException):
    """Exception for agent-related errors"""
    pass


class PolicyException(UXSimException):
    """Exception for policy-related errors"""
    pass


class MemoryException(UXSimException):
    """Exception for memory-related errors"""
    pass


class PersonaException(UXSimException):
    """Raised when persona operations fail"""
    pass


class ComponentException(UXSimException):
    """Exception for component-related errors"""
    pass 