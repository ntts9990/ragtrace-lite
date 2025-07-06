"""
RAGTrace Lite LLM Factory (비동기 버전)

메인 RAGTrace 어댑터 위임 패턴 사용:
- 별도 어댑터 클래스 + LangChain 래퍼
- Pydantic 필드 문제 회피
- RAGAS 완전 호환
"""

import asyncio
import json
import time
import uuid
import aiohttp
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import Generation, LLMResult
from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.prompt_values import StringPromptValue

from .config_loader import Config


class GeminiAdapter:
    """Gemini API 어댑터 (순수 Python 클래스)"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        # API 키 검증 및 정리
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
        
        # 줄바꿈 및 공백 제거
        api_key = api_key.strip()
        
        self.api_key = api_key
        self.model_name = model_name
        
        # Gemini API 설정
        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel(model_name)
        
        print(f"🤖 Gemini 어댑터 초기화: {model_name}")
    
    async def agenerate_answer(self, prompt: str, **kwargs) -> str:
        """Gemini API 비동기 호출"""
        try:
            # 생성 설정
            generation_config = {
                'temperature': kwargs.get('temperature', 0.1),
                'max_output_tokens': kwargs.get('max_tokens', 8192),  # RAGAS를 위해 증가
                'top_p': kwargs.get('top_p', 0.95),
            }
            
            # 안전 설정
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # 비동기 실행
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.gemini_model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
            )
            
            # 응답 처리
            if response.candidates:
                candidate = response.candidates[0]
                # finish_reason 확인 및 텍스트 추출
                if candidate.finish_reason == 1:  # STOP
                    return response.text if response.text else "응답이 생성되었으나 내용이 없습니다."
                elif candidate.finish_reason == 2:  # MAX_TOKENS
                    # 부분 응답이라도 있으면 반환
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text'):
                                text_parts.append(part.text)
                        if text_parts:
                            return ''.join(text_parts) + " [최대 토큰 수 도달]"
                    return "최대 토큰 수에 도달했으나 응답이 없습니다."
                elif candidate.finish_reason == 3:  # SAFETY
                    return "안전 필터에 의해 차단된 응답입니다."
                else:
                    # 기타 경우에도 가능한 텍스트 추출 시도
                    try:
                        return response.text
                    except:
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            text_parts = []
                            for part in candidate.content.parts:
                                if hasattr(part, 'text'):
                                    text_parts.append(part.text)
                            if text_parts:
                                return ''.join(text_parts)
                        return f"응답 추출 실패 (finish_reason: {candidate.finish_reason})"
            else:
                return "응답 후보가 생성되지 않았습니다."
                
        except Exception as e:
            print(f"❌ Gemini API 오류: {e}")
            return f"Gemini API 오류: {str(e)}"
    
    def generate_answer(self, prompt: str, **kwargs) -> str:
        """동기 호출 (비동기를 동기로 래핑)"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 실행 중인 루프가 있으면 executor 사용
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.agenerate_answer(prompt, **kwargs))
                    return future.result()
            else:
                return asyncio.run(self.agenerate_answer(prompt, **kwargs))
        except Exception as e:
            print(f"❌ Gemini 동기 호출 실패: {e}")
            return f"Error: {str(e)}"


