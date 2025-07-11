import logging
from typing import Optional, Dict, Any

from ...core.types import Action, Observation, ActionType, SearchAction, ClickAction, TypeAction
from ..components.action_selectors import ClickTopResultSelector

logger = logging.getLogger(__name__)


class ActionModule:
    """Module for action selection in cognitive loop"""
    
    def __init__(self, llm_provider: str = "openai"):
        self.llm_provider = llm_provider
        self.fallback_selector = ClickTopResultSelector()
    
    async def select_action(
        self, 
        observation: Observation, 
        context: Dict[str, Any], 
        plan: Optional[str]
    ) -> Action:
        """
        Select concrete action based on plan and observation
        
        Args:
            observation: Current environment observation
            context: Agent context including persona and memory
            plan: Current plan string
            
        Returns:
            Action to execute
        """
        try:
            # Analyze the current situation
            situation = self._analyze_action_context(observation, context, plan)
            
            # Select action based on plan and situation
            if plan:
                action = await self._plan_based_action(plan, observation, context, situation)
                if action:
                    logger.info(f"Selected plan-based action: {action.type.value}")
                    return action
            
            # Fallback to situation-based action
            action = await self._situation_based_action(observation, context, situation)
            if action:
                logger.info(f"Selected situation-based action: {action.type.value}")
                return action
            
            # Final fallback
            logger.warning("No suitable action found, stopping")
            return Action(type=ActionType.STOP)
            
        except Exception as e:
            logger.error(f"Error in action module: {e}")
            return Action(type=ActionType.STOP)
    
    def _analyze_action_context(
        self, 
        observation: Observation, 
        context: Dict[str, Any], 
        plan: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze context for action selection"""
        try:
            situation = {
                "has_clickables": len(observation.clickables) > 0,
                "has_inputs": len(observation.inputs) > 0,
                "has_selects": len(observation.selects) > 0,
                "has_error": observation.error_message is not None,
                "url": observation.url,
                "plan": plan,
                "intent": context["persona"].intent
            }
            
            # Analyze page type
            url_lower = observation.url.lower()
            if "search" in url_lower or observation.inputs:
                situation["page_type"] = "search"
            elif "product" in url_lower or "item" in url_lower:
                situation["page_type"] = "product"
            elif observation.clickables:
                situation["page_type"] = "navigation"
            else:
                situation["page_type"] = "content"
            
            # Analyze action urgency
            if observation.error_message:
                situation["urgency"] = "high"  # Need to recover from error
            elif not observation.clickables and not observation.inputs:
                situation["urgency"] = "high"  # Stuck, need to find way forward
            else:
                situation["urgency"] = "normal"
            
            return situation
            
        except Exception as e:
            logger.error(f"Error analyzing action context: {e}")
            return {}
    
    async def _plan_based_action(
        self, 
        plan: str, 
        observation: Observation, 
        context: Dict[str, Any], 
        situation: Dict[str, Any]
    ) -> Optional[Action]:
        """Select action based on current plan"""
        try:
            plan_lower = plan.lower()
            intent = context["persona"].intent
            
            # Search-related plans
            if "search" in plan_lower:
                if observation.inputs:
                    # Find search input and use it
                    for input_elem in observation.inputs:
                        if input_elem.get("type") in ["text", "search"]:
                            element_id = input_elem.get("name", input_elem.get("id", ""))
                            if element_id:
                                return TypeAction(text=intent, element_id=element_id)
                
                # If no inputs, look for search-related clickables
                for clickable in observation.clickables:
                    text = clickable.get("text", "").lower()
                    name = clickable.get("name", "").lower()
                    if "search" in f"{text} {name}":
                        element_id = clickable.get("name", clickable.get("id", ""))
                        if element_id:
                            return ClickAction(element_id=element_id)
            
            # Navigation-related plans
            elif "navigate" in plan_lower or "explore" in plan_lower:
                if observation.clickables:
                    # Use the fallback selector to find relevant clickable
                    return await self.fallback_selector.select_action(observation, context)
            
            # Examination-related plans
            elif "examine" in plan_lower or "analyze" in plan_lower:
                # Check if we've found what we're looking for
                page_content = observation.page_content.lower()
                intent_words = intent.lower().split()
                relevance_score = sum(1 for word in intent_words if word in page_content)
                
                if relevance_score >= len(intent_words) * 0.7:
                    # Found relevant content, can stop
                    return Action(type=ActionType.STOP)
                else:
                    # Continue exploring
                    if observation.clickables:
                        return await self.fallback_selector.select_action(observation, context)
            
            # Recovery-related plans
            elif "recover" in plan_lower or "error" in plan_lower:
                # Try to go back or find alternative path
                if observation.clickables:
                    # Look for back button or home link
                    for clickable in observation.clickables:
                        text = clickable.get("text", "").lower()
                        name = clickable.get("name", "").lower()
                        if any(keyword in f"{text} {name}" for keyword in ["back", "home", "main"]):
                            element_id = clickable.get("name", clickable.get("id", ""))
                            if element_id:
                                return ClickAction(element_id=element_id)
                
                # Fallback to browser back
                return Action(type=ActionType.BACK)
            
            return None
            
        except Exception as e:
            logger.error(f"Error in plan-based action selection: {e}")
            return None
    
    async def _situation_based_action(
        self, 
        observation: Observation, 
        context: Dict[str, Any], 
        situation: Dict[str, Any]
    ) -> Optional[Action]:
        """Select action based on current situation"""
        try:
            # Handle errors first
            if situation.get("has_error"):
                return Action(type=ActionType.BACK)
            
            # Handle different page types
            page_type = situation.get("page_type")
            intent = context["persona"].intent
            
            if page_type == "search":
                # On search page, try to search
                if observation.inputs:
                    for input_elem in observation.inputs:
                        if input_elem.get("type") in ["text", "search"]:
                            element_id = input_elem.get("name", input_elem.get("id", ""))
                            if element_id:
                                return TypeAction(text=intent, element_id=element_id)
            
            elif page_type in ["navigation", "product", "content"]:
                # Try to find relevant clickables
                if observation.clickables:
                    return await self.fallback_selector.select_action(observation, context)
            
            # If we have inputs but no clear search context, try typing intent
            if observation.inputs:
                input_elem = observation.inputs[0]
                element_id = input_elem.get("name", input_elem.get("id", ""))
                if element_id:
                    return TypeAction(text=intent, element_id=element_id)
            
            # If we have clickables, try clicking something relevant
            if observation.clickables:
                return await self.fallback_selector.select_action(observation, context)
            
            # No clear action available
            return None
            
        except Exception as e:
            logger.error(f"Error in situation-based action selection: {e}")
            return None
    
    async def _llm_select_action(
        self, 
        observation: Observation, 
        context: Dict[str, Any], 
        plan: Optional[str]
    ) -> Optional[Action]:
        """Use LLM for sophisticated action selection (TODO: implement)"""
        # TODO: Implement LLM-based action selection
        # This would use prompts to reason about the best action
        return None 