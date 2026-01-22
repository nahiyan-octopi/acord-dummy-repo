"""
Groq API Service for Llama models
"""
import json
from typing import Optional, Dict, Any
from groq import Groq
from backend.config import Config


class GroqService:
    """Service for interacting with Groq API (Llama models)"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Groq service
        
        Args:
            api_key: Groq API key (defaults to environment variable)
        """
        self.api_key = api_key or Config.GROQ_API_KEY
        self.model = Config.GROQ_MODEL
        self.temperature = Config.GROQ_TEMPERATURE
        self.max_tokens = Config.GROQ_MAX_TOKENS
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not configured")
        
        self.client = Groq(api_key=self.api_key)
    
    def chat_completion(
        self,
        messages: list,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate a chat completion using Groq API
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens
            response_format: Optional response format (e.g., {"type": "json_object"})
            
        Returns:
            Response content and metadata
        """
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
            }
            
            if response_format:
                kwargs["response_format"] = response_format
            
            response = self.client.chat.completions.create(**kwargs)
            
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Groq API
        
        Returns:
            Dictionary with success status and details
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Say 'Connection successful'"}
                ],
                max_tokens=50,
                temperature=0
            )
            
            return {
                "success": True,
                "message": "Connected to Groq API",
                "model": self.model
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to connect: {str(e)}"
            }


# Singleton instance
_groq_service = None


def get_groq_service() -> GroqService:
    """Get or create Groq service singleton"""
    global _groq_service
    if _groq_service is None:
        _groq_service = GroqService()
    return _groq_service
