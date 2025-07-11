"""
UXAgent-compatible Agent Policy with full cognitive loop
"""

import asyncio
import json
import logging
import pickle
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..agent import Agent
from ..core.types import Action, ActionType, Persona
from .base_policy import BaseDecisionPolicy

logger = logging.getLogger(__name__)


class AgentPolicy(BaseDecisionPolicy):
    """
    Full UXAgent-compatible agent policy with cognitive loop:
    perceive -> reflect -> wonder -> plan -> act
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.agent = None
        self.persona = None
        self.intent = None
        self.run_path = None
        self.action_trace_file = None
        self.env_trace_file = None
        self.slow_loop_task = None
        self.step_count = 0
        
        # Configuration options
        self.save_traces = config.get('save_traces', True)
        self.save_agent_state = config.get('save_agent_state', True)
        self.enable_reflection = config.get('enable_reflection', True)
        self.enable_memory_update = config.get('enable_memory_update', True)
        
        logger.info("AgentPolicy initialized with UXAgent-compatible cognitive loop")
    
    async def initialize(self, persona: Persona, output_dir: str):
        """Initialize the agent with persona and output directory"""
        self.persona = persona
        self.intent = persona.intent
        
        # Create agent with persona (uxsim Agent takes only Persona object)
        self.agent = Agent(persona)
        
        # Set up run directory and tracing (UXAgent-style)
        if output_dir:
            self.run_path = Path(output_dir)
        else:
            run_name = f"{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}_{uuid.uuid4().hex[:4]}"
            self.run_path = Path("runs") / run_name
        
        self.run_path.mkdir(parents=True, exist_ok=True)
        
        # Save persona and intent files (UXAgent-style)
        (self.run_path / "persona.txt").write_text(persona.background)
        (self.run_path / "intent.txt").write_text(persona.intent)
        
        # Initialize trace files
        if self.save_traces:
            self.action_trace_file = (self.run_path / "action_trace.txt").open("w")
            self.env_trace_file = (self.run_path / "env_trace.txt").open("w")
        
        logger.info(f"Agent initialized with persona: {persona.name}, intent: {persona.intent}")
        logger.info(f"Output directory: {self.run_path}")
    
    async def slow_loop(self):
        """Background loop for reflection and memory updates (UXAgent-style)"""
        while True:
            try:
                if self.enable_reflection:
                    await self.agent.reflect()
                # uxsim doesn't have wonder method, skip it
                if self.enable_memory_update:
                    await self.agent.update_memory()
                await asyncio.sleep(1)  # Small delay to prevent overwhelming
            except Exception as e:
                logger.warning(f"Error in slow loop: {e}")
                await asyncio.sleep(5)  # Longer delay on error
    
    async def decide_action(self, observation, state) -> Action:
        """
        Full UXAgent cognitive loop: perceive -> feedback -> reflect -> wonder -> plan -> act
        """
        try:
            # UXAgent cognitive loop adapted for uxsim Agent
            if self.agent.memory.timestamp != 0:  # Not first step
                # Run feedback and perceive in parallel (if feedback method exists)
                if hasattr(self.agent, 'feedback'):
                    await asyncio.gather(
                        self.agent.feedback(observation, self.last_action if hasattr(self, 'last_action') else None),
                        self.agent.perceive(observation)
                    )
                else:
                    await self.agent.perceive(observation)
            else:
                # First step - only perceive
                await self.agent.perceive(observation)
            
            # Start background slow loop if not started
            if self.slow_loop_task is None and self.enable_reflection:
                self.slow_loop_task = asyncio.create_task(self.slow_loop())
            
            # Plan next action
            await self.agent.plan()
            
            # Act
            actions = await self.agent.act(observation)
            
            # Save agent state (UXAgent-style)
            if self.save_agent_state:
                pickle.dump(
                    self.agent,
                    open(self.run_path / f"agent_{self.agent.memory.timestamp}.pkl", "wb"),
                )
                
                # Save memory trace
                if hasattr(self.agent, 'format_memories'):
                    memory_trace = "\n".join(self.agent.format_memories(self.agent.memory.memories, False))
                else:
                    memory_trace = "\n".join([f"{m.timestamp}: {m.content}" for m in self.agent.memory.memories])
                
                (self.run_path / f"memory_trace_{self.agent.memory.timestamp}.txt").write_text(memory_trace)
                
                # Save page HTML
                if observation.page_content:
                    (self.run_path / f"page_{self.agent.memory.timestamp}.html").write_text(
                        observation.page_content
                    )
            
            # Convert uxsim actions to uxsim format (already compatible)
            uxsim_action = actions[0] if actions else Action(type=ActionType.STOP, parameters={"reason": "No action from agent"})
            
            # Write action trace
            if self.action_trace_file:
                self.action_trace_file.write(json.dumps([a.to_dict() for a in actions]) + "\n")
                self.action_trace_file.flush()
            
            # Store last action for feedback
            self.last_action = uxsim_action
            
            # Increment memory timestamp
            self.agent.memory.timestamp += 1
            self.step_count += 1
            
            logger.info(f"Agent decision step {self.step_count}: {uxsim_action.type}")
            
            return uxsim_action
            
        except Exception as e:
            logger.error(f"Error in agent decision: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to stop action
            return Action(
                type=ActionType.STOP,
                parameters={"reason": f"Agent error: {str(e)}"}
            )
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            # Cancel slow loop
            if self.slow_loop_task:
                self.slow_loop_task.cancel()
                try:
                    await self.slow_loop_task
                except asyncio.CancelledError:
                    pass
                self.slow_loop_task = None
            
            # Close trace files
            if self.action_trace_file:
                self.action_trace_file.close()
                self.action_trace_file = None
            
            if self.env_trace_file:
                self.env_trace_file.close()
                self.env_trace_file = None
            
            logger.info("AgentPolicy cleanup completed")
            
        except Exception as e:
            logger.warning(f"Error during AgentPolicy cleanup: {e}")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current agent state"""
        state = {
            "step_count": self.step_count,
            "persona_name": self.persona.name if self.persona else None,
            "intent": self.intent,
            "run_path": str(self.run_path) if self.run_path else None
        }
        
        if self.agent and self.agent.memory:
            state.update({
                "memory_timestamp": self.agent.memory.timestamp,
                "memory_count": len(self.agent.memory.memories),
                "current_plan": self.agent.current_plan if self.agent.current_plan else None
            })
        
        return state 