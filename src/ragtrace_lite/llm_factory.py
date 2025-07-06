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
    _min_request_interval = 2.0  # 최소 2초 간격 (HCX API 제한 대응)
    
    def __init__(self, api_key: str, model_name: str = "HCX-005"):
        # API 키 검증
        if not api_key:
            raise ValueError("CLOVA_STUDIO_API_KEY가 설정되지 않았습니다.")
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
    
    async def agenerate_answer(self, prompt: str, **kwargs) -> str:
        """HCX API 비동기 호출"""
        try:
            # Rate limiting - 요청 간 최소 간격 유지
            current_time = time.time()
            time_since_last = current_time - HcxAdapter._last_request_time
            if time_since_last < HcxAdapter._min_request_interval:
                wait_time = HcxAdapter._min_request_interval - time_since_last
                await asyncio.sleep(wait_time)
            
            HcxAdapter._last_request_time = time.time()
            
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
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
                            return content if content else "HCX API에서 빈 응답을 받았습니다."
                        else:
                            return f"HCX API 응답 형식 오류: {result}"
                    else:
                        error_text = await response.text()
                        print(f"❌ HCX API 오류 {response.status}: {error_text}")
                        return f"HCX API 오류 ({response.status}): {error_text}"
                        
        except asyncio.TimeoutError:
            print("❌ HCX API 타임아웃")
            return "HCX API 요청 타임아웃"
        except Exception as e:
            print(f"❌ HCX API 오류: {e}")
            return f"HCX API 오류: {str(e)}"
    
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
            return LLMAdapterWrapper(adapter)
            
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


def test_llm_connection(llm: LLM, provider: str) -> bool:
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