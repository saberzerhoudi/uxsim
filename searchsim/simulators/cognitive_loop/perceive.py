import json
import logging
from typing import List, Dict, Any

from ...core.types import Observation

logger = logging.getLogger(__name__)


class PerceptionModule:
    """Module for enhanced perception in cognitive loop"""
    
    def __init__(self, llm_provider: str = "openai"):
        self.llm_provider = llm_provider
    
    async def perceive(self, observation: Observation, context: Dict[str, Any]) -> List[str]:
        """
        Process observation and extract meaningful perceptions
        
        Args:
            observation: Current environment observation
            context: Agent context including persona and memory
            
        Returns:
            List of perception strings
        """
        try:
            perceptions = []
            
            # Basic perceptions about the current state
            if observation.url:
                perceptions.append(f"Currently on page: {observation.url}")
            
            if observation.page_content:
                content_length = len(observation.page_content)
                perceptions.append(f"Page contains {content_length} characters of content")
            
            # Analyze available interactions
            if observation.clickables:
                perceptions.append(f"Found {len(observation.clickables)} clickable elements")
                
                # Analyze clickable relevance to intent
                intent = context["persona"].intent.lower()
                relevant_clickables = []
                
                for clickable in observation.clickables[:5]:  # Analyze top 5
                    text = clickable.get("text", "").lower()
                    name = clickable.get("name", "").lower()
                    
                    # Simple relevance check
                    intent_words = intent.split()
                    relevance_score = sum(1 for word in intent_words if word in f"{text} {name}")
                    
                    if relevance_score > 0:
                        relevant_clickables.append({
                            "element": clickable,
                            "relevance": relevance_score,
                            "text": text[:50]  # Truncate for readability
                        })
                
                if relevant_clickables:
                    perceptions.append(f"Found {len(relevant_clickables)} potentially relevant clickable elements")
                    # Add details about most relevant
                    best = max(relevant_clickables, key=lambda x: x["relevance"])
                    perceptions.append(f"Most relevant element: '{best['text']}' (relevance: {best['relevance']})")
            
            if observation.inputs:
                perceptions.append(f"Found {len(observation.inputs)} input fields")
            
            if observation.selects:
                perceptions.append(f"Found {len(observation.selects)} dropdown menus")
            
            # Error analysis
            if observation.error_message:
                perceptions.append(f"Error detected: {observation.error_message}")
            
            # Content relevance analysis
            if observation.page_content and context["persona"].intent:
                relevance_score = self._analyze_content_relevance(
                    observation.page_content, 
                    context["persona"].intent
                )
                perceptions.append(f"Page relevance to intent: {relevance_score:.2f}")
                
                if relevance_score > 0.7:
                    perceptions.append("This page appears highly relevant to the user's intent")
                elif relevance_score > 0.3:
                    perceptions.append("This page has some relevance to the user's intent")
                else:
                    perceptions.append("This page appears to have low relevance to the user's intent")
            
            # TODO: Add LLM-based perception for more sophisticated analysis
            
            logger.info(f"Generated {len(perceptions)} perceptions")
            return perceptions
            
        except Exception as e:
            logger.error(f"Error in perception module: {e}")
            return ["Error occurred during perception"]
    
    def _analyze_content_relevance(self, content: str, intent: str) -> float:
        """Analyze how relevant the page content is to the user's intent"""
        try:
            intent_words = set(intent.lower().split())
            content_words = set(content.lower().split())
            
            # Simple Jaccard similarity
            intersection = intent_words.intersection(content_words)
            union = intent_words.union(content_words)
            
            if not union:
                return 0.0
            
            return len(intersection) / len(union)
            
        except Exception as e:
            logger.error(f"Error analyzing content relevance: {e}")
            return 0.0
    
    async def _llm_perceive(self, observation: Observation, context: Dict[str, Any]) -> List[str]:
        """Use LLM for sophisticated perception (TODO: implement)"""
        # TODO: Implement LLM-based perception
        # This would use prompts to analyze the observation more deeply
        return [] 