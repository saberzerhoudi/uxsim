import random
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

from ...core.types import Action, Observation, ActionType, ClickAction, TypeAction, ActionType

logger = logging.getLogger(__name__)


class BaseActionSelector(ABC):
    """Base class for action selectors"""
    
    @abstractmethod
    async def select_action(self, observation: Observation, context: Dict[str, Any]) -> Optional[Action]:
        """Select an action based on observation and context"""
        raise NotImplementedError


class ClickTopResultSelector(BaseActionSelector):
    """Selector that clicks the first relevant clickable element"""
    
    async def select_action(self, observation: Observation, context: Dict[str, Any]) -> Optional[Action]:
        """Click the first clickable element that seems relevant"""
        try:
            if not observation.clickables:
                return None
            
            persona = context["persona"]
            intent = persona.intent.lower()
            
            # Score clickables by relevance to intent
            scored_clickables = []
            for clickable in observation.clickables:
                text = clickable.get("text", "").lower()
                name = clickable.get("name", "").lower()
                combined_text = f"{text} {name}"
                
                # Simple keyword matching score
                score = 0
                intent_words = intent.split()
                for word in intent_words:
                    if word in combined_text:
                        score += 1
                
                scored_clickables.append((score, clickable))
            
            # Sort by score and take the highest
            scored_clickables.sort(key=lambda x: x[0], reverse=True)
            
            if scored_clickables and scored_clickables[0][0] > 0:
                best_clickable = scored_clickables[0][1]
                element_id = best_clickable.get("name", best_clickable.get("id", ""))
                
                if element_id:
                    logger.info(f"Selected clickable: {element_id}")
                    return ClickAction(element_id=element_id)
            
            # Fallback: click first clickable
            if observation.clickables:
                first_clickable = observation.clickables[0]
                element_id = first_clickable.get("name", first_clickable.get("id", ""))
                if element_id:
                    logger.info(f"Fallback: clicking first clickable: {element_id}")
                    return ClickAction(element_id=element_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error selecting clickable action: {e}")
            return None


class RandomActionSelector(BaseActionSelector):
    """Selector that chooses random actions"""
    
    async def select_action(self, observation: Observation, context: Dict[str, Any]) -> Optional[Action]:
        """Select a random available action"""
        try:
            available_actions = []
            
            # Add clickable actions
            for clickable in observation.clickables:
                element_id = clickable.get("name", clickable.get("id", ""))
                if element_id:
                    available_actions.append(ClickAction(element_id=element_id))
            
            # Add input actions (for search boxes etc.)
            for input_elem in observation.inputs:
                element_id = input_elem.get("name", input_elem.get("id", ""))
                if element_id and input_elem.get("type") in ["text", "search"]:
                    # Type the persona's intent
                    intent = context["persona"].intent
                    available_actions.append(TypeAction(text=intent, element_id=element_id))
            
            if available_actions:
                selected_action = random.choice(available_actions)
                logger.info(f"Randomly selected action: {selected_action.type.value}")
                return selected_action
            
            return None
            
        except Exception as e:
            logger.error(f"Error selecting random action: {e}")
            return None


class StopOnRelevanceSelector(BaseActionSelector):
    """Selector that stops when relevant content is found"""
    
    def __init__(self, relevance_threshold: float = 0.7):
        self.relevance_threshold = relevance_threshold
    
    async def select_action(self, observation: Observation, context: Dict[str, Any]) -> Optional[Action]:
        """Stop if page content seems relevant to intent"""
        try:
            persona = context["persona"]
            intent = persona.intent.lower()
            
            # Check page content for relevance
            page_content = observation.page_content.lower()
            intent_words = intent.split()
            
            # Simple relevance scoring
            matches = sum(1 for word in intent_words if word in page_content)
            relevance_score = matches / len(intent_words) if intent_words else 0
            
            if relevance_score >= self.relevance_threshold:
                logger.info(f"Found relevant content (score: {relevance_score:.2f}), stopping")
                return Action(type=ActionType.STOP)
            
            # Otherwise, try to click something relevant
            return await ClickTopResultSelector().select_action(observation, context)
            
        except Exception as e:
            logger.error(f"Error in relevance-based selection: {e}")
            return None


class LLMActionSelector(BaseActionSelector):
    """LLM-based action selector for sophisticated decision making"""
    
    def __init__(self, llm_provider: str = "openai"):
        self.llm_provider = llm_provider
    
    async def select_action(self, observation: Observation, context: Dict[str, Any]) -> Optional[Action]:
        """Select action using LLM reasoning"""
        try:
            # TODO: Implement LLM-based action selection
            # For now, fall back to top result selector
            logger.info("Using LLM action selector (fallback to top result)")
            return await ClickTopResultSelector().select_action(observation, context)
            
        except Exception as e:
            logger.error(f"Error in LLM action selection: {e}")
            return None


class CompositeActionSelector(BaseActionSelector):
    """Selector that combines multiple selectors with priorities"""
    
    def __init__(self, selectors: List[BaseActionSelector]):
        self.selectors = selectors
    
    async def select_action(self, observation: Observation, context: Dict[str, Any]) -> Optional[Action]:
        """Try selectors in order until one returns an action"""
        try:
            for selector in self.selectors:
                action = await selector.select_action(observation, context)
                if action:
                    logger.info(f"Composite selector used: {selector.__class__.__name__}")
                    return action
            
            logger.warning("No selector in composite found suitable action")
            return None
            
        except Exception as e:
            logger.error(f"Error in composite action selection: {e}")
            return None 