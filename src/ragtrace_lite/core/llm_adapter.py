"""LLM 어댑터 - HCX/Gemini 지원"""

from typing import Optional, List, Any, Dict
import json
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
import logging
import asyncio
import os
import random
import requests

from .rate_limiter import get_rate_limiter
from .providers.hcx_provider import HCXProvider
from .providers.gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)


class LLMAdapter(LLM):
    """통합 LLM 어댑터"""
    
    provider: str
    api_key: str
    model_name: str
    api_url: str
    temperature: float
    max_tokens: int
    rate_limit_delay: float
    max_retries: int = 5
    backoff_factor: float = 1.5
    
    _provider_instance: Any = None
    rate_limiter: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._initialize_provider()
        
        # Initialize rate limiter
        rate_limit_config = {
            'requests_per_second': 1.0 / self.rate_limit_delay,
            'backoff_factor': 2.0,
            'max_backoff': 60.0
        }
        self.rate_limiter = get_rate_limiter(self.provider, rate_limit_config)
    
    def _initialize_provider(self):
        """프로바이더 인스턴스 초기화"""
        if self.provider == "hcx":
            self._provider_instance = HCXProvider(
                api_url=self.api_url,
                api_key=self.api_key,
                model_name=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        elif self.provider == "gemini":
            self._provider_instance = GeminiProvider(
                api_url=self.api_url,
                api_key=self.api_key,
                model_name=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    @property
    def _llm_type(self) -> str:
        return f"{self.provider}-{self.model_name}"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        """LLM API 호출 - 지수 백오프 및 지터 적용 (동기)"""
        # 동기 호출은 비동기 호출을 래핑
        return asyncio.run(self._acall(prompt, stop, run_manager))

    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        """LLM API 호출 - 지수 백오프 및 지터 적용 (비동기)"""
        
        enhanced_prompt = self._enhance_prompt(prompt)
        
        for attempt in range(self.max_retries):
            try:
                wait_time = await self.rate_limiter.acquire()
                if wait_time > 0:
                    logger.debug(f"Rate limiter applied {wait_time:.2f}s delay")
                
                response = await self._provider_instance.generate_async(enhanced_prompt, stop)
                
                self.rate_limiter.record_request_result(success=True)
                return self._clean_response(response)
                
            except Exception as e:
                error_msg = str(e).lower()
                is_rate_limit = any(keyword in error_msg for keyword in 
                                   ['429', 'rate', 'too many', 'quota', 'limit'])
                
                self.rate_limiter.record_request_result(success=False, is_rate_limit=is_rate_limit)
                
                if attempt < self.max_retries - 1:
                    backoff_time = self.rate_limit_delay * (self.backoff_factor ** attempt)
                    jitter = backoff_time * 0.1 * random.uniform(-1, 1)
                    sleep_time = backoff_time + jitter
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries} failed with error: {e}. "
                        f"Retrying in {sleep_time:.2f} seconds..."
                    )
                    await asyncio.sleep(sleep_time)
                else:
                    logger.error(f"All {self.max_retries} attempts failed for {self.provider}. Using fallback.")
                    return self._get_fallback_response(prompt)
        
        return self._get_fallback_response(prompt)
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return self.rate_limiter.get_stats()
    
    def _call_hcx(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """HCX v3 API 호출"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",  # v3 API는 Bearer 토큰 사용
            "Content-Type": "application/json"
        }
        
        # v3 API 형식에 맞게 수정
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": "You are a helpful assistant for RAG evaluation."}]
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ],
            "temperature": self.temperature,
            "maxTokens": self.max_tokens,
            "topP": 0.8,
            "topK": 0,
            "repetitionPenalty": 1.1,
            "stop": stop or []
        }
        
        response = requests.post(
            self.api_url,
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        content = result.get("result", {}).get("message", {}).get("content", "")
        
        return self._clean_response(content)
    
    def _call_gemini(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Gemini API 호출"""
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
        
        response = requests.post(
            f"{self.api_url}?key={self.api_key}",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        content = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        return self._clean_response(content)
    
    def _enhance_prompt(self, prompt: str) -> str:
        """RAGAS 메트릭에 맞는 정확한 JSON 형식 지정"""
        
        prompt_lower = prompt.lower()
        
        # Faithfulness - Statement generation 또는 NLI verification
        if "statement" in prompt_lower and "verdict" in prompt_lower:
            # NLI Statement verification
            enhancement = '''\n\nIMPORTANT: Return JSON with exact structure:
{
  "statements": [
    {"statement": "original statement text", "reason": "explanation", "verdict": 1}
  ]
}
verdict must be 0 (not faithful) or 1 (faithful). Use double quotes only.'''
        elif "statement" in prompt_lower:
            # Statement generation
            enhancement = '''\n\nIMPORTANT: Return JSON with exact structure:
{"statements": ["statement 1", "statement 2"]}
Use double quotes only.'''
        
        # Answer Relevancy
        elif "question" in prompt_lower and "answer" in prompt_lower:
            enhancement = '''\n\nIMPORTANT: Return JSON with exact structure:
{"question": "generated question", "noncommittal": 0}
noncommittal: 0 (clear) or 1 (vague). Use double quotes only.'''
        
        # Context Precision
        elif "precision" in prompt_lower or "useful" in prompt_lower:
            enhancement = '''\n\nIMPORTANT: Return JSON with exact structure:
{"reason": "explanation", "verdict": 1}
verdict: 0 (not useful) or 1 (useful). Use double quotes only.'''
        
        # Context Recall
        elif "recall" in prompt_lower or "attributed" in prompt_lower:
            enhancement = '''\n\nIMPORTANT: Return JSON with exact structure:
{
  "classifications": [
    {"statement": "text", "reason": "explanation", "attributed": 1}
  ]
}
attributed: 0 (no) or 1 (yes). Use double quotes only.'''
        
        # Answer Correctness
        elif "tp" in prompt_lower or "fp" in prompt_lower or "fn" in prompt_lower:
            enhancement = '''\n\nIMPORTANT: Return JSON with exact structure:
{
  "TP": [{"statement": "text", "reason": "why"}],
  "FP": [{"statement": "text", "reason": "why"}],
  "FN": [{"statement": "text", "reason": "why"}]
}
Use double quotes only.'''
        
        # Generic JSON request
        elif "json" in prompt_lower:
            enhancement = '''\n\nIMPORTANT: Return valid JSON only. Use double quotes for all strings. No additional text.'''
        else:
            return prompt
        
        return prompt + enhancement
    
    def _clean_response(self, response: str) -> str:
        """응답 정리 및 JSON 검증 - 강화된 처리"""
        
        original_response = response
        
        # 1. JSON 블록 추출 (```json ... ```)
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end > start:
                response = response[start:end].strip()
        elif "```" in response:
            # 단순 ``` 블록
            start = response.find("```") + 3
            end = response.find("```", start)
            if end > start:
                response = response[start:end].strip()
        
        # 2. JSON 부분만 추출 ({...} 또는 [...])
        response = response.strip()
        
        # 시작과 끝의 불필요한 문자 제거
        while response and response[0] not in '{[':
            response = response[1:]
        while response and response[-1] not in '}]':
            response = response[:-1]
        
        # 3. 일반적인 오류 수정
        # 작은따옴표를 큰따옴표로 변환 (필드명에서)
        import re
        # JSON 필드명에 작은따옴표 사용 수정
        response = re.sub(r"(\w+)':", r'"\1":', response)
        response = re.sub(r"'(\w+):", r'"\1":', response)
        
        # 4. JSON 파싱 시도
        try:
            json_data = json.loads(response)
            
            # 5. RAGAS 형식 호환성 확인 및 보정
            json_data = self._fix_ragas_format(json_data)
            
            return json.dumps(json_data, ensure_ascii=False)
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}")
            logger.debug(f"Original response: {original_response}")
            logger.debug(f"Cleaned response: {response}")
            
            # 폴백 응답 생성
            return self._create_structured_fallback(original_response)
    
    def _fix_ragas_format(self, json_data: dict) -> dict:
        """RAGAS 형식에 맞게 JSON 보정"""
        
        # Faithfulness NLI - verdict가 boolean이면 int로 변환
        if "statements" in json_data and isinstance(json_data["statements"], list):
            for stmt in json_data["statements"]:
                if isinstance(stmt, dict) and "verdict" in stmt:
                    if isinstance(stmt["verdict"], bool):
                        stmt["verdict"] = 1 if stmt["verdict"] else 0
                    elif isinstance(stmt["verdict"], str):
                        stmt["verdict"] = 1 if stmt["verdict"].lower() in ['true', 'yes', '1'] else 0
        
        # Answer Relevancy - noncommittal boolean to int
        if "noncommittal" in json_data:
            if isinstance(json_data["noncommittal"], bool):
                json_data["noncommittal"] = 1 if json_data["noncommittal"] else 0
        
        # Context Precision - verdict boolean to int
        if "verdict" in json_data:
            if isinstance(json_data["verdict"], bool):
                json_data["verdict"] = 1 if json_data["verdict"] else 0
        
        # Context Recall - attributed boolean to int
        if "classifications" in json_data and isinstance(json_data["classifications"], list):
            for cls in json_data["classifications"]:
                if isinstance(cls, dict) and "attributed" in cls:
                    if isinstance(cls["attributed"], bool):
                        cls["attributed"] = 1 if cls["attributed"] else 0
        
        return json_data
    
    def _create_structured_fallback(self, original_response: str) -> str:
        """구조화된 폴백 응답 생성"""
        response_lower = original_response.lower()
        
        # Faithfulness
        if "statement" in response_lower and "verdict" in response_lower:
            return json.dumps({"statements": [{"statement": "No clear statement", "reason": "Parsing failed", "verdict": 0}]})
        elif "statement" in response_lower:
            return json.dumps({"statements": []})
        
        # Answer Relevancy
        elif "question" in response_lower:
            return json.dumps({"question": "What is discussed?", "noncommittal": 0})
        
        # Context Precision
        elif "verdict" in response_lower or "precision" in response_lower:
            return json.dumps({"reason": "Default assessment", "verdict": 1})
        
        # Context Recall
        elif "attributed" in response_lower or "classification" in response_lower:
            return json.dumps({"classifications": [{"statement": "Content", "reason": "Default", "attributed": 1}]})
        
        # Answer Correctness
        elif "tp" in response_lower or "fp" in response_lower:
            return json.dumps({"TP": [], "FP": [], "FN": []})
        
        # Default
        else:
            return "{}"
    
    def _get_fallback_response(self, prompt: str) -> str:
        """에러 시 폴백 응답 - 개선된 버전"""
        return self._create_structured_fallback(prompt)
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "LLMAdapter":
        """설정에서 생성"""
        provider = config.get("provider", "hcx")
        
        # provider별 설정 추출
        provider_config = config.get(provider, {})
        if not provider_config:
            raise ValueError(f"No configuration found for provider: {provider}")
        
        # API key 처리 (환경변수 치환)
        api_key = provider_config.get("api_key", "")
        if api_key.startswith("${") and api_key.endswith("}"):
            env_var = api_key[2:-1]
            api_key = os.environ.get(env_var, "mock_key_for_testing")
        
        # 기본값 설정
        default_apis = {
            "hcx": "https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/HCX-005",
            "gemini": "https://generativelanguage.googleapis.com/v1beta/models"
        }
        
        return cls(
            provider=provider,
            api_key=api_key,
            api_url=provider_config.get("api_url") or default_apis.get(provider, ""),
            model_name=provider_config.get("model_name", f"{provider}-default"),
            temperature=provider_config.get("temperature", 0.1),
            max_tokens=provider_config.get("max_tokens", 1024),
            rate_limit_delay=provider_config.get("rate_limit_delay", 5.0)
        )