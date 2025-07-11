"""
UXSim: Advanced Search Simulation Framework

A unified framework for simulating search behavior with LLM-based agents
"""

__version__ = "0.2.0"

from .core.types import (
    Action, ActionType, Observation, Persona, MemoryPiece, 
    SimulationConfig, AgentState
)
from .core.exceptions import (
    UXSimException, SimulationException, AgentException, 
    EnvironmentException, PolicyException, MemoryException
)
from .agent import Agent
from .simulation import Simulation

__all__ = [
    # Core types
    "Action", "ActionType", "Observation", "Persona", "MemoryPiece",
    "SimulationConfig", "AgentState",
    
    # Exceptions
    "UXSimException", "SimulationException", "AgentException",
    "EnvironmentException", "PolicyException", "MemoryException",
    
    # Main classes
    "Agent", "Simulation"
] 