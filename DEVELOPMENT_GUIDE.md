# RAGTrace Lite 개발자 가이드

## 목차
1. [예상되는 에러 패턴 및 해결방안](#1-예상되는-에러-패턴-및-해결방안)
2. [폐쇄망 환경 구성 가이드](#2-폐쇄망-환경-구성-가이드)
3. [LLM 모델 교체 가이드](#3-llm-모델-교체-가이드)
4. [임베딩 모델 교체 가이드](#4-임베딩-모델-교체-가이드)
5. [문제 해결 팁](#5-문제-해결-팁)

---

## 1. 예상되는 에러 패턴 및 해결방안

### 1.1 DataFrame Ambiguous Truth Value 에러

#### 문제 상황
Windows 환경에서 pandas DataFrame의 boolean 평가 시 발생하는 에러입니다.

```python
# 문제가 되는 코드 (main.py:154)
if results_df is None or results_df.empty:
    # ValueError: The truth value of a DataFrame is ambiguous
```

#### 해결 방법
```python
# 방법 1: len() 사용 (권장)
if results_df is None or len(results_df) == 0:
    # 안전한 처리

# 방법 2: shape 속성 사용
if results_df is None or results_df.shape[0] == 0:
    # 안전한 처리

# 방법 3: isinstance 체크 추가
if results_df is None or (isinstance(results_df, pd.DataFrame) and results_df.empty):
    # 더 안전한 처리
```

### 1.2 타입 변환 에러 (None/NaN 처리)

#### 문제 상황
숫자형 데이터에 None이나 문자가 섞여 있을 때 발생합니다.

```python
# 문제가 되는 코드
score = stats.get('average')  # None일 수 있음
formatted_score = f"{score:.4f}"  # TypeError 발생
```

#### 해결 방법
```python
# 방법 1: 기본값과 함께 사용
score = float(stats.get('average', 0) or 0)  # None이면 0으로 변환
formatted_score = f"{score:.4f}"

# 방법 2: 명시적 타입 체크
score = stats.get('average')
if score is not None and not pd.isna(score):
    try:
        numeric_score = float(score)
        formatted_score = f"{numeric_score:.4f}"
    except (ValueError, TypeError):
        formatted_score = "N/A"
else:
    formatted_score = "N/A"

# 방법 3: pandas의 안전한 변환 사용
numeric_data = pd.to_numeric(data_series, errors='coerce')  # 변환 실패 시 NaN
numeric_data = numeric_data.fillna(0)  # NaN을 0으로 채우기
```

### 1.3 경로 처리 문제 (크로스 플랫폼)

#### 문제 상황
Windows와 Unix 시스템 간 경로 구분자 차이로 인한 문제입니다.

```python
# 문제가 되는 코드
file_path = "data/input/test.json"  # Windows에서 문제 가능
```

#### 해결 방법
```python
from pathlib import Path

# 방법 1: pathlib 사용 (권장)
file_path = Path("data") / "input" / "test.json"
# 자동으로 OS에 맞는 경로 구분자 사용

# 방법 2: 절대 경로 변환
absolute_path = file_path.absolute()
# Windows: C:\Users\...\data\input\test.json
# Unix: /home/.../data/input/test.json

# 방법 3: 문자열 변환 (외부 라이브러리용)
path_str = str(file_path)  # 일부 라이브러리는 문자열만 받음

# 방법 4: 플랫폼 체크
import platform
if platform.system() == "Windows":
    # Windows 특별 처리
    pass
```

### 1.4 API Rate Limiting 처리

#### 문제 상황
API 호출 제한으로 인한 429 에러 또는 연결 거부입니다.

#### 해결 방법
```python
import time
import asyncio
from typing import Optional

class RateLimiter:
    def __init__(self, min_interval: float = 1.0):
        self.min_interval = min_interval
        self.last_request_time = 0
    
    async def wait_if_needed(self):
        """필요시 대기"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            print(f"⏱️  Rate limit 대기: {wait_time:.1f}초")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()

# 사용 예시
rate_limiter = RateLimiter(min_interval=12.0)  # HCX는 12초

async def call_api():
    await rate_limiter.wait_if_needed()
    # API 호출 수행
```

---

## 2. 폐쇄망 환경 구성 가이드

### 2.1 환경 변수 설정

폐쇄망에서는 외부 네트워크 접근을 차단해야 합니다.

```bash
# Hugging Face 오프라인 모드 설정
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

# 프록시 설정 (필요한 경우)
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port
export NO_PROXY=localhost,127.0.0.1
```

### 2.2 모델 파일 사전 준비

#### BGE-M3 모델 다운로드 (인터넷 가능한 환경에서)
```python
from huggingface_hub import snapshot_download

# 모델 다운로드
model_path = "./models/bge-m3"
snapshot_download(
    repo_id="BAAI/bge-m3",
    local_dir=model_path,
    local_dir_use_symlinks=False,  # 중요: 심볼릭 링크 비활성화
    resume_download=True
)

# 다운로드된 파일 확인
import os
for root, dirs, files in os.walk(model_path):
    for file in files:
        print(os.path.join(root, file))
```

#### 모델 파일 구조
```
models/
└── bge-m3/
    ├── config.json
    ├── model.safetensors
    ├── tokenizer_config.json
    ├── tokenizer.json
    └── special_tokens_map.json
```

### 2.3 의존성 패키지 준비

```bash
# 1. 인터넷 가능한 환경에서 패키지 다운로드
pip download -r requirements.txt -d ./offline_packages/

# 2. 폐쇄망으로 offline_packages 폴더 이동

# 3. 폐쇄망에서 설치
pip install --no-index --find-links ./offline_packages/ -r requirements.txt
```

---

## 3. LLM 모델 교체 가이드

### 3.1 새로운 LLM Provider 추가하기

#### Step 1: Config 설정 추가 (config_loader.py)

```python
# config_loader.py 수정
class LLMConfig(BaseModel):
    """LLM 설정"""
    provider: str = Field(..., description="LLM 제공자")
    api_key: Optional[str] = Field(None, description="API 키")
    model_name: Optional[str] = Field(None, description="모델 이름")
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v):
        # 새로운 provider 추가
        allowed = ['gemini', 'hcx', 'ollama', 'custom_llm']  # 새 provider 추가
        if v.lower() not in allowed:
            raise ValueError(f"지원하지 않는 LLM 제공자: {v}. 허용: {allowed}")
        return v.lower()
```

#### Step 2: LLM Adapter 클래스 구현

```python
# 새 파일: custom_llm_adapter.py
class CustomLLMAdapter:
    """커스텀 LLM API 어댑터"""
    
    def __init__(self, api_key: str, model_name: str, base_url: str = None):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url or "http://localhost:8080"
        
        # 헤더 설정
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"🤖 Custom LLM 어댑터 초기화: {model_name}")
    
    async def agenerate_answer(self, prompt: str, **kwargs) -> str:
        """비동기 API 호출"""
        import aiohttp
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', 1000),
            # 추가 파라미터
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/completions",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('choices', [{}])[0].get('text', '')
                    else:
                        error_text = await response.text()
                        raise Exception(f"API 에러 ({response.status}): {error_text}")
                        
        except Exception as e:
            print(f"❌ Custom LLM API 오류: {e}")
            return f"Error: {str(e)}"
    
    def generate_answer(self, prompt: str, **kwargs) -> str:
        """동기 호출 (비동기를 동기로 래핑)"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 실행 중인 루프가 있으면 스레드 사용
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, 
                        self.agenerate_answer(prompt, **kwargs)
                    )
                    return future.result()
            else:
                return asyncio.run(self.agenerate_answer(prompt, **kwargs))
        except Exception as e:
            print(f"❌ Custom LLM 동기 호출 실패: {e}")
            return f"Error: {str(e)}"
```

#### Step 3: LLM Factory에 통합 (llm_factory.py)

```python
# llm_factory.py의 create_llm 함수 수정
def create_llm(config: Config) -> LLM:
    """RAGAS 호환 LLM 인스턴스 생성"""
    provider = config.llm.provider.lower()
    
    try:
        if provider == 'gemini':
            # 기존 Gemini 코드
            pass
            
        elif provider == 'hcx':
            # 기존 HCX 코드
            pass
            
        elif provider == 'custom_llm':  # 새로운 provider
            from .custom_llm_adapter import CustomLLMAdapter
            
            # 설정에서 추가 파라미터 읽기
            base_url = config.llm.get('base_url', 'http://localhost:8080')
            
            adapter = CustomLLMAdapter(
                api_key=config.llm.api_key,
                model_name=config.llm.model_name,
                base_url=base_url
            )
            return LLMAdapterWrapper(adapter)
            
        else:
            raise ValueError(f"지원하지 않는 LLM 제공자: {provider}")
            
    except Exception as e:
        raise Exception(f"LLM 초기화 실패 ({provider}): {str(e)}")
```

#### Step 4: 설정 파일 업데이트 (config.yaml)

```yaml
# config.yaml
llm:
  provider: custom_llm
  api_key: ${CUSTOM_LLM_API_KEY}
  model_name: "my-custom-model-7b"
  base_url: "http://10.0.0.10:8080"  # 폐쇄망 내부 주소

# 또는 환경 변수 사용
# export CUSTOM_LLM_API_KEY="your-api-key"
```

### 3.2 Ollama 통합 예시 (로컬 LLM)

```python
# ollama_adapter.py
class OllamaAdapter:
    """Ollama 로컬 LLM 어댑터"""
    
    def __init__(self, model_name: str = "llama2", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        print(f"🦙 Ollama 어댑터 초기화: {model_name}")
        
        # 모델 존재 여부 확인
        self._check_model_exists()
    
    def _check_model_exists(self):
        """모델이 로컬에 있는지 확인"""
        import requests
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                if self.model_name not in model_names:
                    print(f"⚠️  모델 '{self.model_name}'이 없습니다. 사용 가능한 모델: {model_names}")
        except:
            print("⚠️  Ollama 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
    
    async def agenerate_answer(self, prompt: str, **kwargs) -> str:
        """Ollama API 호출"""
        import aiohttp
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get('temperature', 0.7),
                "num_predict": kwargs.get('max_tokens', 1000),
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('response', '')
                else:
                    raise Exception(f"Ollama API 에러: {response.status}")
```

---

## 4. 임베딩 모델 교체 가이드

### 4.1 새로운 임베딩 Provider 추가하기

#### Step 1: Config 설정 추가 (config_loader.py)

```python
class EmbeddingConfig(BaseModel):
    """임베딩 설정"""
    provider: str = Field("default", description="임베딩 제공자")
    device: str = Field("auto", description="디바이스")
    model_path: Optional[str] = Field(None, description="로컬 모델 경로")
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v):
        # 새로운 provider 추가
        allowed = ['default', 'bge_m3', 'sentence_transformers', 'custom_embedding']
        if v.lower() not in allowed:
            raise ValueError(f"지원하지 않는 임베딩 제공자: {v}. 허용: {allowed}")
        return v.lower()
```

#### Step 2: 임베딩 설정 메서드 구현 (evaluator.py)

```python
# evaluator.py에 추가
def _setup_custom_embeddings(self):
    """커스텀 임베딩 모델 설정"""
    try:
        from sentence_transformers import SentenceTransformer
        from langchain_huggingface import HuggingFaceEmbeddings
        from ragas.embeddings import LangchainEmbeddingsWrapper
        
        # 설정에서 모델 경로 읽기
        model_path = self.config.embedding.model_path or "sentence-transformers/all-MiniLM-L6-v2"
        device = self.config.embedding.device
        
        # 자동 디바이스 선택
        if device == 'auto':
            import torch
            if torch.cuda.is_available():
                device = 'cuda'
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                device = 'mps'
            else:
                device = 'cpu'
        
        print(f"🔧 커스텀 임베딩 모델 로딩: {model_path} (device: {device})")
        
        # 모델이 로컬에 있는지 확인
        model_path_obj = Path(model_path)
        if model_path_obj.exists():
            print(f"✅ 로컬 모델 사용: {model_path_obj.absolute()}")
            model_name_or_path = str(model_path_obj.absolute())
        else:
            print(f"📥 Hugging Face에서 모델 다운로드: {model_path}")
            model_name_or_path = model_path
        
        # HuggingFace 임베딩 생성
        lc_embeddings = HuggingFaceEmbeddings(
            model_name=model_name_or_path,
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True}  # 정규화 옵션
        )
        
        # RAGAS 호환 래퍼로 감싸기
        embeddings = LangchainEmbeddingsWrapper(lc_embeddings)
        
        print(f"✅ 커스텀 임베딩 로드 완료 (device: {device})")
        return embeddings
        
    except Exception as e:
        raise Exception(f"커스텀 임베딩 모델 로드 실패: {e}")

# _setup_embeddings 메서드 수정
def _setup_embeddings(self):
    """임베딩 모델을 설정합니다."""
    embedding_provider = self.config.embedding.provider.lower()
    
    print(f"🔧 임베딩 설정: {embedding_provider}")
    
    if embedding_provider == 'default':
        # 기존 코드
        pass
    elif embedding_provider == 'bge_m3':
        # 기존 코드
        pass
    elif embedding_provider == 'custom_embedding':  # 새로운 provider
        embeddings = self._setup_custom_embeddings()
        return embeddings
    else:
        print(f"⚠️  지원하지 않는 임베딩 제공자: {embedding_provider}")
        return None
```

### 4.2 다국어 임베딩 모델 예시

```python
def _setup_multilingual_embeddings(self):
    """다국어 지원 임베딩 모델 설정"""
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        from ragas.embeddings import LangchainEmbeddingsWrapper
        
        # 다국어 모델 옵션
        multilingual_models = {
            'xlm-roberta': 'sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens',
            'labse': 'sentence-transformers/LaBSE',
            'multilingual-e5': 'intfloat/multilingual-e5-large'
        }
        
        model_name = multilingual_models.get(
            self.config.embedding.get('model_variant', 'xlm-roberta')
        )
        
        print(f"🌍 다국어 임베딩 모델 로딩: {model_name}")
        
        lc_embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': self.config.embedding.device},
            encode_kwargs={
                'normalize_embeddings': True,
                'batch_size': 32  # 배치 크기 조정
            }
        )
        
        return LangchainEmbeddingsWrapper(lc_embeddings)
        
    except Exception as e:
        raise Exception(f"다국어 임베딩 모델 로드 실패: {e}")
```

---

## 5. 문제 해결 팁

### 5.1 디버깅 방법

```python
# 상세 로그 활성화
import logging
logging.basicConfig(level=logging.DEBUG)

# LangChain 디버그 모드
from langchain.globals import set_debug
set_debug(True)

# 환경 변수로 디버그 활성화
export RAGTRACE_DEBUG=1
```

### 5.2 성능 최적화

```python
# 배치 처리 활성화
config.evaluation.batch_size = 10  # 동시 처리 수 증가

# 캐싱 활성화
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_embedding(text: str):
    return embedding_model.encode(text)
```

### 5.3 메모리 관리

```python
# GPU 메모리 정리
import torch
torch.cuda.empty_cache()

# 가비지 컬렉션 강제 실행
import gc
gc.collect()
```

### 5.4 일반적인 문제와 해결책

| 문제 | 원인 | 해결책 |
|------|------|--------|
| "API key not found" | 환경 변수 미설정 | `.env` 파일 확인 또는 `export` 명령 사용 |
| "Model not found" | 모델 파일 누락 | 모델 경로 확인 및 다운로드 |
| "Out of memory" | GPU/RAM 부족 | 배치 크기 축소 또는 CPU 사용 |
| "Connection timeout" | 네트워크 문제 | 프록시 설정 확인 또는 타임아웃 증가 |
| "Rate limit exceeded" | API 제한 초과 | Rate limiter 간격 증가 |

---

## 추가 리소스

- [RAGTrace Lite GitHub](https://github.com/yourusername/ragtrace-lite)
- [RAGAS 공식 문서](https://docs.ragas.io/)
- [LangChain 문서](https://docs.langchain.com/)
- [Hugging Face Hub](https://huggingface.co/)

질문이나 문제가 있으시면 이슈를 생성해주세요!