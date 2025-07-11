import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union

import numpy as np

logger = logging.getLogger(__name__)

# Global provider setting
provider = "openai"


class LLMException(Exception):
    """Exception for LLM-related errors"""
    pass


def set_provider(provider_name: str):
    """Set the global LLM provider"""
    global provider
    provider = provider_name.lower()
    logger.info(f"LLM provider set to: {provider}")


def async_retry(times=10):
    """Decorator for async retry logic"""
    def func_wrapper(f):
        async def wrapper(*args, **kwargs):
            wait = 1
            max_wait = 5
            last_exception = None
            
            for attempt in range(times):
                try:
                    return await f(*args, **kwargs)
                except Exception as exc:
                    last_exception = exc
                    logger.warning(f"LLM call failed (attempt {attempt + 1}/{times}): {exc}")
                    await asyncio.sleep(wait)
                    wait = min(wait * 2, max_wait)
            
            raise last_exception

        return wrapper
    return func_wrapper


@async_retry()
async def async_chat_openai(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    json_mode: bool = False,
    **kwargs
) -> str:
    """OpenAI chat completion"""
    try:
        import openai
        
        client = openai.AsyncClient()
        
        # Convert model size to actual model name
        model_mapping = {
            "small": "gpt-4o-mini",
            "large": "gpt-4o",
            "gpt-4o-mini": "gpt-4o-mini",
            "gpt-4o": "gpt-4o",
            "gpt-4": "gpt-4"
        }
        actual_model = model_mapping.get(model, model)
        
        # Prepare request arguments
        request_args = {
            "model": actual_model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7)
        }
        
        if json_mode:
            request_args["response_format"] = {"type": "json_object"}
        
        response = await client.chat.completions.create(**request_args)
        content = response.choices[0].message.content
        
        if json_mode:
            # Validate JSON
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response: {content}")
                raise LLMException(f"Invalid JSON response: {e}")
        
        return content
        
    except Exception as e:
        logger.error(f"OpenAI chat error: {e}")
        raise LLMException(f"OpenAI chat failed: {e}")


@async_retry()
async def async_chat_aws(
    messages: List[Dict[str, str]],
    model: str = "claude-3-5-sonnet-20241022",
    json_mode: bool = False,
    **kwargs
) -> str:
    """AWS Bedrock chat completion"""
    try:
        import aioboto3
        
        session = aioboto3.Session()
        
        # Convert model size to actual model name
        model_mapping = {
            "small": "claude-3-haiku-20240307",
            "large": "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
            "claude-3-haiku": "claude-3-haiku-20240307"
        }
        actual_model = model_mapping.get(model, model)
        
        async with session.client("bedrock-runtime", region_name="us-east-1") as client:
            # Extract system message
            system_message = ""
            conversation_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    conversation_messages.append({
                        "role": msg["role"],
                        "content": [{"text": msg["content"]}]
                    })
            
            # Add JSON instruction if needed
            if json_mode and system_message:
                system_message += "\n\nIMPORTANT: You must respond with valid JSON only. Do not include any text outside the JSON object."
            
            request_args = {
                "modelId": actual_model,
                "messages": conversation_messages,
                "inferenceConfig": {
                    "maxTokens": kwargs.get("max_tokens", 1000),
                    "temperature": kwargs.get("temperature", 0.7)
                }
            }
            
            if system_message:
                request_args["system"] = [{"text": system_message}]
            
            response = await client.converse(**request_args)
            content = response["output"]["message"]["content"][0]["text"]
            
            if json_mode:
                # Extract JSON from response
                content = _extract_json_string(content)
                # Validate JSON
                try:
                    json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response: {content}")
                    raise LLMException(f"Invalid JSON response: {e}")
            
            return content
            
    except Exception as e:
        logger.error(f"AWS Bedrock chat error: {e}")
        raise LLMException(f"AWS chat failed: {e}")


def _extract_json_string(text: str) -> str:
    """Extract JSON object from text response"""
    import re
    
    # Try to find JSON object in the text
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    
    if matches:
        return matches[0]
    
    # If no JSON found, try to extract anything between { and }
    start = text.find('{')
    if start != -1:
        # Find matching closing brace
        brace_count = 0
        for i, char in enumerate(text[start:], start):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return text[start:i+1]
    
    raise LLMException("No JSON object found in response")


@async_retry()
async def embed_text_openai(texts: List[str], **kwargs) -> List[List[float]]:
    """OpenAI text embedding"""
    try:
        import openai
        
        client = openai.AsyncClient()
        
        response = await client.embeddings.create(
            input=texts,
            model="text-embedding-3-small"
        )
        
        return [embedding.embedding for embedding in response.data]
        
    except Exception as e:
        logger.error(f"OpenAI embedding error: {e}")
        raise LLMException(f"OpenAI embedding failed: {e}")


@async_retry()
async def embed_text_aws(texts: List[str], **kwargs) -> List[List[float]]:
    """AWS Bedrock text embedding"""
    try:
        import aioboto3
        
        session = aioboto3.Session()
        
        async with session.client("bedrock-runtime", region_name="us-east-1") as client:
            response = await client.invoke_model(
                modelId="cohere.embed-english-v3",
                body=json.dumps({
                    "texts": texts,
                    "input_type": kwargs.get("type", "search_document"),
                    "truncate": "END"
                })
            )
            
            result = json.loads(await response["body"].read())
            return result["embeddings"]
            
    except Exception as e:
        logger.error(f"AWS embedding error: {e}")
        raise LLMException(f"AWS embedding failed: {e}")


# Main API functions
async def async_chat(
    messages: List[Dict[str, str]],
    model: str = "small",
    json_mode: bool = False,
    **kwargs
) -> str:
    """Async chat completion using configured provider"""
    global provider
    
    if provider == "openai":
        return await async_chat_openai(messages, model, json_mode, **kwargs)
    elif provider == "aws":
        return await async_chat_aws(messages, model, json_mode, **kwargs)
    else:
        raise LLMException(f"Unknown provider: {provider}")


async def embed_text(texts: List[str], **kwargs) -> List[List[float]]:
    """Text embedding using configured provider"""
    global provider
    
    if provider == "openai":
        return await embed_text_openai(texts, **kwargs)
    elif provider == "aws":
        return await embed_text_aws(texts, **kwargs)
    else:
        raise LLMException(f"Unknown provider: {provider}")


def chat(
    messages: List[Dict[str, str]],
    model: str = "small",
    json_mode: bool = False,
    **kwargs
) -> str:
    """Synchronous chat completion"""
    return asyncio.run(async_chat(messages, model, json_mode, **kwargs))


# Convenience functions for different model sizes
async def chat_small(messages: List[Dict[str, str]], **kwargs) -> str:
    """Chat with small model"""
    return await async_chat(messages, model="small", **kwargs)


async def chat_large(messages: List[Dict[str, str]], **kwargs) -> str:
    """Chat with large model"""
    return await async_chat(messages, model="large", **kwargs) 