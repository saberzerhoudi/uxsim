import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ReflectionModule:
    """Module for reflection in cognitive loop"""
    
    def __init__(self, llm_provider: str = "openai"):
        self.llm_provider = llm_provider
    
    async def reflect(self, context: Dict[str, Any]) -> List[str]:
        """
        Reflect on recent experiences and generate insights
        
        Args:
            context: Agent context including persona, memory, and current state
            
        Returns:
            List of reflection insights
        """
        try:
            reflections = []
            
            # Analyze recent actions and their outcomes
            recent_actions = context.get("recent_actions", [])
            if recent_actions:
                action_reflections = self._reflect_on_actions(recent_actions, context)
                reflections.extend(action_reflections)
            
            # Analyze progress toward goal
            progress_reflections = self._reflect_on_progress(context)
            reflections.extend(progress_reflections)
            
            # Analyze patterns in behavior
            pattern_reflections = self._reflect_on_patterns(context)
            reflections.extend(pattern_reflections)
            
            # Generate strategic insights
            strategic_reflections = self._reflect_on_strategy(context)
            reflections.extend(strategic_reflections)
            
            # TODO: Add LLM-based reflection for deeper insights
            
            logger.info(f"Generated {len(reflections)} reflections")
            return reflections
            
        except Exception as e:
            logger.error(f"Error in reflection module: {e}")
            return ["Error occurred during reflection"]
    
    def _reflect_on_actions(self, recent_actions: List, context: Dict[str, Any]) -> List[str]:
        """Reflect on recent actions and their effectiveness"""
        try:
            reflections = []
            
            if len(recent_actions) >= 2:
                # Analyze action patterns
                action_types = [action.metadata.get("action_type") for action in recent_actions]
                
                # Check for repetitive actions
                if len(set(action_types)) < len(action_types) / 2:
                    reflections.append("I notice I'm repeating similar actions - may need to try a different approach")
                
                # Check for search vs navigation balance
                search_actions = sum(1 for t in action_types if t == "search")
                click_actions = sum(1 for t in action_types if t == "click")
                
                if search_actions > click_actions * 2:
                    reflections.append("I've been searching a lot - maybe I should focus more on navigating results")
                elif click_actions > search_actions * 3:
                    reflections.append("I've been clicking around - maybe I need to refine my search strategy")
            
            # Analyze last action specifically
            if recent_actions:
                last_action = recent_actions[-1]
                action_type = last_action.metadata.get("action_type")
                
                if action_type == "search":
                    reflections.append("My last search action should help me find relevant content")
                elif action_type == "click":
                    reflections.append("My last click should have taken me to more relevant content")
            
            return reflections
            
        except Exception as e:
            logger.error(f"Error reflecting on actions: {e}")
            return []
    
    def _reflect_on_progress(self, context: Dict[str, Any]) -> List[str]:
        """Reflect on progress toward the goal"""
        try:
            reflections = []
            
            persona = context["persona"]
            memory_summary = context.get("memory_summary", {})
            
            # Analyze memory growth
            total_memories = memory_summary.get("total_memories", 0)
            if total_memories > 10:
                reflections.append(f"I've accumulated {total_memories} memories - building good context about this search")
            elif total_memories > 5:
                reflections.append("I'm starting to build context about this search task")
            else:
                reflections.append("I'm still in the early stages of this search")
            
            # Analyze memory types
            memory_by_kind = memory_summary.get("by_kind", {})
            observations = memory_by_kind.get("observation", 0)
            actions = memory_by_kind.get("action", 0)
            
            if observations > actions * 2:
                reflections.append("I've been observing a lot - time to take more decisive action")
            elif actions > observations:
                reflections.append("I've been active - good progress on exploring options")
            
            # Reflect on intent alignment
            intent = persona.intent
            if "buy" in intent.lower():
                reflections.append("My goal is to make a purchase - I should focus on finding product pages and purchase options")
            elif "find" in intent.lower() or "search" in intent.lower():
                reflections.append("My goal is to find information - I should focus on relevant content and details")
            elif "compare" in intent.lower():
                reflections.append("My goal involves comparison - I should look for multiple options to evaluate")
            
            return reflections
            
        except Exception as e:
            logger.error(f"Error reflecting on progress: {e}")
            return []
    
    def _reflect_on_patterns(self, context: Dict[str, Any]) -> List[str]:
        """Reflect on behavioral patterns"""
        try:
            reflections = []
            
            memory_summary = context.get("memory_summary", {})
            api_calls = memory_summary.get("api_calls", 0)
            
            # Analyze decision-making frequency
            if api_calls > 15:
                reflections.append("I've been making many decisions - should ensure I'm being efficient")
            elif api_calls > 8:
                reflections.append("I'm making steady progress through this search task")
            else:
                reflections.append("I'm still getting oriented with this search task")
            
            # Analyze recent thoughts
            recent_thoughts = context.get("recent_thoughts", [])
            if recent_thoughts:
                thought_content = " ".join([t.content for t in recent_thoughts])
                
                if "error" in thought_content.lower():
                    reflections.append("I've encountered some errors - need to be more careful with my actions")
                
                if "relevant" in thought_content.lower():
                    reflections.append("I've been finding relevant content - good sign I'm on the right track")
                
                if "perception" in thought_content.lower():
                    reflections.append("I'm actively perceiving my environment - maintaining good situational awareness")
            
            return reflections
            
        except Exception as e:
            logger.error(f"Error reflecting on patterns: {e}")
            return []
    
    def _reflect_on_strategy(self, context: Dict[str, Any]) -> List[str]:
        """Reflect on overall strategy and approach"""
        try:
            reflections = []
            
            current_plan = context.get("current_plan")
            persona = context["persona"]
            
            # Analyze plan effectiveness
            if current_plan:
                if "search" in current_plan.lower():
                    reflections.append("My current strategy focuses on searching - good for discovery")
                elif "navigate" in current_plan.lower():
                    reflections.append("My current strategy focuses on navigation - good for exploring options")
                elif "examine" in current_plan.lower():
                    reflections.append("My current strategy focuses on examination - good for detailed analysis")
            
            # Consider persona characteristics
            age = getattr(persona, 'age', 0)
            if age > 0:
                if age < 30:
                    reflections.append("As a younger user, I might prefer quick, efficient interactions")
                elif age > 50:
                    reflections.append("As an older user, I might prefer more deliberate, careful interactions")
            
            # Consider shopping habits if available
            shopping_habits = getattr(persona, 'shopping_habits', '')
            if shopping_habits:
                if "research" in shopping_habits.lower():
                    reflections.append("Given my research-oriented shopping style, I should thoroughly evaluate options")
                elif "quick" in shopping_habits.lower() or "efficient" in shopping_habits.lower():
                    reflections.append("Given my preference for efficiency, I should focus on direct paths to my goal")
            
            return reflections
            
        except Exception as e:
            logger.error(f"Error reflecting on strategy: {e}")
            return []
    
    async def _llm_reflect(self, context: Dict[str, Any]) -> List[str]:
        """Use LLM for sophisticated reflection (TODO: implement)"""
        # TODO: Implement LLM-based reflection
        # This would use prompts to generate deeper insights
        return [] 