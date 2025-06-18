import random
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


class BaseQueryGenerator(ABC):
    """Base class for query generators"""
    
    @abstractmethod
    async def generate_query(self, context: Dict[str, Any]) -> Optional[str]:
        """Generate a search query based on context"""
        raise NotImplementedError


class IntentBasedQueryGenerator(BaseQueryGenerator):
    """Simple query generator that uses persona intent directly"""
    
    async def generate_query(self, context: Dict[str, Any]) -> Optional[str]:
        """Generate query from persona intent"""
        try:
            persona = context["persona"]
            intent = persona.intent
            
            if not intent:
                return None
            
            # Clean and format the intent as a search query
            query = intent.strip().lower()
            
            # Remove common words that don't help search
            stop_words = ["i want to", "i need to", "looking for", "find", "search for"]
            for stop_word in stop_words:
                query = query.replace(stop_word, "").strip()
            
            logger.info(f"Generated intent-based query: {query}")
            return query
            
        except Exception as e:
            logger.error(f"Error generating intent-based query: {e}")
            return None


class LLMQueryGenerator(BaseQueryGenerator):
    """LLM-based query generator for more sophisticated queries"""
    
    def __init__(self, llm_provider: str = "openai"):
        self.llm_provider = llm_provider
    
    async def generate_query(self, context: Dict[str, Any]) -> Optional[str]:
        """Generate query using LLM"""
        try:
            # TODO: Implement LLM call
            # For now, fall back to intent-based generation
            persona = context["persona"]
            intent = persona.intent
            
            # Enhance query with persona characteristics
            demographic_terms = []
            if persona.age > 0:
                if persona.age < 25:
                    demographic_terms.append("young adult")
                elif persona.age > 55:
                    demographic_terms.append("senior")
            
            if persona.gender:
                demographic_terms.append(persona.gender)
            
            base_query = intent.strip().lower()
            
            # Remove intent prefixes
            for prefix in ["i want to", "i need to", "looking for"]:
                base_query = base_query.replace(prefix, "").strip()
            
            # TODO: Use LLM to generate more sophisticated query
            # For now, return enhanced base query
            logger.info(f"Generated LLM-based query: {base_query}")
            return base_query
            
        except Exception as e:
            logger.error(f"Error generating LLM query: {e}")
            return None


class TrecTopicQueryGenerator(BaseQueryGenerator):
    """Query generator for TREC-style topics"""
    
    def __init__(self, topics_file: Optional[str] = None):
        self.topics_file = topics_file
        self.topics = []
        if topics_file:
            self._load_topics()
    
    def _load_topics(self):
        """Load TREC topics from file"""
        try:
            # TODO: Implement TREC topic loading
            pass
        except Exception as e:
            logger.error(f"Error loading TREC topics: {e}")
    
    async def generate_query(self, context: Dict[str, Any]) -> Optional[str]:
        """Generate query from TREC topic"""
        try:
            if not self.topics:
                # Fall back to intent-based if no topics loaded
                return await IntentBasedQueryGenerator().generate_query(context)
            
            # Select random topic
            topic = random.choice(self.topics)
            query = topic.get("title", "").strip()
            
            logger.info(f"Generated TREC query: {query}")
            return query
            
        except Exception as e:
            logger.error(f"Error generating TREC query: {e}")
            return None


class VariationQueryGenerator(BaseQueryGenerator):
    """Generator that creates query variations"""
    
    def __init__(self, base_generator: BaseQueryGenerator, variations: int = 3):
        self.base_generator = base_generator
        self.variations = variations
        self.current_variation = 0
    
    async def generate_query(self, context: Dict[str, Any]) -> Optional[str]:
        """Generate query variation"""
        try:
            base_query = await self.base_generator.generate_query(context)
            if not base_query:
                return None
            
            # Simple variations
            variations = [
                base_query,
                f"{base_query} reviews",
                f"best {base_query}",
                f"{base_query} buy online",
                f"cheap {base_query}"
            ]
            
            if self.current_variation < len(variations):
                query = variations[self.current_variation]
                self.current_variation += 1
            else:
                query = base_query
            
            logger.info(f"Generated variation query: {query}")
            return query
            
        except Exception as e:
            logger.error(f"Error generating variation query: {e}")
            return None 