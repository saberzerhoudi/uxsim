from abc import ABC, abstractmethod
from typing import Dict, Any

from ..core.types import Action, Observation
from ..core.exceptions import EnvironmentException


class BaseEnvironment(ABC):
    """Base class for all environments"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.current_state = {}
    
    @abstractmethod
    async def observe(self) -> Observation:
        """
        Get current observation from environment
        
        Returns:
            Current observation
        """
        raise NotImplementedError
    
    @abstractmethod
    async def step(self, action: Action) -> Observation:
        """
        Execute action in environment and return new observation
        
        Args:
            action: Action to execute
            
        Returns:
            New observation after action
        """
        raise NotImplementedError
    
    @abstractmethod
    async def reset(self) -> Observation:
        """
        Reset environment to initial state
        
        Returns:
            Initial observation
        """
        raise NotImplementedError
    
    async def close(self):
        """Clean up environment resources"""
        pass
    
    def get_state(self) -> Dict[str, Any]:
        """Get current environment state"""
        return self.current_state.copy()


class MockEnvironment(BaseEnvironment):
    """Mock environment for testing"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.step_count = 0
        self.max_steps = config.get("max_steps", 10)
        self.mock_pages = config.get("mock_pages", [])
        self.current_page_index = 0
    
    async def observe(self) -> Observation:
        """Return current mock observation"""
        if self.current_page_index < len(self.mock_pages):
            page_data = self.mock_pages[self.current_page_index]
            return Observation(
                page_content=page_data.get("content", "Mock page content"),
                url=page_data.get("url", f"http://mock.com/page{self.current_page_index}"),
                clickables=page_data.get("clickables", [
                    {"name": "link1", "text": "Click me", "id": "link1"}
                ]),
                inputs=page_data.get("inputs", []),
                selects=page_data.get("selects", [])
            )
        else:
            return Observation(
                page_content="End of mock pages",
                url="http://mock.com/end",
                clickables=[],
                inputs=[],
                selects=[]
            )
    
    async def step(self, action: Action) -> Observation:
        """Execute mock action and return new observation"""
        self.step_count += 1
        
        # Simple mock behavior: advance to next page on any action
        if action.type.value in ["click", "search", "type"]:
            self.current_page_index += 1
        
        # Mock error occasionally
        if self.step_count > self.max_steps:
            obs = await self.observe()
            obs.error_message = "Mock environment reached max steps"
            return obs
        
        return await self.observe()
    
    async def reset(self) -> Observation:
        """Reset mock environment"""
        self.step_count = 0
        self.current_page_index = 0
        return await self.observe() 