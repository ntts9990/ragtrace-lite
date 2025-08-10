"""HCX LLM Provider"""

import httpx
import json
import logging
from typing import List, Optional, Dict, Any

from .base import LLMProvider

logger = logging.getLogger(__name__)

class HCXProvider(LLMProvider):
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
            response = self.client.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            content = result.get("result", {}).get("message", {}).get("content", "")
            return content
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for HCX API: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for HCX API: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from HCX API")
            raise ValueError("Invalid JSON response from HCX API")

    async def generate_async(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        headers = self._get_headers()
        data = self._get_payload(prompt, stop)

        try:
            response = await self.async_client.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            content = result.get("result", {}).get("message", {}).get("content", "")
            return content
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for HCX API: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for HCX API: {e}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from HCX API: {response.text}")
            raise ValueError("Invalid JSON response from HCX API")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _get_payload(self, prompt: str, stop: Optional[List[str]]) -> Dict[str, Any]:
        return {
            "messages": [
                {"role": "system", "content": [{"type": "text", "text": "You are a helpful assistant for RAG evaluation."}]},
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ],
            "temperature": self.temperature,
            "maxTokens": self.max_tokens,
            "topP": 0.8,
            "topK": 0,
            "repetitionPenalty": 1.1,
            "stop": stop or []
        }

    def __del__(self):
        if hasattr(self, 'client') and self.client:
            self.client.close()
    
    async def aclose(self):
        """Properly close async client"""
        if hasattr(self, 'async_client') and self.async_client:
            await self.async_client.aclose()
