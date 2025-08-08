# RAGTrace Lite 모델 교체 아키텍처 가이드

## 목차
1. [아키텍처 개요](#1-아키텍처-개요)
2. [LLM 아키텍처 상세](#2-llm-아키텍처-상세)
3. [임베딩 모델 아키텍처](#3-임베딩-모델-아키텍처)
4. [디자인 패턴 분석](#4-디자인-패턴-분석)
5. [RAGAS 통합 메커니즘](#5-ragas-통합-메커니즘)
6. [새로운 모델 추가 가이드](#6-새로운-모델-추가-가이드)

---

## 1. 아키텍처 개요

RAGTrace Lite는 다양한 LLM과 임베딩 모델을 쉽게 교체할 수 있도록 **플러그인 기반 아키텍처**를 채택하고 있습니다.

### 전체 아키텍처 다이어그램

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Config     │────▶│  Factory     │────▶│   RAGAS      │
│  (YAML/.env) │     │  Pattern     │     │ Evaluation   │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
        ┌──────────────┐       ┌──────────────┐
        │ LLM Factory  │       │  Embedding   │
        │              │       │   Factory    │
        └──────────────┘       └──────────────┘
                │                       │
     ┌──────────┴──────────┐           │
     ▼                     ▼           ▼
┌─────────┐           ┌─────────┐ ┌─────────┐
│ Gemini  │           │   HCX   │ │  BGE-M3 │
│ Adapter │           │ Adapter │ │ Wrapper │
└─────────┘           └─────────┘ └─────────┘
     │                     │           │
     ▼                     ▼           ▼
┌─────────┐           ┌─────────┐ ┌─────────┐
│   LLM   │           │   LLM   │ │LangChain│
│ Wrapper │           │ Wrapper │ │Embedding│
└─────────┘           └─────────┘ └─────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ HCX RAGAS   │
                    │   Proxy     │
                    └─────────────┘
```

### 핵심 설계 원칙

1. **인터페이스 분리 원칙 (ISP)**: 각 컴포넌트는 명확한 책임을 가집니다
2. **의존성 역전 원칙 (DIP)**: 구체적인 구현이 아닌 추상화에 의존합니다
3. **개방-폐쇄 원칙 (OCP)**: 확장에는 열려있고 수정에는 닫혀있습니다

---

## 2. LLM 아키텍처 상세

### 2.1 계층 구조

```
Application Layer (main.py, cli.py)
         │
         ▼
    Factory Layer (llm_factory.py)
         │
         ▼
    Adapter Layer (gemini_adapter, hcx_adapter)
         │
         ▼
    Wrapper Layer (LLMAdapterWrapper)
         │
         ▼
    Proxy Layer (HCXRAGASProxy - HCX only)
         │
         ▼
    RAGAS Framework
```

### 2.2 Factory Pattern 구현

```python
# llm_factory.py
def create_llm(config: Config) -> LLM:
    """RAGAS 호환 LLM 인스턴스 생성"""
    provider = config.llm.provider.lower()
    
    try:
        if provider == 'gemini':
            # 1. 어댑터 생성
            adapter = GeminiAdapter(
                api_key=config.llm.api_key,
                model_name=config.llm.model_name
            )
            # 2. LangChain 래퍼로 감싸기
            return LLMAdapterWrapper(adapter)
            
        elif provider == 'hcx':
            # 1. 어댑터 생성
            adapter = HcxAdapter(
                api_key=config.llm.api_key,
                model_name=config.llm.model_name
            )
            # 2. LangChain 래퍼로 감싸기
            base_llm = LLMAdapterWrapper(adapter)
            # 3. RAGAS 호환을 위한 프록시 추가
            return HCXRAGASProxy(base_llm)
            
        else:
            raise ValueError(f"지원하지 않는 LLM 제공자: {provider}")
    except Exception as e:
        raise Exception(f"LLM 초기화 실패 ({provider}): {str(e)}")
```

### 2.3 Adapter Pattern 구현

각 LLM 제공자마다 독립적인 어댑터 클래스를 구현합니다:

```python
class GeminiAdapter:
    """Gemini API 어댑터 (순수 Python 클래스)"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel(model_name)
    
    async def agenerate_answer(self, prompt: str, **kwargs) -> str:
        """비동기 API 호출"""
        generation_config = {
            'temperature': kwargs.get('temperature', 0.1),
            'max_output_tokens': kwargs.get('max_tokens', 1000)
        }
        
        response = await self.gemini_model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        
        # 응답 추출 로직
        return extracted_text
    
    def generate_answer(self, prompt: str, **kwargs) -> str:
        """동기 호출 (비동기를 동기로 래핑)"""
        return asyncio.run(self.agenerate_answer(prompt, **kwargs))
```

### 2.4 Wrapper Pattern 구현

어댑터를 LangChain 호환 인터페이스로 감싸는 래퍼:

```python
class LLMAdapterWrapper(LLM):
    """어댑터를 LangChain LLM으로 변환하는 래퍼"""
    
    adapter: Any = Field(default=None, exclude=True)
    
    def __init__(self, adapter: Any, **kwargs):
        super().__init__(**kwargs)
        self.adapter = adapter
    
    @property
    def _llm_type(self) -> str:
        return f"adapter-{type(self.adapter).__name__.lower()}"
    
    def _call(self, prompt: str, **kwargs) -> str:
        """동기 호출 - LangChain 필수 메서드"""
        return self.adapter.generate_answer(prompt, **kwargs)
    
    async def _acall(self, prompt: str, **kwargs) -> str:
        """비동기 호출 - LangChain 필수 메서드"""
        return await self.adapter.agenerate_answer(prompt, **kwargs)
    
    def generate(self, prompts: List[str], **kwargs) -> LLMResult:
        """RAGAS 호환 generate 메서드"""
        generations = []
        for prompt in prompts:
            response = self._call(prompt, **kwargs)
            generation = Generation(text=response)
            generations.append([generation])
        return LLMResult(generations=generations)
```

### 2.5 Proxy Pattern 구현 (HCX 전용)

HCX의 응답을 RAGAS가 이해할 수 있는 형식으로 변환:

```python
class HCXRAGASProxy(BaseLLM):
    """HCX LLM을 RAGAS와 호환되도록 하는 프록시"""
    
    # RAGAS 메트릭별 예상 스키마
    METRIC_SCHEMAS = {
        'faithfulness': {
            'schema': {"statements": [{"statement": str, "reason": str, "verdict": int}]},
            'keywords': ['faithfulness', 'statements', 'verdict']
        },
        'answer_relevancy': {
            'schema': {"question": str},
            'keywords': ['relevancy', 'relevant question']
        }
    }
    
    def _detect_metric_type(self, prompt: str) -> Optional[str]:
        """프롬프트에서 RAGAS 메트릭 타입 감지"""
        prompt_lower = prompt.lower()
        
        for metric, info in self.METRIC_SCHEMAS.items():
            if any(keyword in prompt_lower for keyword in info['keywords']):
                return metric
        return None
    
    async def _acall(self, prompt: str, **kwargs) -> str:
        """비동기 호출 with 응답 변환"""
        # 1. 메트릭 타입 감지
        metric_type = self._detect_metric_type(prompt)
        
        # 2. 기본 LLM 호출
        response = await self.base_llm._acall(prompt, **kwargs)
        
        # 3. 메트릭별 응답 변환
        if metric_type:
            response = self._transform_response(response, metric_type)
        
        return response
```

---

## 3. 임베딩 모델 아키텍처

### 3.1 임베딩 설정 흐름

```python
# evaluator.py
def _setup_embeddings(self):
    """임베딩 모델을 설정합니다."""
    embedding_provider = self.config.embedding.provider.lower()
    
    if embedding_provider == 'bge_m3':
        embeddings = self._setup_bge_m3_embeddings()
    elif embedding_provider == 'default':
        embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
    else:
        embeddings = None
    
    return embeddings
```

### 3.2 BGE-M3 임베딩 설정

```python
def _setup_bge_m3_embeddings(self):
    """BGE-M3 임베딩 모델을 설정합니다."""
    # 1. 모델 경로 확인
    model_path = Path(os.getenv('BGE_M3_MODEL_PATH', './models/bge-m3'))
    
    # 2. 디바이스 자동 선택
    device = self._select_device()
    
    # 3. HuggingFace 임베딩 생성
    lc_embeddings = HuggingFaceEmbeddings(
        model_name=str(model_path),
        model_kwargs={'device': device}
    )
    
    # 4. RAGAS 호환 래퍼로 감싸기
    embeddings = LangchainEmbeddingsWrapper(lc_embeddings)
    
    return embeddings
```

---

## 4. 디자인 패턴 분석

### 4.1 Adapter Pattern (어댑터 패턴)

**목적**: 서로 다른 인터페이스를 가진 LLM API들을 통일된 인터페이스로 제공

```
┌─────────────────┐          ┌─────────────────┐
│  Client Code    │────────▶ │ Common Interface│
└─────────────────┘          └─────────────────┘
                                      △
                    ┌─────────────────┴─────────────────┐
                    │                                   │
            ┌───────────────┐                 ┌───────────────┐
            │ GeminiAdapter │                 │  HcxAdapter   │
            └───────────────┘                 └───────────────┘
                    │                                 │
            ┌───────────────┐                 ┌───────────────┐
            │  Gemini API   │                 │   HCX API     │
            └───────────────┘                 └───────────────┘
```

**장점**:
- 새로운 LLM 추가가 쉬움
- 기존 코드 수정 없이 확장 가능
- 각 LLM의 특성을 독립적으로 처리

### 4.2 Factory Pattern (팩토리 패턴)

**목적**: 객체 생성 로직을 캡슐화하여 클라이언트 코드와 분리

```python
def create_llm(config):
    if config.provider == "gemini":
        return create_gemini_llm(config)
    elif config.provider == "hcx":
        return create_hcx_llm(config)
    # 새로운 provider 추가 시 여기에 추가
```

**장점**:
- 설정 기반 객체 생성
- 복잡한 초기화 로직 숨김
- 테스트 용이성

### 4.3 Proxy Pattern (프록시 패턴)

**목적**: 실제 객체에 대한 대리자 역할을 하며 추가 기능 제공

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   RAGAS     │────▶│ HCX Proxy   │────▶│ Real HCX    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    Response Transform
```

**HCX Proxy의 역할**:
1. RAGAS 메트릭 타입 감지
2. HCX 응답을 RAGAS 형식으로 변환
3. 에러 처리 및 폴백 메커니즘

### 4.4 Wrapper Pattern (래퍼 패턴)

**목적**: 기존 클래스를 새로운 인터페이스로 감싸서 호환성 제공

```python
class LLMAdapterWrapper(LangChainLLM):
    def __init__(self, adapter):
        self.adapter = adapter  # 순수 Python 어댑터
    
    def _call(self, prompt):
        return self.adapter.generate_answer(prompt)  # 위임
```

---

## 5. RAGAS 통합 메커니즘

### 5.1 메트릭별 응답 스키마

RAGAS는 각 평가 메트릭마다 특정 JSON 스키마를 기대합니다:

```python
# Faithfulness 메트릭
{
    "statements": [
        {
            "statement": "문장 내용",
            "reason": "판단 이유",
            "verdict": 1  # 0 또는 1
        }
    ]
}

# Answer Relevancy 메트릭
{
    "question": "생성된 질문"
}

# Context Precision 메트릭
{
    "relevance": 1  # 0 또는 1
}
```

### 5.2 응답 변환 전략

```python
def _transform_response(self, raw_response: str, metric_type: str) -> str:
    """원시 응답을 RAGAS 형식으로 변환"""
    
    # 1. JSON 파싱 시도
    try:
        data = json.loads(raw_response)
        if self._validate_schema(data, metric_type):
            return json.dumps(data)
    except:
        pass
    
    # 2. 텍스트 파싱 전략
    if metric_type == 'faithfulness':
        return self._parse_faithfulness_text(raw_response)
    elif metric_type == 'answer_relevancy':
        return self._parse_relevancy_text(raw_response)
    
    # 3. 기본값 반환
    return self._get_default_response(metric_type)
```

### 5.3 프롬프트 강화

HCX 어댑터는 RAGAS 메트릭에 맞는 프롬프트를 강화합니다:

```python
def enhance_prompt_for_hcx(prompt: str, metric_type: str) -> str:
    """HCX를 위한 프롬프트 강화"""
    
    enhancements = {
        'faithfulness': """
반드시 다음 JSON 형식으로 응답하세요:
{
    "statements": [
        {"statement": "문장", "reason": "이유", "verdict": 0 또는 1}
    ]
}
""",
        'answer_relevancy': """
주어진 답변과 관련된 질문을 생성하고 JSON 형식으로 응답하세요:
{"question": "생성한 질문"}
"""
    }
    
    if metric_type in enhancements:
        return prompt + "\n\n" + enhancements[metric_type]
    return prompt
```

---

## 6. 새로운 모델 추가 가이드

### 6.1 새로운 LLM 추가하기

#### Step 1: 어댑터 클래스 생성

```python
# ollama_adapter.py
class OllamaAdapter:
    """Ollama 로컬 LLM 어댑터"""
    
    def __init__(self, model_name: str = "llama2", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self._check_model_exists()
    
    async def agenerate_answer(self, prompt: str, **kwargs) -> str:
        """Ollama API 비동기 호출"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get('temperature', 0.7),
                    "num_predict": kwargs.get('max_tokens', 1000)
                }
            }
            
            async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                data = await response.json()
                return data.get('response', '')
    
    def generate_answer(self, prompt: str, **kwargs) -> str:
        """동기 호출"""
        return asyncio.run(self.agenerate_answer(prompt, **kwargs))
```

#### Step 2: Factory에 추가

```python
# llm_factory.py에 추가
elif provider == 'ollama':
    from .ollama_adapter import OllamaAdapter
    
    adapter = OllamaAdapter(
        model_name=config.llm.model_name or "llama2",
        base_url=config.llm.get('base_url', 'http://localhost:11434')
    )
    return LLMAdapterWrapper(adapter)
```

#### Step 3: Config 업데이트

```python
# config_loader.py
@field_validator('provider')
@classmethod
def validate_provider(cls, v):
    allowed = ['gemini', 'hcx', 'ollama']  # ollama 추가
    if v.lower() not in allowed:
        raise ValueError(f"지원하지 않는 LLM 제공자: {v}")
    return v.lower()
```

### 6.2 새로운 임베딩 모델 추가하기

#### Step 1: 임베딩 설정 메서드 추가

```python
# evaluator.py에 추가
def _setup_multilingual_e5_embeddings(self):
    """다국어 E5 임베딩 설정"""
    from langchain_huggingface import HuggingFaceEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper
    
    model_name = "intfloat/multilingual-e5-large"
    device = self._select_device()
    
    lc_embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': device},
        encode_kwargs={
            'normalize_embeddings': True,
            'batch_size': 32
        }
    )
    
    return LangchainEmbeddingsWrapper(lc_embeddings)
```

#### Step 2: _setup_embeddings 메서드 수정

```python
elif embedding_provider == 'multilingual_e5':
    embeddings = self._setup_multilingual_e5_embeddings()
```

### 6.3 RAGAS 호환성 체크리스트

새로운 모델을 추가할 때 확인해야 할 사항:

1. **LLM 체크리스트**:
   - [ ] `generate()` 메서드 구현 (동기)
   - [ ] `agenerate()` 메서드 구현 (비동기)
   - [ ] `_llm_type` 속성 정의
   - [ ] JSON 응답 처리 능력
   - [ ] 에러 처리 및 재시도 로직

2. **임베딩 체크리스트**:
   - [ ] `LangchainEmbeddingsWrapper`로 감싸기
   - [ ] 벡터 차원 호환성 확인
   - [ ] 배치 처리 지원
   - [ ] 정규화 옵션 설정

3. **성능 최적화**:
   - [ ] 비동기 처리 구현
   - [ ] 배치 처리 최적화
   - [ ] 캐싱 메커니즘
   - [ ] Rate limiting 처리

---

## 요약

RAGTrace Lite의 모델 교체 아키텍처는 다음과 같은 특징을 가집니다:

1. **모듈성**: 각 컴포넌트가 독립적으로 교체 가능
2. **확장성**: 새로운 모델 추가가 간단
3. **호환성**: RAGAS 프레임워크와 완벽 호환
4. **유연성**: 동기/비동기 처리 모두 지원
5. **견고성**: 에러 처리 및 폴백 메커니즘

이 아키텍처를 통해 다양한 LLM과 임베딩 모델을 쉽게 통합하고, RAGAS 평가 프레임워크의 요구사항을 충족시킬 수 있습니다.