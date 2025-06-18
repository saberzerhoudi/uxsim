import logging
from typing import List, Dict, Any, Optional

from .base_policy import BaseDecisionPolicy
from ...core.types import Action, Observation, ActionType, SearchAction, ClickAction, StopAction
from ...core.exceptions import PolicyException
from ..components.query_generators import BaseQueryGenerator, IntentBasedQueryGenerator
from ..components.action_selectors import BaseActionSelector, ClickTopResultSelector
from ..components.relevance_classifiers import BaseRelevanceClassifier, KeywordRelevanceClassifier

logger = logging.getLogger(__name__)


class ComponentPolicy(BaseDecisionPolicy):
    """Policy that uses pluggable components for decision making"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Create default components if not provided in config
        self.query_generator = IntentBasedQueryGenerator()
        self.action_selector = ClickTopResultSelector()
        self.relevance_classifier = KeywordRelevanceClassifier()
        
        # Configuration
        self.steps_taken = 0
        self.max_steps = self.config.get('max_steps', 20)
        self.use_relevance_check = self.config.get('use_relevance_check', True)
    
    async def decide(self, observation: Observation) -> Action:
        """Make decision using component pipeline"""
        try:
            context = self.get_agent_context()
            
            # Check if we should stop based on relevance
            if self.relevance_classifier and self.use_relevance_check and self.steps_taken > 0:
                is_relevant = await self.relevance_classifier.is_relevant(
                    observation, context["persona"].intent
                )
                if is_relevant:
                    logger.info("Found relevant content, stopping search")
                    return StopAction(reason="Found relevant content")
            
            # Check max steps
            if self.steps_taken >= self.max_steps:
                logger.info("Max steps reached, stopping")
                return StopAction(reason="Maximum steps reached")
            
            # If we're on a search results page, use action selector
            if observation.clickables and self.steps_taken > 0:
                action = await self.action_selector.select_action(observation, context)
                if action:
                    self.steps_taken += 1
                    return action
            
            # Generate search query if we need to search
            if self.steps_taken == 0 or not observation.clickables:
                query = await self.query_generator.generate_query(context)
                if query:
                    self.steps_taken += 1
                    return SearchAction(query=query)
            
            # Default fallback
            logger.warning("No suitable action found, stopping")
            return StopAction(reason="No suitable action available")
            
        except Exception as e:
            logger.error(f"Error in component policy decision: {e}")
            return StopAction(reason=f"Policy error: {e}")
    
    def get_state(self) -> dict:
        """Get current policy state"""
        return {
            "policy_type": "component",
            "steps_taken": self.steps_taken,
            "max_steps": self.max_steps,
            "use_relevance_check": self.use_relevance_check
        }
    
    def reset(self):
        """Reset policy state for new simulation"""
        self.steps_taken = 0 