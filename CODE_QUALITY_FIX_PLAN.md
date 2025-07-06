# 코드 품질 개선 계획

## 📋 현재 상태 분석

### 발견된 문제 요약

1. **Black 포매팅 이슈**
   - 19개 파일이 재포맷 필요
   - 코드 스타일이 일관되지 않음

2. **isort 임포트 정렬 이슈**
   - 18개 파일의 import 구문 정렬 필요
   - 표준 라이브러리, 서드파티, 로컬 임포트 순서가 뒤섞임

3. **mypy 타입 체킹 오류 (95개)**
   - 함수 반환 타입 누락
   - 인자 타입 어노테이션 누락
   - Python 3.10+ Union 구문 사용 (`X | Y`)
   - 누락된 타입 스텁 패키지 (types-PyYAML)
   - Pydantic 필드 검증 오류

4. **pytest 테스트 실패 (20개 실패, 7개 에러)**
   - Pydantic Config 모델의 `llm` 필드 관련 ValidationError
   - enhanced CLI 명령어 AttributeError
   - 데이터베이스 관련 ResourceWarning

## 🔧 단계별 해결 전략

### 1단계: 환경 준비 및 의존성 설치
```bash
# 타입 스텁 패키지 설치
uv pip install types-PyYAML

# 개발 의존성 확인
uv pip install -e ".[dev]"
```

### 2단계: 자동 포매팅 적용 (안전한 변경)
```bash
# import 정렬
uv run isort src tests

# 코드 포매팅
uv run black src tests
```

### 3단계: Python 3.9 호환성 문제 해결

#### Union 구문 변경
```python
# 변경 전 (Python 3.10+)
def func(param: str | None) -> list[str] | None:
    pass

# 변경 후 (Python 3.9+)
from typing import Union, List, Optional

def func(param: Optional[str]) -> Optional[List[str]]:
    pass
```

### 4단계: Pydantic Config 모델 수정

#### 주요 문제점
- 테스트에서 Config 초기화 시 `llm` 필드 누락
- 필수 필드들의 기본값 부재

#### 해결 방안
```python
# config_loader.py 수정
class Config(BaseSettings):
    # llm 필드를 Optional로 변경
    llm: Optional[LLMConfig] = None
    
    # 또는 기본값 제공
    llm: LLMConfig = Field(default_factory=lambda: LLMConfig(
        provider="hcx",
        model_name="HCX-003"
    ))
```

### 5단계: 타입 어노테이션 추가

#### 함수 반환 타입 추가
```python
# 변경 전
def setup_logging(config):
    # ...

# 변경 후
def setup_logging(config: LoggingConfig) -> None:
    # ...
```

#### 복잡한 타입 처리
```python
from typing import Dict, List, Any, Optional, Union

def process_data(
    data: Dict[str, Any],
    options: Optional[List[str]] = None
) -> Union[Dict[str, Any], None]:
    # ...
```

### 6단계: 테스트 수정

#### Config 초기화 수정
```python
# conftest.py 또는 test 파일
@pytest.fixture
def test_config():
    return Config(
        llm=LLMConfig(
            provider="hcx",
            model_name="HCX-003",
            api_key="test-key"
        ),
        embedding=EmbeddingConfig(
            provider="bge-m3",
            model_name="BAAI/bge-m3",
            device="cpu"
        ),
        # ... 기타 필수 필드
    )
```

#### Enhanced CLI 테스트 수정
- `main_enhanced` 함수가 실제로 존재하는지 확인
- CLI 명령어 등록 확인

### 7단계: 최종 검증
```bash
# 각 도구별 검증
uv run black --check src tests
uv run isort --check-only src tests
uv run mypy src --ignore-missing-imports
uv run pytest tests -v

# 전체 CI 파이프라인 실행
uv run black src tests && \
uv run isort src tests && \
uv run mypy src && \
uv run pytest
```

## 📊 예상 작업 시간

| 작업 | 예상 시간 | 우선순위 |
|------|----------|----------|
| 의존성 설치 | 5분 | 높음 |
| 자동 포매팅 | 10분 | 높음 |
| Union 구문 수정 | 30분 | 높음 |
| Config 모델 수정 | 1시간 | 높음 |
| 타입 어노테이션 | 2시간 | 중간 |
| 테스트 수정 | 1시간 | 중간 |
| 최종 검증 | 30분 | 낮음 |

**총 예상 시간: 약 5시간**

## ⚠️ 주의사항

1. **단계별 커밋**: 각 단계 완료 후 별도 커밋으로 진행 추적
2. **테스트 우선**: 변경 후 즉시 테스트 실행으로 회귀 방지
3. **백업**: 대규모 변경 전 현재 상태 백업
4. **점진적 수정**: 한 번에 모든 것을 고치려 하지 말고 단계별로 진행

## 🎯 성공 지표

- [ ] Black 검사 통과
- [ ] isort 검사 통과
- [ ] mypy 오류 0개
- [ ] 모든 테스트 통과
- [ ] CI/CD 파이프라인 그린

## 📝 진행 상황 추적

### 완료된 작업
- [x] 문제 분석 및 계획 수립

### 진행 중
- [ ] 의존성 설치
- [ ] 자동 포매팅

### 대기 중
- [ ] Python 3.9 호환성
- [ ] Pydantic 모델 수정
- [ ] 타입 어노테이션
- [ ] 테스트 수정
- [ ] 최종 검증