from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod
from enum import Enum
import numpy as np
import json


class ActionType(Enum):
    """Types of actions an agent can take"""
    SEARCH = "search"
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    BACK = "back"
    WAIT = "wait"
    STOP = "stop"


class AgentState(Enum):
    """Agent cognitive states"""
    IDLE = "idle"
    PERCEIVING = "perceiving"
    PLANNING = "planning"
    ACTING = "acting"
    REFLECTING = "reflecting"


@dataclass
class Action:
    """Base action class"""
    type: Optional[ActionType] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.type is None and hasattr(self, '_action_type'):
            self.type = self._action_type
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value if self.type else None,
            "parameters": self.parameters
        }


@dataclass
class SearchAction(Action):
    """Search action with query"""
    query: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.type = ActionType.SEARCH
        self.parameters["query"] = self.query


@dataclass
class ClickAction(Action):
    """Click action on element"""
    element_id: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.type = ActionType.CLICK
        self.parameters["element_id"] = self.element_id


@dataclass
class TypeAction(Action):
    """Type text into input"""
    element_id: str = ""
    text: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.type = ActionType.TYPE
        self.parameters["element_id"] = self.element_id
        self.parameters["text"] = self.text


@dataclass
class SelectAction(Action):
    """Select option from dropdown"""
    element_id: str = ""
    value: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.type = ActionType.SELECT
        self.parameters["element_id"] = self.element_id
        self.parameters["value"] = self.value


@dataclass
class StopAction(Action):
    """Stop simulation"""
    reason: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.type = ActionType.STOP
        self.parameters["reason"] = self.reason


@dataclass
class Observation:
    """Environment observation"""
    page_content: str = ""
    url: str = ""
    clickables: List[Dict[str, Any]] = field(default_factory=list)
    inputs: List[Dict[str, Any]] = field(default_factory=list)
    selects: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_content": self.page_content,
            "url": self.url,
            "clickables": self.clickables,
            "inputs": self.inputs,
            "selects": self.selects,
            "metadata": self.metadata,
            "error_message": self.error_message
        }


@dataclass
class Persona:
    """Agent persona with background and intent"""
    name: str
    background: str
    intent: str
    age: Optional[int] = None
    gender: Optional[str] = None
    income: Optional[List[int]] = None
    demographics: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Persona':
        """Create persona from dictionary (UXAgent format support)"""
        # Support UXAgent format
        if "persona" in data:
            background = data["persona"]
            name = background.split('\n')[0].replace("Persona: ", "") if background else "Unknown"
        else:
            background = data.get("background", "")
            name = data.get("name", "Unknown")
        
        return cls(
            name=name,
            background=background,
            intent=data.get("intent", ""),
            age=data.get("age"),
            gender=data.get("gender"),
            income=data.get("income"),
            demographics={
                k: v for k, v in data.items() 
                if k not in ["name", "background", "intent", "persona", "age", "gender", "income"]
            }
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "background": self.background,
            "intent": self.intent,
            "age": self.age,
            "gender": self.gender,
            "income": self.income,
            **self.demographics
        }


@dataclass
class MemoryPiece:
    """Individual memory piece with metadata"""
    content: str
    memory_type: str  # observation, action, plan, thought, reflection
    timestamp: int = 0
    importance: float = 0.5
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "memory_type": self.memory_type,
            "timestamp": self.timestamp,
            "importance": self.importance,
            "metadata": self.metadata
        }


@dataclass
class SimulationConfig:
    """Configuration for simulation runs"""
    max_steps: int = 50
    environment_type: str = "mock"
    environment_config: Dict[str, Any] = field(default_factory=dict)
    policy_type: str = "component"
    policy_config: Dict[str, Any] = field(default_factory=dict)
    llm_provider: str = "openai"
    output_dir: str = "output"
    save_traces: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationConfig':
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_steps": self.max_steps,
            "environment_type": self.environment_type,
            "environment_config": self.environment_config,
            "policy_type": self.policy_type,
            "policy_config": self.policy_config,
            "llm_provider": self.llm_provider,
            "output_dir": self.output_dir,
            "save_traces": self.save_traces
        } 