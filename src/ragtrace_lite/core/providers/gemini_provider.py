"""Gemini LLM Provider"""

import httpx
import json
import logging
from typing import List, Optional, Dict, Any

from .base import LLMProvider

logger = logging.getLogger(__name__)

class GeminiProvider(LLMProvider):
    def __init__(
        self,
        api_url: str,
        api_key: str,
        model_name: str,
        temperature: float,
        max_tokens: int,
        timeout: int = 30
    ):
        super().__init__(api_url, api_key, model_name, temperature, max_tokens, timeout)
        self.client = httpx.Client(timeout=self.timeout)
        self.async_client = httpx.AsyncClient(timeout=self.timeout)

    def generate(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Generate text synchronously"""
        headers = self._get_headers()
        data = self._get_payload(prompt, stop)
        
        try:
            response = self.client.post(f"{self.api_url}?key={self.api_key}", headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            candidates = result.get("candidates", [])
            if candidates and len(candidates) > 0:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts and len(parts) > 0:
                    return parts[0].get("text", "")
            return ""
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for Gemini API: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for Gemini API: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Gemini API")
            raise ValueError("Invalid JSON response from Gemini API")

    async def generate_async(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Generate text asynchronously"""
        headers = self._get_headers()
        data = self._get_payload(prompt, stop)

        try:
            response = await self.async_client.post(f"{self.api_url}?key={self.api_key}", headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            candidates = result.get("candidates", [])
            if candidates and len(candidates) > 0:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts and len(parts) > 0:
                    return parts[0].get("text", "")
            return ""
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for Gemini API: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for Gemini API: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Gemini API")
            raise ValueError("Invalid JSON response from Gemini API")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json"
        }

    def _get_payload(self, prompt: str, stop: Optional[List[str]]) -> Dict[str, Any]:
        return {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
                "stopSequences": stop or []
            }
        }

    def __del__(self):
        if hasattr(self, 'client') and self.client:
            self.client.close()
    
    async def aclose(self):
        """Properly close async client"""
        if hasattr(self, 'async_client') and self.async_client:
            await self.async_client.aclose()