class HcxAdapter:
    """HCX API 어댑터 (순수 Python 클래스)"""
    
    # 클래스 변수로 마지막 요청 시간 저장
    _last_request_time = 0
    _min_request_interval = 12.0  # 최소 12초 간격 (HCX API 제한 대응, 여유있게 설정)
    
    def __init__(self, api_key: str, model_name: str = "HCX-005"):
        # API 키 검증 및 정리
        if not api_key:
            raise ValueError("CLOVA_STUDIO_API_KEY가 설정되지 않았습니다.")
        
        # 줄바꿈 및 공백 제거
        api_key = api_key.strip()
        
        if not api_key.startswith("nv-"):
            raise ValueError("CLOVA_STUDIO_API_KEY는 'nv-'로 시작해야 합니다.")
            
        self.api_key = api_key
        self.model_name = model_name
        self.api_url = f"https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/{model_name}"
        
        # 동적 요청 ID 생성
        request_id = str(uuid.uuid4())
        
        self.headers = {
            "Authorization": f"Bearer {api_key}",  # 중요: Bearer 토큰 추가
            "X-NCP-CLOVASTUDIO-API-KEY": api_key,
            "X-NCP-APIGW-API-KEY": api_key,
            "X-NCP-CLOVASTUDIO-REQUEST-ID": request_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        print(f"🤖 HCX 어댑터 초기화: {model_name}")
    
    async def agenerate_answer(self, prompt: str, max_retries: int = 3, **kwargs) -> str:
        """HCX API 비동기 호출 (재시도 로직 포함)"""
        from .hcx_ragas_adapter import HCXRAGASAdapter
        
        # 메트릭 타입 감지 및 프롬프트 강화
        metric_type = HCXRAGASAdapter.detect_metric_type(prompt)
        self._last_metric_type = metric_type  # 나중에 사용하기 위해 저장
        
        # 프롬프트 강화 (JSON 응답 유도)
        enhanced_prompt = HCXRAGASAdapter.enhance_prompt_for_hcx(prompt, metric_type)
        
        for attempt in range(max_retries + 1):
            try:
                # Rate limiting - 요청 간 최소 간격 유지
                current_time = time.time()
                time_since_last = current_time - HcxAdapter._last_request_time
                if time_since_last < HcxAdapter._min_request_interval:
                    wait_time = HcxAdapter._min_request_interval - time_since_last
                    print(f"⏱️  HCX Rate limit 대기: {wait_time:.1f}초")
                    await asyncio.sleep(wait_time)
                
                HcxAdapter._last_request_time = time.time()
                
                payload = {
                    "messages": [
                        {
                            "role": "user",
                            "content": enhanced_prompt
                        }
                    ],
                    "topP": kwargs.get('top_p', 0.8),
                    "topK": kwargs.get('top_k', 0),
                    "maxTokens": kwargs.get('max_tokens', 1000),
                    "temperature": kwargs.get('temperature', 0.5),
                    "repetitionPenalty": kwargs.get('repetition_penalty', 1.1),
                    "stop": [],
                    "includeAiFilters": True,
                    "seed": 0
                }
                
                # 각 요청마다 새로운 요청 ID 생성
                headers = self.headers.copy()
                headers["X-NCP-CLOVASTUDIO-REQUEST-ID"] = str(uuid.uuid4())
                
                # aiohttp 비동기 요청
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.api_url,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            
                            if 'result' in result and 'message' in result['result']:
                                content = result['result']['message']['content']
                                if content:
                                    # RAGAS 호환성을 위한 응답 후처리
                                    cleaned_content = self._clean_response_for_ragas(content)
                                    
                                    # JSON 응답이 아니면 메트릭에 맞게 변환
                                    if hasattr(self, '_last_metric_type') and self._last_metric_type:
                                        if not cleaned_content.strip().startswith('{'):
                                            from .hcx_ragas_adapter import HCXRAGASAdapter
                                            parsed = HCXRAGASAdapter.parse_hcx_response(cleaned_content, self._last_metric_type)
                                            return json.dumps(parsed, ensure_ascii=False)
                                    
                                    return cleaned_content
                                else:
                                    return "HCX API에서 빈 응답을 받았습니다."
                            else:
                                return f"HCX API 응답 형식 오류: {result}"
                                
                        elif response.status == 429:  # Rate limit 오류
                            error_text = await response.text()
                            if attempt < max_retries:
                                wait_time = (attempt + 1) * 10  # 지수적 백오프: 10초, 20초, 30초
                                print(f"❌ HCX Rate limit (시도 {attempt + 1}/{max_retries + 1}): {wait_time}초 후 재시도")
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                print(f"❌ HCX Rate limit 최대 재시도 초과: {error_text}")
                                return f"HCX API Rate limit 초과: {error_text}"
                        else:
                            error_text = await response.text()
                            print(f"❌ HCX API 오류 {response.status}: {error_text}")
                            return f"HCX API 오류 ({response.status}): {error_text}"
                            
            except asyncio.TimeoutError:
                if attempt < max_retries:
                    print(f"❌ HCX API 타임아웃 (시도 {attempt + 1}/{max_retries + 1}): 재시도")
                    await asyncio.sleep(5)
                    continue
                else:
                    print("❌ HCX API 타임아웃 최대 재시도 초과")
                    return "HCX API 요청 타임아웃"
            except Exception as e:
                if attempt < max_retries:
                    print(f"❌ HCX API 오류 (시도 {attempt + 1}/{max_retries + 1}): {e}")
                    await asyncio.sleep(5)
                    continue
                else:
                    print(f"❌ HCX API 최대 재시도 초과: {e}")
                    return f"HCX API 오류: {str(e)}"
        
        return "HCX API 최대 재시도 초과"
    
    def _clean_response_for_ragas(self, content: str) -> str:
        """RAGAS 호환성을 위한 응답 후처리"""
        import re
        import json
        from .hcx_ragas_adapter import HCXRAGASAdapter
        
        # 프롬프트에서 메트릭 타입 감지 (저장된 값 사용)
        metric_type = getattr(self, '_last_metric_type', None)
        
        # HCX RAGAS 어댑터로 파싱
        try:
            parsed = HCXRAGASAdapter.parse_hcx_response(content, metric_type)
            return json.dumps(parsed, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ HCX 응답 파싱 실패, 원본 반환: {e}")
            
        # 폴백: 기존 로직
        if content.strip().startswith('{') and content.strip().endswith('}'):
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    # text를 statements로 변환 (faithfulness용)
                    if 'text' in data and metric_type == "faithfulness":
                        text = data['text']
                        statements = [s.strip() for s in re.split(r'[.。\n]+', text) if s.strip()]
                        return json.dumps({"statements": statements}, ensure_ascii=False)
                    return json.dumps(data, ensure_ascii=False)
            except json.JSONDecodeError:
                pass
        
        # 일반 텍스트 응답 정리
        cleaned = content.strip()
        
        # 마크다운 포맷팅 제거
        cleaned = re.sub(r'```.*?```', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
        cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)
        
        # 불필요한 공백 정리
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def generate_answer(self, prompt: str, **kwargs) -> str:
        """동기 호출 (비동기를 동기로 래핑)"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 실행 중인 루프가 있으면 executor 사용
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.agenerate_answer(prompt, **kwargs))
                    return future.result()
            else:
                return asyncio.run(self.agenerate_answer(prompt, **kwargs))
        except Exception as e:
            print(f"❌ HCX 동기 호출 실패: {e}")
            return f"Error: {str(e)}"


class LLMAdapterWrapper(LLM):
    """LLM 어댑터 래퍼 - 메인 RAGTrace HcxLangChainCompat 구조 참조"""
    
    adapter: Any = None
    model: str = None
    
    def __init__(self, adapter, **kwargs):
        super().__init__(**kwargs)
        self.adapter = adapter
        self.model = adapter.model_name
    
    @property
    def _llm_type(self) -> str:
        return "ragtrace_lite_adapter"
    
    def set_run_config(self, run_config):
        """RAGAS RunConfig 설정 - 무시"""
        # 자체 설정을 사용하므로 RunConfig는 무시
        pass
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None,
              run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs: Any) -> str:
        """동기 호출"""
        return self.adapter.generate_answer(prompt, **kwargs)
    
    async def _acall(self, prompt: str, stop: Optional[List[str]] = None,
                     run_manager: Optional[AsyncCallbackManagerForLLMRun] = None, **kwargs: Any) -> str:
        """비동기 호출"""
        return await self.adapter.agenerate_answer(prompt, **kwargs)
    
    async def agenerate(self, prompts: List[str | StringPromptValue], **kwargs: Any):
        """RAGAS가 원하는 비동기 generate 메서드"""
        results = []
        for prompt in prompts:
            prompt_str = prompt.text if hasattr(prompt, 'text') else str(prompt)
            result = await self.adapter.agenerate_answer(prompt_str, **kwargs)
            results.append(LLMResult(generations=[[Generation(text=result)]]))
        return LLMResult(generations=[gen.generations[0] for gen in results])
    
    def generate(self, prompts: List[str | StringPromptValue], **kwargs: Any):
        """RAGAS 호환 generate - 비동기 컨텍스트 감지"""
        # RAGAS 버그 우회: RAGAS가 await llm.generate()를 호출하므로
        # 비동기 컨텍스트에서는 코루틴을 반환해야 함
        try:
            # 비동기 컨텍스트 확인
            loop = asyncio.get_running_loop()
            # 비동기 컨텍스트에서 실행 중이면 agenerate 반환
            return self.agenerate(prompts, **kwargs)
        except RuntimeError:
            # 동기 컨텍스트에서는 일반 LLMResult 반환
            if not isinstance(prompts, list):
                prompts = [prompts]
            
            generations = []
            for prompt in prompts:
                # 프롬프트를 문자열로 변환
                if hasattr(prompt, 'to_string'):
                    prompt_str = prompt.to_string()
                else:
                    prompt_str = str(prompt)
                
                # 어댑터 호출
                response = self._call(prompt_str, **kwargs)
                
                # Generation 객체 생성
                generation = Generation(text=response)
                generations.append([generation])
            
            return LLMResult(generations=generations)
    
    def agenerate(self, prompts: List[str | StringPromptValue], **kwargs: Any):
        """비동기 generate - RAGAS 호환 (코루틴 반환)"""
        async def _agenerate():
            if not isinstance(prompts, list):
                prompts_list = [prompts]
            else:
                prompts_list = prompts
            
            generations = []
            
            # 모든 프롬프트를 동시에 처리
            tasks = []
            for prompt in prompts_list:
                if hasattr(prompt, 'to_string'):
                    prompt_str = prompt.to_string()
                else:
                    prompt_str = str(prompt)
                tasks.append(self._acall(prompt_str, **kwargs))
            
            responses = await asyncio.gather(*tasks)
            
            for response in responses:
                generation = Generation(text=response)
                generations.append([generation])
            
            return LLMResult(generations=generations)
        
        # 코루틴 객체 반환 (await 가능)
        return _agenerate()


def create_llm(config: Config) -> LLM:
    """RAGAS 호환 LLM 인스턴스 생성"""
    provider = config.llm.provider.lower()
    
    try:
        if provider == 'gemini':
            if not config.llm.api_key:
                raise ValueError("Gemini API 키가 설정되지 않았습니다")
            
            model_name = config.llm.model_name or "gemini-2.5-flash"
            adapter = GeminiAdapter(
                api_key=config.llm.api_key,
                model_name=model_name
            )
            return LLMAdapterWrapper(adapter)
            
        elif provider == 'hcx':
            if not config.llm.api_key:
                raise ValueError("HCX API 키가 설정되지 않았습니다")
            
            model_name = config.llm.model_name or "HCX-005"
            adapter = HcxAdapter(
                api_key=config.llm.api_key,
                model_name=model_name
            )
            
            # HCX는 프록시로 감싸서 반환
            from .hcx_proxy import HCXRAGASProxy
            base_llm = LLMAdapterWrapper(adapter)
            return HCXRAGASProxy(base_llm)
            
        else:
            raise ValueError(f"지원하지 않는 LLM 제공자: {provider}")
            
    except Exception as e:
        raise Exception(f"LLM 초기화 실패 ({provider}): {str(e)}")


async def test_llm_connection_async(llm: LLM, provider: str) -> bool:
    """LLM 비동기 연결 테스트"""
    test_prompt = "Hello, this is a test. Please respond with 'OK'."
    
    try:
        print(f"🔄 {provider.upper()} LLM 비동기 연결 테스트 중...")
        response = await llm._acall(test_prompt)
        print(f"✅ {provider.upper()} LLM 연결 성공")
        print(f"테스트 응답: {response[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ {provider.upper()} LLM 연결 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def check_llm_connection(llm: LLM, provider: str) -> bool:
    """LLM 연결 테스트 (동기 래퍼)"""
    try:
        return asyncio.run(test_llm_connection_async(llm, provider))
    except Exception as e:
        print(f"❌ {provider.upper()} LLM 연결 테스트 실패: {str(e)}")
        return False


if __name__ == "__main__":
    # 테스트 코드
    import asyncio
    from .config_loader import load_config
    
    async def test_main():
        try:
            config = load_config()
            print(f"설정 로드 완료: {config.llm.provider}")
            
            llm = create_llm(config)
            print("LLM 인스턴스 생성 완료")
            
            success = await test_llm_connection_async(llm, config.llm.provider)
            
            if success:
                print("✅ LLM Factory 비동기 테스트 성공")
            else:
                print("❌ LLM Factory 비동기 테스트 실패")
                
        except Exception as e:
            print(f"❌ LLM Factory 테스트 오류: {e}")
    
    asyncio.run(test_main())