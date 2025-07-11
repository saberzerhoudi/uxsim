import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any
import numpy as np

from .core.types import AgentState, Persona, MemoryPiece, Action, Observation, ActionType, SearchAction, ClickAction, TypeAction, SelectAction, StopAction
from .core.exceptions import AgentException, MemoryException
from .llm import async_chat, embed_text, LLMException
from .llm.prompts import (
    PERCEIVE_PROMPT, PLANNING_PROMPT, ACTION_PROMPT, 
    REFLECTION_PROMPT, FEEDBACK_PROMPT, MEMORY_IMPORTANCE_PROMPT
)

logger = logging.getLogger(__name__)


class Memory:
    """Enhanced memory system with embeddings and importance scoring"""
    
    def __init__(self, agent):
        self.agent = agent
        self.memories: List[MemoryPiece] = []
        self.embeddings: Optional[np.ndarray] = None
        self.importance_scores: Optional[np.ndarray] = None
        self.timestamp = 0
        
    async def add_memory(self, memory: MemoryPiece):
        """Add a memory piece to the system"""
        memory.timestamp = self.timestamp
        self.memories.append(memory)
        logger.debug(f"Added memory: {memory.content[:100]}...")
        
    async def update_embeddings_and_importance(self):
        """Update embeddings and importance scores for new memories using UXAgent's approach"""
        try:
            # Check if update is needed
            if len(self.embeddings) == len(self.memories):
                return
                
            logger.info(f"Updating embeddings and importance for {len(self.memories) - len(self.embeddings)} new memories")
            
            # Get memories that need embeddings
            start_idx = len(self.embeddings) if self.embeddings is not None else 0
            memory_to_embed = self.memories[start_idx:]
            
            if not memory_to_embed:
                return
            
            async def get_embeddings():
                """Get embeddings for new memories"""
                inputs = [m.content for m in memory_to_embed]
                embeds = await embed_text(inputs)
                embeds = np.array(embeds)
                
                # Store embeddings on memory pieces
                for i, m in enumerate(memory_to_embed):
                    m.embedding = embeds[i]
                return embeds
            
            async def update_importance():
                """Update importance scores for new memories"""
                memory_to_update = self.memories[len(self.importance_scores) if self.importance_scores is not None else 0:]
                
                new_importance = []
                for memory in memory_to_update:
                    try:
                        response = await async_chat([
                            {"role": "system", "content": MEMORY_IMPORTANCE_PROMPT},
                            {"role": "user", "content": json.dumps({
                                "persona": self.agent.persona.background,
                                "intent": self.agent.persona.intent,
                                "memory": memory.content,
                                "plan": getattr(self.agent, 'current_plan', None)
                            })}
                        ], json_mode=True, model="small")
                        
                        score_data = json.loads(response)
                        importance = score_data["score"] / 10.0  # Normalize to 0-1
                        new_importance.append(importance)
                        memory.importance = importance
                        
                    except Exception as e:
                        logger.warning(f"Failed to score memory importance: {e}")
                        new_importance.append(0.5)  # Default importance
                        memory.importance = 0.5
                
                return np.array(new_importance)
            
            # Run both operations concurrently
            embeds, new_importance = await asyncio.gather(
                get_embeddings(), update_importance()
            )
            
            # Update arrays synchronously to avoid mismatches
            if self.embeddings is None or len(self.embeddings) == 0:
                self.embeddings = embeds
            else:
                self.embeddings = np.concatenate([self.embeddings, embeds])
                
            if self.importance_scores is None:
                self.importance_scores = new_importance
            else:
                self.importance_scores = np.concatenate([self.importance_scores, new_importance])
                
            logger.info(f"Updated embeddings: {len(self.embeddings)}, memories: {len(self.memories)}")
                
        except Exception as e:
            logger.error(f"Error updating memory embeddings/importance: {e}")
    
    async def retrieve_relevant(self, query: str, n: int = 10, include_recent: bool = True, kind_weight: dict = None) -> List[MemoryPiece]:
        """Retrieve most relevant memories using UXAgent's approach with kind weighting"""
        try:
            if not self.memories:
                return []
            
            # Always include very recent memories (UXAgent pattern)
            results = []
            if include_recent:
                recent_observations = [
                    m for m in self.memories 
                    if m.memory_type == "observation" and m.timestamp >= self.timestamp - 3
                ]
                recent_actions = [
                    m for m in self.memories
                    if m.memory_type == "action" and m.timestamp >= self.timestamp - 5  
                ]
                results.extend(recent_observations + recent_actions)
            
            # Update embeddings if needed
            await self.update_embeddings_and_importance()
            
            # If no embeddings yet, just return recent
            if self.embeddings is None or len(self.embeddings) == 0:
                return results[:n]
            
            # Ensure we have consistent arrays
            smallest_size = min(len(self.embeddings), len(self.memories), 
                               len(self.importance_scores) if self.importance_scores is not None else len(self.memories))
            
            if smallest_size == 0:
                return results[:n]
            
            # Get query embedding
            query_embedding = (await embed_text([query]))[0]
            query_embedding = np.array(query_embedding)
            
            # Calculate similarity scores
            similarities = np.dot(self.embeddings[:smallest_size], query_embedding)
            
            # Calculate recency scores (UXAgent uses timestamp differences)
            recencies = np.array([m.timestamp - self.timestamp for m in self.memories[:smallest_size]])
            recencies = np.exp(recencies)
            
            # Apply kind weights (UXAgent pattern)
            if kind_weight is None:
                kind_weight = {"action": 10, "plan": 10, "thought": 10, "reflection": 10}
            
            kind_weights = np.array([kind_weight.get(m.memory_type, 1) for m in self.memories[:smallest_size]])
            
            # Combine scores (UXAgent formula)
            importance_scores = self.importance_scores[:smallest_size] if self.importance_scores is not None else np.ones(smallest_size)
            scores = (similarities + recencies + importance_scores) * kind_weights
            
            # Get top indices
            top_indices = np.argsort(-scores)[:n]
            retrieved_memories = [self.memories[i] for i in top_indices if i < len(self.memories)]
            
            # Combine with recent memories (remove duplicates)
            all_memories = results + [m for m in retrieved_memories if m not in results]
            
            return all_memories[:n]
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return self.memories[-5:] if self.memories else []  # Fallback to recent memories


