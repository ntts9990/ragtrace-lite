# HCX RAGAS 비동기 구현 상세 분석 보고서

## 1. 문제 요약

### 현재 상태
- HCX-005 프록시 레이어가 JSON 변환은 성공적으로 수행
- 그러나 모든 평가 점수가 NaN으로 반환됨
- 비동기 에러: `TypeError: object LLMResult can't be used in 'await' expression`

### 근본 원인
1. RAGAS의 비동기 평가 파이프라인이 특정한 async/await 패턴을 기대
2. HCX 프록시가 이 패턴을 완벽하게 구현하지 못함
3. 'reference' 컬럼 누락으로 일부 메트릭 실행 불가

## 2. 상세 분석

### 2.1 RAGAS의 비동기 호출 패턴

RAGAS는 다음과 같은 방식으로 LLM을 호출합니다:

```python
# RAGAS 내부 코드 (추정)
async def evaluate_metric():
    # LLM이 비동기 컨텍스트에서 호출됨
    result = await llm.generate(prompts)  # 또는 agenerate
    # result는 LLMResult 객체여야 함
```

### 2.2 현재 HCX 프록시 구현

```python
def generate(self, prompts, **kwargs):
    try:
        loop = asyncio.get_running_loop()
        # 비동기 컨텍스트에서는 코루틴 반환
        return self.agenerate(prompts, **kwargs)
    except RuntimeError:
        # 동기 컨텍스트에서는 LLMResult 반환
        return LLMResult(generations=...)

def agenerate(self, prompts, **kwargs):
    async def _async_generate():
        # 실제 비동기 로직
        return LLMResult(generations=...)
    return _async_generate()  # 코루틴 객체 반환
```

### 2.3 문제점

1. **비동기 메서드 체인**: `_acall` 메서드가 `functools.partial` 사용 시 kwargs 전달 문제
2. **컨텍스트 감지**: 일부 RAGAS 내부 호출에서 컨텍스트 감지 실패
3. **데이터 형식**: 'reference' vs 'ground_truths' 컬럼 불일치

## 3. 시도한 해결 방법

### 3.1 비동기 컨텍스트 감지 (✅ 구현됨)
- `asyncio.get_running_loop()`를 사용하여 비동기 컨텍스트 감지
- 컨텍스트에 따라 다른 반환 타입 제공

### 3.2 메트릭별 프롬프트 최적화 (✅ 구현됨)
- faithfulness, answer_relevancy 등 각 메트릭별 전용 파싱 로직
- NLI 형식 지원 추가

### 3.3 비동기 실행 래퍼 (✅ 구현됨)
- `run_in_executor`를 사용한 동기 함수의 비동기 실행

## 4. 남은 문제와 해결 방안

### 4.1 즉시 적용 가능한 해결책

1. **데이터 전처리 개선**
```python
# evaluator.py에서 reference 컬럼 자동 추가
if 'reference' not in dataset.column_names and 'ground_truths' in dataset.column_names:
    # ground_truths의 첫 번째 요소를 reference로 사용
    dataset = dataset.map(lambda x: {
        **x, 
        'reference': x['ground_truths'][0] if x['ground_truths'] else ''
    })
```

2. **동기 평가 모드 강제**
```python
# RAGAS 평가를 동기 모드로 실행
from ragas.evaluation import evaluate_sync  # 만약 존재한다면
# 또는 asyncio.run()으로 래핑
```

### 4.2 중장기 해결책

1. **커스텀 평가 파이프라인 구현**
   - RAGAS를 사용하지 않고 직접 메트릭 계산
   - HCX 응답을 직접 파싱하여 점수 계산

2. **LangChain 베이스 클래스 재구현**
   - BaseLLM 대신 커스텀 베이스 클래스 사용
   - 완전한 비동기 지원 구현

3. **RAGAS 포크 및 수정**
   - RAGAS 소스를 수정하여 HCX 호환성 추가
   - PR 제출하여 공식 지원 요청

## 5. 테스트 결과 상세

### 5.1 성공한 부분
- JSON 변환: "1. statement" → {"statements": ["statement"]} ✅
- 프롬프트 타입 감지: faithfulness vs answer_relevancy 구분 ✅
- Rate limiting 처리: 12초 간격 유지 ✅

### 5.2 실패한 부분
- 평가 점수 계산: 모든 메트릭 NaN ❌
- 비동기 에러 완전 해결: 여전히 TypeError 발생 ❌
- reference 컬럼 자동 처리: 미구현 ❌

## 6. 디버깅을 위한 추가 정보

### 6.1 에러 발생 위치
```
File: ragas/metrics/_faithfulness.py (추정)
Line: await llm.generate() 호출 부분
Error: TypeError: object LLMResult can't be used in 'await' expression
```

### 6.2 의심되는 원인
1. RAGAS가 `generate` 메서드를 직접 await로 호출
2. 하지만 generate가 때로는 코루틴, 때로는 LLMResult를 반환
3. 일관성 없는 반환 타입으로 인한 에러

### 6.3 추가 디버깅 방법
```python
# HCX 프록시에 상세 로깅 추가
import logging
logging.basicConfig(level=logging.DEBUG)

def generate(self, prompts, **kwargs):
    logger.debug(f"generate called with prompts: {prompts}")
    logger.debug(f"Current context: {asyncio.current_task()}")
    # ... 기존 코드
```

## 7. 권장 사항

### 7.1 단기 (1-2일)
1. reference 컬럼 자동 처리 구현
2. 동기 평가 모드 테스트
3. 에러 로깅 강화로 정확한 문제 위치 파악

### 7.2 중기 (1주)
1. 커스텀 메트릭 계산 로직 구현
2. RAGAS 대체 평가 프레임워크 검토
3. HCX 전용 평가 파이프라인 설계

### 7.3 장기 (1개월)
1. RAGAS 프로젝트에 HCX 지원 PR 제출
2. LangChain 커뮤니티와 협력하여 표준화
3. 자체 평가 프레임워크 개발

## 8. 결론

HCX-005와 RAGAS의 통합은 기술적으로 가능하며, JSON 변환 레이어는 성공적으로 작동합니다. 
하지만 비동기 실행 패턴의 불일치로 인해 실제 평가 점수 계산이 실패하고 있습니다.

단기적으로는 동기 평가 모드나 커스텀 평가 로직을 사용하고, 
장기적으로는 RAGAS 또는 LangChain 레벨에서의 근본적인 해결이 필요합니다.

## 9. 참고 자료

- RAGAS 소스 코드: https://github.com/explodinggradients/ragas
- LangChain LLM 인터페이스: https://python.langchain.com/docs/modules/model_io/llms/
- 비동기 프로그래밍 패턴: https://docs.python.org/3/library/asyncio.html