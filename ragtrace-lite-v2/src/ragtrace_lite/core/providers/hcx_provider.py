"""HCX LLM Provider"""

import httpx
import json
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

class HCXProvider:
    def __init__(
        self,
        api_url: str,
        api_key: str,
        model_name: str,
        temperature: float,
        max_tokens: int,
        timeout: int = 30
    ):
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.client = httpx.Client(timeout=self.timeout)

    def generate(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
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
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from HCX API: {response.text}")
            raise ValueError("Invalid JSON response from HCX API")

    def __del__(self):
        self.client.close()
