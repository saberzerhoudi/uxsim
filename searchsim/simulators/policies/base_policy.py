from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Any, Optional

from ...core.types import Action, Observation
from ...core.exceptions import PolicyException

if TYPE_CHECKING:
    from ...agent import Agent


class BaseDecisionPolicy(ABC):
    """Base class for all decision policies"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.agent: 'Agent' = None
        self.config = config or {}
    
    def set_agent(self, agent: 'Agent'):
        """Set the agent that uses this policy"""
        self.agent = agent
    
    @abstractmethod
    async def decide(self, observation: Observation) -> Action:
        """
        Make a decision based on current observation
        
        Args:
            observation: Current environment observation
            
        Returns:
            Action to take next
        """
        raise NotImplementedError
    
    def get_agent_context(self) -> dict:
        """Get relevant agent context for decision making"""
        if not self.agent:
            raise PolicyException("Agent not set for policy")
        
        return {
            "persona": self.agent.persona,
            "current_plan": self.agent.current_plan,
            "memory_count": len(self.agent.memory.memories),
            "timestamp": self.agent.memory.timestamp
        } 