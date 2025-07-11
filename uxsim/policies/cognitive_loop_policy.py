import asyncio
import logging
from typing import List, Optional, Dict, Any
import json

from ..core.types import Action, Observation, Persona, ActionType
from ..agent import Agent
from ..llm import async_chat
from .base_policy import BaseDecisionPolicy

logger = logging.getLogger(__name__)


class CognitiveLoopPolicy(BaseDecisionPolicy):
    """
    Full cognitive loop policy implementing Perceive-Plan-Reflect-Act cycle
    Uses real LLM-based agent with sophisticated reasoning
    """
    
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.agent: Optional[Agent] = None
        self.last_action: Optional[Action] = None
        self.reflection_frequency = config.get("reflection_frequency", 3) if config else 3
        self.step_count = 0
        
    def set_agent(self, agent: Agent):
        """Set the agent instance"""
        self.agent = agent
        
    async def decide(self, observation: Observation) -> Action:
        """
        Full cognitive loop: Perceive → Plan → Reflect → Act
        """
        try:
            if not self.agent:
                raise ValueError("Agent not set for cognitive loop policy")
            
            logger.info("=== Cognitive Loop Step ===")
            
            # 1. PERCEIVE: Process current environment
            logger.info("🔍 PERCEIVE: Processing environment...")
            observations = await self.agent.perceive(observation)
            logger.info(f"Perceived {len(observations)} observations")
            
            # 2. FEEDBACK: Analyze last action if available
            if self.last_action and self.step_count > 0:
                logger.info("💭 FEEDBACK: Analyzing last action...")
                thoughts = await self.agent.feedback(observation, self.last_action)
                logger.info(f"Generated {len(thoughts)} feedback thoughts")
            
            # 3. PLAN: Create or update plan
            logger.info("📋 PLAN: Creating/updating plan...")
            plan = await self.agent.plan()
            logger.info(f"Plan: {plan[:100]}...")
            
            # 4. REFLECT: Periodic reflection on experiences
            if self.step_count % self.reflection_frequency == 0 and self.step_count > 0:
                logger.info("🤔 REFLECT: Analyzing recent experiences...")
                insights = await self.agent.reflect()
                logger.info(f"Generated {len(insights)} insights")
            
            # 5. ACT: Select actions based on plan and environment
            logger.info("⚡ ACT: Selecting actions...")
            actions = await self.agent.act(observation)
            
            if not actions:
                logger.warning("No actions generated, creating stop action")
                from ..core.types import StopAction
                actions = [StopAction(reason="No valid actions available")]
            
            # Take the first action
            action = actions[0]
            self.last_action = action
            
            # 6. UPDATE MEMORY: Update embeddings and importance scores
            logger.info("🧠 UPDATE: Updating memory...")
            await self.agent.update_memory()
            
            # Increment timestamp
            self.agent.memory.timestamp += 1
            self.step_count += 1
            
            logger.info(f"Selected action: {action.type.value if action.type else 'unknown'}")
            logger.info("=== End Cognitive Loop ===")
            
            return action
            
        except Exception as e:
            logger.error(f"Error in cognitive loop: {e}")
            # Fallback to stop action
            from ..core.types import StopAction
            return StopAction(reason=f"Error in cognitive loop: {e}")
    
    def get_state(self) -> dict:
        """Get current policy state"""
        state = {
            "policy_type": "cognitive_loop",
            "step_count": self.step_count,
            "reflection_frequency": self.reflection_frequency
        }
        
        if self.agent:
            state.update(self.agent.get_state())
            
        return state
    
    def reset(self):
        """Reset policy state"""
        self.last_action = None
        self.step_count = 0
        if self.agent:
            self.agent.memory.timestamp = 0

    async def decide_action(self, observation: Observation, state: Dict[str, Any]) -> Action:
        """
        LLM-powered cognitive loop decision making
        """
        try:
            # Get agent context
            agent_context = self.get_agent_context()
            
            # Prepare LLM input
            system_prompt = """You are an intelligent web agent. Analyze the current situation and decide on the next action.
            
Available actions:
- search[query]: Search for information
- click[element_id]: Click on an element
- type[element_id, text]: Type text into an input field
- select[element_id, value]: Select an option from a dropdown
- wait[time]: Wait for a specified time
- stop[reason]: Stop the simulation

Respond with JSON: {"action": "action_name", "parameters": {...}, "reasoning": "explanation"}"""

            user_prompt = f"""
Current situation:
- URL: {observation.url}
- Page content: {observation.page_content[:1000]}...
- Available clickables: {len(observation.clickables)} elements
- Agent persona: {agent_context.get('persona').name if agent_context.get('persona') else 'Unknown'}
- Intent: {agent_context.get('persona').intent if agent_context.get('persona') else 'Unknown'}
- Memory count: {agent_context.get('memory_count', 0)}

What should the agent do next?"""

            # Make LLM call
            response = await async_chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                json_mode=True
            )
            
            # Parse response
            result = json.loads(response)
            action_name = result.get("action", "wait")
            parameters = result.get("parameters", {})
            reasoning = result.get("reasoning", "No reasoning provided")
            
            logger.info(f"Cognitive loop decision: {action_name} - {reasoning}")
            
            # Map to ActionType
            action_type_map = {
                "search": ActionType.SEARCH,
                "click": ActionType.CLICK,
                "type": ActionType.TYPE,
                "select": ActionType.SELECT,
                "wait": ActionType.WAIT,
                "stop": ActionType.STOP
            }
            
            action_type = action_type_map.get(action_name, ActionType.WAIT)
            
            return Action(type=action_type, parameters=parameters)
            
        except Exception as e:
            logger.error(f"Error in cognitive loop decision: {e}")
            # Fallback to safe action
            return Action(
                type=ActionType.STOP,
                parameters={"reason": f"Cognitive loop error: {str(e)}"}
            ) 