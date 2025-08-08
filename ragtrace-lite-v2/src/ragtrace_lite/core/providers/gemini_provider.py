"""Gemini LLM Provider"""

import httpx
import json
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

class GeminiProvider:
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
            "Content-Type": "application/json"
        }
        data = {
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

        try:
            response = self.client.post(f"{self.api_url}?key={self.api_key}", headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            content = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return content
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for Gemini API: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for Gemini API: {e}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from Gemini API: {response.text}")
            raise ValueError("Invalid JSON response from Gemini API")

    def __del__(self):
        self.client.close()
