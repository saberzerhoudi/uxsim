import logging
from typing import Optional, Dict, Any, List

from ...core.types import Observation

logger = logging.getLogger(__name__)


class PlanningModule:
    """Module for planning in cognitive loop"""
    
    def __init__(self, llm_provider: str = "openai"):
        self.llm_provider = llm_provider
    
    async def plan(
        self, 
        observation: Observation, 
        context: Dict[str, Any], 
        perceptions: List[str]
    ) -> Optional[str]:
        """
        Generate or update plan based on current situation
        
        Args:
            observation: Current environment observation
            context: Agent context including persona and memory
            perceptions: Recent perceptions from perception module
            
        Returns:
            Updated plan string or None if no plan change needed
        """
        try:
            persona = context["persona"]
            current_plan = context.get("current_plan")
            
            # Analyze current situation
            situation_analysis = self._analyze_situation(observation, context, perceptions)
            
            # Determine if we need a new plan or can continue with current one
            if not current_plan:
                # No existing plan, create initial plan
                new_plan = self._create_initial_plan(persona, observation, situation_analysis)
                logger.info(f"Created initial plan: {new_plan}")
                return new_plan
            
            # Check if current plan is still valid
            plan_validity = self._assess_plan_validity(current_plan, observation, situation_analysis)
            
            if plan_validity["needs_update"]:
                # Update existing plan
                updated_plan = self._update_plan(
                    current_plan, 
                    observation, 
                    situation_analysis, 
                    plan_validity["reason"]
                )
                logger.info(f"Updated plan: {updated_plan}")
                return updated_plan
            
            # Current plan is still valid
            logger.info("Current plan remains valid")
            return None
            
        except Exception as e:
            logger.error(f"Error in planning module: {e}")
            return None
    
    def _analyze_situation(
        self, 
        observation: Observation, 
        context: Dict[str, Any], 
        perceptions: List[str]
    ) -> Dict[str, Any]:
        """Analyze the current situation"""
        try:
            analysis = {
                "has_clickables": len(observation.clickables) > 0,
                "has_inputs": len(observation.inputs) > 0,
                "has_error": observation.error_message is not None,
                "url": observation.url,
                "content_length": len(observation.page_content),
                "perceptions": perceptions
            }
            
            # Analyze progress toward goal
            intent = context["persona"].intent.lower()
            page_content = observation.page_content.lower()
            
            # Simple relevance scoring
            intent_words = intent.split()
            relevance_score = sum(1 for word in intent_words if word in page_content)
            analysis["relevance_to_intent"] = relevance_score / len(intent_words) if intent_words else 0
            
            # Determine page type
            if "search" in observation.url.lower() or observation.inputs:
                analysis["page_type"] = "search"
            elif observation.clickables and "product" in observation.url.lower():
                analysis["page_type"] = "product"
            elif observation.clickables:
                analysis["page_type"] = "navigation"
            else:
                analysis["page_type"] = "content"
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing situation: {e}")
            return {}
    
    def _create_initial_plan(
        self, 
        persona, 
        observation: Observation, 
        situation: Dict[str, Any]
    ) -> str:
        """Create initial plan based on persona intent and current situation"""
        try:
            intent = persona.intent
            
            if situation.get("page_type") == "search":
                return f"Search for '{intent}' using available search interface"
            elif situation.get("has_clickables"):
                return f"Navigate through available options to find '{intent}'"
            elif situation.get("has_inputs"):
                return f"Use input fields to search for '{intent}'"
            else:
                return f"Explore the page to find ways to accomplish '{intent}'"
                
        except Exception as e:
            logger.error(f"Error creating initial plan: {e}")
            return f"Find and accomplish: {persona.intent}"
    
    def _assess_plan_validity(
        self, 
        current_plan: str, 
        observation: Observation, 
        situation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess whether current plan is still valid"""
        try:
            validity = {"needs_update": False, "reason": ""}
            
            # Check for errors
            if situation.get("has_error"):
                validity["needs_update"] = True
                validity["reason"] = "Error encountered, need to adapt plan"
                return validity
            
            # Check if we've found highly relevant content
            if situation.get("relevance_to_intent", 0) > 0.7:
                validity["needs_update"] = True
                validity["reason"] = "Found relevant content, may need to refine approach"
                return validity
            
            # Check if page type has changed significantly
            if "search" in current_plan.lower() and situation.get("page_type") != "search":
                validity["needs_update"] = True
                validity["reason"] = "Moved away from search page, need new strategy"
                return validity
            
            # Check if we have new interaction opportunities
            if "navigate" not in current_plan.lower() and situation.get("has_clickables"):
                validity["needs_update"] = True
                validity["reason"] = "New navigation options available"
                return validity
            
            return validity
            
        except Exception as e:
            logger.error(f"Error assessing plan validity: {e}")
            return {"needs_update": False, "reason": ""}
    
    def _update_plan(
        self, 
        current_plan: str, 
        observation: Observation, 
        situation: Dict[str, Any], 
        reason: str
    ) -> str:
        """Update existing plan based on new situation"""
        try:
            if "error" in reason.lower():
                return f"Recover from error and continue with: {current_plan}"
            
            if "relevant content" in reason.lower():
                return f"Examine relevant content and determine next steps for: {current_plan}"
            
            if "search page" in reason.lower():
                return f"Navigate through results to accomplish: {current_plan}"
            
            if "navigation options" in reason.lower():
                return f"Explore new navigation options to: {current_plan}"
            
            # Default update
            return f"Adapt strategy and continue with: {current_plan}"
            
        except Exception as e:
            logger.error(f"Error updating plan: {e}")
            return current_plan
    
    async def _llm_plan(
        self, 
        observation: Observation, 
        context: Dict[str, Any], 
        perceptions: List[str]
    ) -> Optional[str]:
        """Use LLM for sophisticated planning (TODO: implement)"""
        # TODO: Implement LLM-based planning
        # This would use prompts to generate more sophisticated plans
        return None 