class Agent:
    """Enhanced agent with real LLM-based cognitive loop"""
    
    def __init__(self, persona: Persona):
        self.persona = persona
        self.memory = Memory(self)
        self.current_plan: Optional[str] = None
        self.current_plan_rationale: Optional[str] = None
        self.next_step: Optional[str] = None
        self.state = AgentState.IDLE
        
        logger.info(f"Created agent with persona: {persona.name}")
    
    async def perceive(self, observation: Observation) -> List[str]:
        """Perceive and process the current environment"""
        try:
            self.state = AgentState.PERCEIVING
            logger.info("Agent perceiving environment...")
            
            # Prepare environment data for LLM
            env_data = {
                "url": observation.url,
                "page_content": observation.page_content,
                "clickables": [{"id": c.get("id", ""), "text": c.get("text", "")} for c in observation.clickables],
                "inputs": [{"id": i.get("id", ""), "type": i.get("type", ""), "placeholder": i.get("placeholder", "")} for i in observation.inputs],
                "selects": [{"id": s.get("id", ""), "options": s.get("options", [])} for s in observation.selects]
            }
            
            # Get perceptions from LLM
            response = await async_chat([
                {"role": "system", "content": PERCEIVE_PROMPT},
                {"role": "user", "content": json.dumps(env_data)}
            ], json_mode=True, model="small")
            
            perception_data = json.loads(response)
            observations = perception_data.get("observations", [])
            
            # Add observations to memory
            for obs in observations:
                memory_piece = MemoryPiece(
                    content=obs,
                    memory_type="observation",
                    timestamp=self.memory.timestamp
                )
                await self.memory.add_memory(memory_piece)
            
            logger.info(f"Perceived {len(observations)} observations")
            return observations
            
        except Exception as e:
            logger.error(f"Error in perceive: {e}")
            return []
    
    async def plan(self) -> str:
        """Create or update the current plan using UXAgent's approach"""
        try:
            self.state = AgentState.PLANNING
            logger.info("Agent planning...")
            
            # Retrieve relevant memories for planning with UXAgent-style weighting
            planning_query = f"{self.persona.intent} {self.current_plan or ''}"
            relevant_memories = await self.memory.retrieve_relevant(
                planning_query, 
                n=20,
                include_recent=True,
                kind_weight={"action": 10, "plan": 10, "thought": 10, "reflection": 10}
            )
            
            # Format memories for LLM
            memory_strings = [
                f"timestamp: {m.timestamp}; kind: {m.memory_type}; content: {m.content}" 
                for m in relevant_memories
            ]
            
            # Prepare planning data
            planning_data = {
                "persona": self.persona.background,
                "intent": self.persona.intent,
                "memories": memory_strings,
                "current_timestamp": self.memory.timestamp,
                "old_plan": self.current_plan or "N/A"
            }
            
            # Get plan from LLM with retry logic for better results
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = await async_chat([
                        {"role": "system", "content": PLANNING_PROMPT},
                        {"role": "user", "content": json.dumps(planning_data)}
                    ], json_mode=True, model="large")
                    
                    plan_data = json.loads(response)
                    
                    # Validate response has required fields
                    if all(key in plan_data for key in ["plan", "rationale", "next_step"]):
                        self.current_plan = plan_data.get("plan", "")
                        self.current_plan_rationale = plan_data.get("rationale", "")
                        self.next_step = plan_data.get("next_step", "")
                        break
                    else:
                        logger.warning(f"Invalid plan response on attempt {attempt + 1}: {plan_data}")
                        
                except Exception as e:
                    logger.warning(f"Plan attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        # Fallback plan
                        self.current_plan = "Continue with current approach"
                        self.current_plan_rationale = "Using fallback plan due to LLM errors"
                        self.next_step = "Try the next logical action"
            
            # Add plan to memory
            plan_memory = MemoryPiece(
                content=f"Plan: {self.current_plan}",
                memory_type="plan",
                timestamp=self.memory.timestamp
            )
            await self.memory.add_memory(plan_memory)
            
            # Add rationale as thought
            if self.current_plan_rationale:
                thought_memory = MemoryPiece(
                    content=self.current_plan_rationale,
                    memory_type="thought",
                    timestamp=self.memory.timestamp
                )
                await self.memory.add_memory(thought_memory)
            
            logger.info(f"Created plan: {self.current_plan[:100]}...")
            logger.info(f"Next step: {self.next_step}")
            return self.current_plan
            
        except Exception as e:
            logger.error(f"Error in plan: {e}")
            return "Continue with current approach"
    
    async def act(self, observation: Observation) -> List[Action]:
        """Select and return actions using UXAgent's approach with better memory retrieval"""
        try:
            self.state = AgentState.ACTING
            logger.info("Agent selecting actions...")
            
            # Use UXAgent-style memory retrieval with specific weighting for actions
            action_query = f"{self.next_step} {self.persona.intent}"
            relevant_memories = await self.memory.retrieve_relevant(
                action_query, 
                n=15,
                include_recent=True,
                kind_weight={"observation": 0, "action": 10, "thought": 10}  # UXAgent pattern
            )
            
            # Format memories with UXAgent-style formatting
            memory_strings = [
                f"timestamp: {m.timestamp}; kind: {m.memory_type}; content: {m.content}"
                for m in relevant_memories
            ]
            
            # Enhanced action data with more context to help agent make better decisions
            action_data = {
                "persona": self.persona.background,
                "intent": self.persona.intent,
                "plan": self.current_plan,
                "next_step": self.next_step,
                "current_timestamp": self.memory.timestamp,
                "environment": {
                    "url": observation.url,
                    "page_content": observation.page_content[:2000],  # Limit content
                    "clickables": [
                        {"id": c.get("id", ""), "text": c.get("text", ""), "name": c.get("name", "")} 
                        if isinstance(c, dict) else {"id": str(c), "text": str(c), "name": str(c)}
                        for c in observation.clickables
                    ],
                    "inputs": [
                        {"id": i.get("id", ""), "type": i.get("type", ""), "placeholder": i.get("placeholder", ""), "name": i.get("name", "")} 
                        if isinstance(i, dict) else {"id": str(i), "type": "text", "placeholder": "", "name": str(i)}
                        for i in observation.inputs
                    ],
                    "selects": [
                        {"id": s.get("id", ""), "options": s.get("options", []), "name": s.get("name", "")} 
                        if isinstance(s, dict) else {"id": str(s), "options": [], "name": str(s)}
                        for s in observation.selects
                    ]
                },
                "recent_memories": memory_strings
            }
            
            # Get actions from LLM
            response = await async_chat([
                {"role": "system", "content": ACTION_PROMPT},
                {"role": "user", "content": json.dumps(action_data)}
            ], json_mode=True, model="large")
            
            action_data = json.loads(response)
            actions = []
            
            # Define action type mapping from string to enum
            action_type_mapping = {
                "search": ActionType.SEARCH,
                "click": ActionType.CLICK,
                "type": ActionType.TYPE,
                "select": ActionType.SELECT,
                "back": ActionType.BACK,
                "wait": ActionType.WAIT,
                "stop": ActionType.STOP
            }
            
            for action_dict in action_data.get("actions", []):
                action_type_str = action_dict.get("type", "").lower()
                action_type = action_type_mapping.get(action_type_str, ActionType.STOP)
                
                # Create proper Action subclass based on type
                if action_type == ActionType.SEARCH:
                    action = SearchAction(
                        query=action_dict.get("query", action_dict.get("text", ""))
                    )
                elif action_type == ActionType.CLICK:
                    action = ClickAction(
                        element_id=action_dict.get("element_id", action_dict.get("selector", ""))
                    )
                elif action_type == ActionType.TYPE:
                    action = TypeAction(
                        element_id=action_dict.get("element_id", action_dict.get("selector", "")),
                        text=action_dict.get("text", action_dict.get("value", ""))
                    )
                elif action_type == ActionType.SELECT:
                    action = SelectAction(
                        element_id=action_dict.get("element_id", action_dict.get("selector", "")),
                        value=action_dict.get("value", "")
                    )
                else:
                    action = StopAction(
                        reason=action_dict.get("reason", action_dict.get("description", "Agent decided to stop"))
                    )
                
                actions.append(action)
                
                # Add action to memory with UXAgent-style description
                action_memory = MemoryPiece(
                    content=f"Action: {action_dict.get('description', str(action_dict))}",
                    memory_type="action",
                    timestamp=self.memory.timestamp
                )
                await self.memory.add_memory(action_memory)
            
            logger.info(f"Selected {len(actions)} actions")
            return actions
            
        except Exception as e:
            logger.error(f"Error in act: {e}")
            return []
    
    async def reflect(self) -> List[str]:
        """Reflect on recent experiences and generate insights"""
        try:
            self.state = AgentState.REFLECTING
            logger.info("Agent reflecting...")
            
            # Get recent memories for reflection
            recent_memories = self.memory.memories[-10:] if self.memory.memories else []
            
            if not recent_memories:
                return []
            
            # Format memories
            memory_strings = [
                f"[{m.memory_type}] {m.content}" for m in recent_memories
            ]
            
            # Prepare reflection data
            reflection_data = {
                "current_timestamp": self.memory.timestamp,
                "memories": memory_strings,
                "persona": self.persona.background
            }
            
            # Get reflections from LLM
            response = await async_chat([
                {"role": "system", "content": REFLECTION_PROMPT},
                {"role": "user", "content": json.dumps(reflection_data)}
            ], json_mode=True, model="small")
            
            reflection_data = json.loads(response)
            insights = reflection_data.get("insights", [])
            
            # Add insights to memory
            for insight in insights:
                insight_memory = MemoryPiece(
                    content=insight,
                    memory_type="reflection",
                    timestamp=self.memory.timestamp
                )
                await self.memory.add_memory(insight_memory)
            
            logger.info(f"Generated {len(insights)} insights")
            return insights
            
        except Exception as e:
            logger.error(f"Error in reflect: {e}")
            return []
    
    async def feedback(self, observation: Observation, last_action: Action) -> List[str]:
        """Analyze the outcome of the last action"""
        try:
            logger.info("Agent processing feedback...")
            
            # Prepare feedback data
            feedback_data = {
                "persona": self.persona.background,
                "last_action": {
                    "type": last_action.type.value if last_action.type else "unknown",
                    "parameters": last_action.parameters
                },
                "last_plan": self.current_plan,
                "observation": {
                    "url": observation.url,
                    "page_content": observation.page_content[:1000],  # Limit content
                    "error_message": observation.error_message
                }
            }
            
            # Get feedback from LLM
            response = await async_chat([
                {"role": "system", "content": FEEDBACK_PROMPT},
                {"role": "user", "content": json.dumps(feedback_data)}
            ], json_mode=True, model="small")
            
            feedback_data = json.loads(response)
            thoughts = feedback_data.get("thoughts", [])
            
            # Add thoughts to memory
            for thought in thoughts:
                thought_memory = MemoryPiece(
                    content=thought,
                    memory_type="thought",
                    timestamp=self.memory.timestamp
                )
                await self.memory.add_memory(thought_memory)
            
            logger.info(f"Generated {len(thoughts)} feedback thoughts")
            return thoughts
            
        except Exception as e:
            logger.error(f"Error in feedback: {e}")
            return []
    
    async def update_memory(self):
        """Update memory embeddings and importance scores"""
        try:
            await self.memory.update_embeddings_and_importance()
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current agent state"""
        return {
            "persona": {
                "name": self.persona.name,
                "intent": self.persona.intent
            },
            "current_plan": self.current_plan,
            "next_step": self.next_step,
            "memory_count": len(self.memory.memories),
            "timestamp": self.memory.timestamp,
            "state": self.state.value
        } 