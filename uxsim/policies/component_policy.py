import logging
from typing import Dict, Any

from ..core.types import Action, ActionType, Observation
from .base_policy import BaseDecisionPolicy

logger = logging.getLogger(__name__)


class ComponentPolicy(BaseDecisionPolicy):
    """Simple component-based policy for testing and basic simulations"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.step_count = 0
    
    async def decide_action(self, observation: Observation, state: Dict[str, Any]) -> Action:
        """Generate action based on simple heuristics"""
        self.step_count += 1
        
        # Simple strategy: search on first step, then stop
        if self.step_count == 1:
            # Extract intent from agent context
            if self.agent and self.agent.persona:
                search_query = self._generate_search_query(self.agent.persona.intent)
                return Action(
                    type=ActionType.SEARCH,
                    parameters={"query": search_query}
                )
        
        # Stop after a few steps
        return Action(
            type=ActionType.STOP,
            parameters={"reason": "ComponentPolicy completed basic simulation"}
        )
    
    def _generate_search_query(self, intent: str) -> str:
        """Generate search query from intent"""
        # Simple intent-to-query conversion
        query = intent.lower()
        # Remove common prefixes
        for prefix in ["i want to", "i need to", "buy", "find", "search for"]:
            if query.startswith(prefix):
                query = query[len(prefix):].strip()
        
        return query or "search query"
    
    def get_state(self) -> dict:
        """Get current policy state"""
        return {
            "policy_type": "component",
            "step_count": self.step_count
        } 