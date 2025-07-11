import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

from .core.types import Persona, SimulationConfig, Action, ActionType
from .core.exceptions import SimulationException
from .agent import Agent
from .environments.base_env import BaseEnvironment
from .environments.web_browser_env import WebBrowserEnv
from .policies.base_policy import BaseDecisionPolicy
from .policies.component_policy import ComponentPolicy
from .policies.cognitive_loop_policy import CognitiveLoopPolicy
from .policies.agent_policy import AgentPolicy
from .llm import set_provider

logger = logging.getLogger(__name__)


class Simulation:
    """
    Central simulation orchestrator implementing unified workflow
    """
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.persona: Optional[Persona] = None
        self.agent: Optional[Agent] = None
        self.environment: Optional[BaseEnvironment] = None
        self.policy: Optional[BaseDecisionPolicy] = None
        self.step_count = 0
        self.is_running = False
        self.results = []
        
        # Set up LLM provider
        set_provider(config.llm_provider)
        
        # Create output directory
        os.makedirs(config.output_dir, exist_ok=True)
        
        logger.info(f"Initialized simulation with config: {config.to_dict()}")
    
    def load_persona(self, persona_path: str) -> Persona:
        """Load persona from file"""
        try:
            with open(persona_path, 'r') as f:
                persona_data = json.load(f)
            
            self.persona = Persona.from_dict(persona_data)
            logger.info(f"Loaded persona: {self.persona.name}")
            return self.persona
            
        except Exception as e:
            logger.error(f"Failed to load persona from {persona_path}: {e}")
            raise SimulationException(f"Failed to load persona: {e}")
    
    def create_environment(self) -> BaseEnvironment:
        """Create environment based on configuration"""
        try:
            env_type = self.config.environment_type.lower()
            env_config = self.config.environment_config
            
            if env_type == "mock":
                from .environments.base_env import MockEnvironment
                self.environment = MockEnvironment(env_config)
            elif env_type == "web_browser":
                self.environment = WebBrowserEnv(env_config)
            else:
                raise SimulationException(f"Unknown environment type: {env_type}")
            
            logger.info(f"Created {env_type} environment")
            return self.environment
            
        except Exception as e:
            logger.error(f"Failed to create environment: {e}")
            raise SimulationException(f"Failed to create environment: {e}")
    
    def create_agent(self) -> Agent:
        """Create agent with persona"""
        try:
            if not self.persona:
                raise SimulationException("Persona must be loaded before creating agent")
            
            self.agent = Agent(self.persona)
            logger.info(f"Created agent for persona: {self.persona.name}")
            return self.agent
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise SimulationException(f"Failed to create agent: {e}")
    
    def create_policy(self) -> BaseDecisionPolicy:
        """Create decision policy based on configuration"""
        try:
            policy_type = self.config.policy_type.lower()
            policy_config = self.config.policy_config
            
            if policy_type == "component":
                self.policy = ComponentPolicy(policy_config)
            elif policy_type == "cognitive_loop":
                self.policy = CognitiveLoopPolicy(policy_config)
            elif policy_type == "agent":
                self.policy = AgentPolicy(policy_config)
            else:
                raise SimulationException(f"Unknown policy type: {policy_type}")
            
            # Set agent for policy if it supports it
            if hasattr(self.policy, 'set_agent') and self.agent:
                self.policy.set_agent(self.agent)
            
            logger.info(f"Created {policy_type} policy")
            return self.policy
            
        except Exception as e:
            logger.error(f"Failed to create policy: {e}")
            raise SimulationException(f"Failed to create policy: {e}")
    
    async def initialize_policy(self):
        """Initialize policy with persona and output directory (for AgentPolicy)"""
        if hasattr(self.policy, 'initialize') and self.persona:
            await self.policy.initialize(self.persona, self.config.output_dir)
            logger.info("Policy initialized with persona and output directory")
        elif hasattr(self.policy, 'initialize') and not self.persona:
            logger.info("Policy initialization skipped - persona not available yet")
    
    async def initialize(self):
        """Initialize simulation components (without running)"""
        try:
            logger.info("=== Initializing UXSim Components ===")
            
            # Create components
            self.create_environment()
            if self.persona:  # Only create agent if persona is set
                self.create_agent()
                self.create_policy()
                # Initialize policy (for AgentPolicy) only if persona is available
                await self.initialize_policy()
            else:
                # Create policy without agent if no persona yet
                self.create_policy()
            
            # Initialize environment
            await self.environment.reset()
            logger.info("Simulation components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize simulation: {e}")
            raise SimulationException(f"Failed to initialize simulation: {e}")
    
    async def run_with_persona(self, persona: Persona) -> Dict[str, Any]:
        """
        Run simulation with a Persona object directly (instead of loading from file)
        """
        try:
            start_time = time.time()
            self.is_running = True
            
            logger.info("=== Starting UXSim Simulation ===")
            
            # 1. Set persona directly
            self.persona = persona
            logger.info(f"Using persona: {self.persona.name}")
            
            # 2. Create components (if not already created)
            if not self.environment:
                self.create_environment()
            if not self.agent:
                self.create_agent()
            if not self.policy:
                self.create_policy()
            
            # Set agent for policy if it supports it and wasn't done before
            if hasattr(self.policy, 'set_agent') and self.agent and not hasattr(self.policy, 'agent'):
                self.policy.set_agent(self.agent)
            
            # 2.5. Initialize policy (for AgentPolicy)
            await self.initialize_policy()
            
            # 3. Initialize environment (if not already done)
            observation = await self.environment.reset()
            logger.info(f"Environment initialized at: {observation.url}")
            
            # 4. Main simulation loop
            logger.info("Starting simulation loop...")
            
            while self.step_count < self.config.max_steps and self.is_running:
                try:
                    logger.info(f"\n--- Step {self.step_count + 1} ---")
                    
                    # Agent decides on action using policy
                    action = await self.policy.decide_action(observation, self.agent.get_state() if self.agent else {})
                    
                    # Record step
                    step_result = {
                        "step": self.step_count + 1,
                        "observation": observation.to_dict(),
                        "action": action.to_dict(),
                        "timestamp": time.time()
                    }
                    
                    # Check for stop action
                    if action.type == ActionType.STOP:
                        logger.info("Agent requested to stop simulation")
                        step_result["stop_reason"] = action.parameters.get("reason", "Agent completed task")
                        self.results.append(step_result)
                        break
                    
                    # Execute action in environment
                    observation = await self.environment.step(action)
                    
                    # Handle errors
                    if observation.error_message:
                        logger.warning(f"Environment error: {observation.error_message}")
                        step_result["error"] = observation.error_message
                    
                    self.results.append(step_result)
                    self.step_count += 1
                    
                    # Small delay between steps
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error in simulation step {self.step_count + 1}: {e}")
                    error_result = {
                        "step": self.step_count + 1,
                        "error": str(e),
                        "timestamp": time.time()
                    }
                    self.results.append(error_result)
                    break
            
            # 5. Finalize simulation
            end_time = time.time()
            duration = end_time - start_time
            
            # Create final results
            final_results = {
                "simulation_id": f"sim_{int(start_time)}",
                "persona": self.persona.to_dict(),
                "config": self.config.to_dict(),
                "steps": self.results,
                "total_steps": self.step_count,
                "duration_seconds": duration,
                "status": "completed" if self.step_count < self.config.max_steps else "max_steps_reached",
                "completed": self.step_count < self.config.max_steps,
                "agent_state": self.agent.get_state() if self.agent else {},
                "policy_state": self.policy.get_state() if hasattr(self.policy, 'get_state') else {}
            }
            
            # Save results if configured
            if self.config.save_traces:
                await self._save_results(final_results)
            
            logger.info(f"=== Simulation Complete ===")
            logger.info(f"Steps: {self.step_count}/{self.config.max_steps}")
            logger.info(f"Duration: {duration:.2f}s")
            logger.info(f"Status: {final_results['status']}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            raise SimulationException(f"Simulation failed: {e}")
        
        finally:
            self.is_running = False
            # Clean up resources
            if self.policy and hasattr(self.policy, 'cleanup'):
                try:
                    await self.policy.cleanup()
                    logger.info("Policy cleanup completed")
                except Exception as e:
                    logger.warning(f"Error during policy cleanup: {e}")
            
            logger.info("Simulation cleanup completed")
    
    async def cleanup(self):
        """Clean up simulation resources"""
        try:
            # Clean up policy
            if self.policy and hasattr(self.policy, 'cleanup'):
                await self.policy.cleanup()
            
            # Clean up environment
            if self.environment:
                await self.environment.close()
            
            logger.info("Simulation cleanup completed")
            
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
    
    async def run(self, persona_path: str) -> Dict[str, Any]:
        """
        Run complete simulation
        """
        try:
            start_time = time.time()
            self.is_running = True
            
            logger.info("=== Starting UXSim Simulation ===")
            
            # 1. Load persona
            self.load_persona(persona_path)
            
            # 2. Create components
            self.create_environment()
            self.create_agent()
            self.create_policy()
            
            # 2.5. Initialize policy (for AgentPolicy)
            await self.initialize_policy()
            
            # 3. Initialize environment
            observation = await self.environment.reset()
            logger.info(f"Environment initialized at: {observation.url}")
            
            # 4. Main simulation loop
            logger.info("Starting simulation loop...")
            
            while self.step_count < self.config.max_steps and self.is_running:
                try:
                    logger.info(f"\n--- Step {self.step_count + 1} ---")
                    
                    # Agent decides on action using policy
                    action = await self.policy.decide_action(observation, self.agent.get_state() if self.agent else {})
                    
                    # Record step
                    step_result = {
                        "step": self.step_count + 1,
                        "observation": observation.to_dict(),
                        "action": action.to_dict(),
                        "timestamp": time.time()
                    }
                    
                    # Check for stop action
                    if action.type == ActionType.STOP:
                        logger.info("Agent requested to stop simulation")
                        step_result["stop_reason"] = action.parameters.get("reason", "Agent completed task")
                        self.results.append(step_result)
                        break
                    
                    # Execute action in environment
                    observation = await self.environment.step(action)
                    
                    # Handle errors
                    if observation.error_message:
                        logger.warning(f"Environment error: {observation.error_message}")
                        step_result["error"] = observation.error_message
                    
                    self.results.append(step_result)
                    self.step_count += 1
                    
                    # Small delay between steps
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error in simulation step {self.step_count + 1}: {e}")
                    error_result = {
                        "step": self.step_count + 1,
                        "error": str(e),
                        "timestamp": time.time()
                    }
                    self.results.append(error_result)
                    break
            
            # 5. Finalize simulation
            end_time = time.time()
            duration = end_time - start_time
            
            # Create final results
            final_results = {
                "simulation_id": f"sim_{int(start_time)}",
                "persona": self.persona.to_dict(),
                "config": self.config.to_dict(),
                "steps": self.results,
                "total_steps": self.step_count,
                "duration_seconds": duration,
                "completed": self.step_count < self.config.max_steps,
                "agent_state": self.agent.get_state() if self.agent else {},
                "policy_state": self.policy.get_state() if hasattr(self.policy, 'get_state') else {}
            }
            
            # Save results if configured
            if self.config.save_traces:
                await self._save_results(final_results)
            
            logger.info(f"=== Simulation Complete ===")
            logger.info(f"Steps: {self.step_count}/{self.config.max_steps}")
            logger.info(f"Duration: {duration:.2f}s")
            logger.info(f"Success: {final_results['completed']}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            raise SimulationException(f"Simulation failed: {e}")
        
        finally:
            self.is_running = False
            # Clean up resources
            if self.policy and hasattr(self.policy, 'cleanup'):
                try:
                    await self.policy.cleanup()
                    logger.info("Policy cleanup completed")
                except Exception as e:
                    logger.warning(f"Error during policy cleanup: {e}")
            
            # Clean up environment
            if self.environment:
                await self.environment.close()
            
            logger.info("Simulation cleanup completed")
    
    async def _save_results(self, results: Dict[str, Any]):
        """Save simulation results to files"""
        try:
            output_path = Path(self.config.output_dir)
            
            # Save main results
            results_file = output_path / "simulation_results.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            # Save agent memory if available
            if self.agent and self.agent.memory.memories:
                memory_file = output_path / "agent_memory.json"
                memory_data = [m.to_dict() for m in self.agent.memory.memories]
                with open(memory_file, 'w') as f:
                    json.dump(memory_data, f, indent=2, default=str)
            
            # Save step-by-step trace
            trace_file = output_path / "step_trace.json"
            with open(trace_file, 'w') as f:
                json.dump(results["steps"], f, indent=2, default=str)
            
            logger.info(f"Results saved to {output_path}")
            
        except Exception as e:
            logger.warning(f"Failed to save results: {e}")
    
    def stop(self):
        """Stop the simulation"""
        self.is_running = False
        logger.info("Simulation stop requested")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current simulation status"""
        return {
            "is_running": self.is_running,
            "step_count": self.step_count,
            "max_steps": self.config.max_steps,
            "persona_loaded": self.persona is not None,
            "agent_created": self.agent is not None,
            "environment_created": self.environment is not None,
            "policy_created": self.policy is not None
        } 