from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Any, Optional

from ..core.types import Action, Observation
from ..core.exceptions import PolicyException

if TYPE_CHECKING:
    from ..agent import Agent


class BaseDecisionPolicy(ABC):
    """Base class for all decision policies"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.agent: 'Agent' = None
        self.config = config or {}
    
    def set_agent(self, agent: 'Agent'):
        """Set the agent that uses this policy"""
        self.agent = agent
    
    async def decide(self, observation: Observation) -> Action:
        """
        Legacy method for backward compatibility
        """
        return await self.decide_action(observation, {})
    
    @abstractmethod
    async def decide_action(self, observation: Observation, state: Dict[str, Any]) -> Action:
        """
        Make a decision based on current observation and agent state
        
        Args:
            observation: Current environment observation
            state: Current agent state
            
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