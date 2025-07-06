# Contributing to RAGTrace Lite

RAGTrace Lite에 기여해주셔서 감사합니다! 이 문서는 프로젝트에 기여하는 방법을 안내합니다.

## 기여 방법

### 1. Issue 보고

버그를 발견하거나 새로운 기능을 제안하려면:

1. [기존 Issue](https://github.com/yourusername/ragtrace-lite/issues) 확인
2. 중복이 없다면 새 Issue 생성
3. Issue 템플릿 사용:
   - 🐛 Bug Report
   - ✨ Feature Request
   - 📚 Documentation

### 2. Pull Request 제출

#### 준비 작업

1. **Fork 및 Clone**
   ```bash
   git clone https://github.com/yourusername/ragtrace-lite.git
   cd ragtrace-lite
   git remote add upstream https://github.com/originalowner/ragtrace-lite.git
   ```

2. **브랜치 생성**
   ```bash
   git checkout -b feature/your-feature-name
   # 또는
   git checkout -b fix/issue-number
   ```

3. **개발 환경 설정**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

#### 코드 작성

1. **코딩 스타일**
   - PEP 8 준수
   - Type hints 사용
   - Docstring 작성 (Google style)

2. **예제**
   ```python
   def calculate_score(
       values: List[float], 
       weights: Optional[List[float]] = None
   ) -> float:
       """
       Calculate weighted average score.
       
       Args:
           values: List of score values
           weights: Optional weights for each value
           
       Returns:
           Weighted average score
           
       Raises:
           ValueError: If lengths don't match
       """
       if weights and len(values) != len(weights):
           raise ValueError("Values and weights must have same length")
       
       if weights:
           return sum(v * w for v, w in zip(values, weights)) / sum(weights)
       return sum(values) / len(values)
   ```

#### 테스트 작성

1. **단위 테스트**
   ```python
   # tests/test_score_calculator.py
   import pytest
   from ragtrace_lite.calculator import calculate_score
   
   def test_calculate_score_without_weights():
       assert calculate_score([1, 2, 3]) == 2.0
   
   def test_calculate_score_with_weights():
       assert calculate_score([1, 2, 3], [1, 2, 1]) == 2.0
   
   def test_calculate_score_mismatched_lengths():
       with pytest.raises(ValueError):
           calculate_score([1, 2], [1, 2, 3])
   ```

2. **테스트 실행**
   ```bash
   # 모든 테스트
   pytest
   
   # 커버리지 포함
   pytest --cov=ragtrace_lite
   
   # 특정 테스트
   pytest tests/test_score_calculator.py
   ```

#### 코드 품질 검사

1. **포맷팅**
   ```bash
   # 코드 포맷팅
   black src/ tests/
   
   # Import 정렬
   isort src/ tests/
   ```

2. **린팅**
   ```bash
   # 코드 스타일 검사
   flake8 src/ tests/
   
   # 타입 검사
   mypy src/
   ```

3. **Pre-commit 사용**
   ```bash
   # Pre-commit 설치
   pre-commit install
   
   # 수동 실행
   pre-commit run --all-files
   ```

#### Pull Request 제출

1. **커밋 메시지 규칙**
   ```
   <type>: <subject>
   
   <body>
   
   <footer>
   ```
   
   Types:
   - feat: 새로운 기능
   - fix: 버그 수정
   - docs: 문서 수정
   - style: 코드 스타일 변경
   - refactor: 리팩토링
   - test: 테스트 추가/수정
   - chore: 빌드, 설정 등

   예제:
   ```
   feat: Add BGE-M3 GPU auto-detection
   
   - Automatically detect CUDA/MPS/CPU availability
   - Optimize batch size based on device
   - Add device selection configuration
   
   Closes #123
   ```

2. **PR 체크리스트**
   - [ ] 코드가 스타일 가이드를 따르는가?
   - [ ] 테스트를 추가/업데이트했는가?
   - [ ] 문서를 업데이트했는가?
   - [ ] CHANGELOG.md를 업데이트했는가?
   - [ ] 모든 테스트가 통과하는가?

### 3. 문서 기여

문서 개선도 중요한 기여입니다:

1. **문서 유형**
   - API 문서
   - 사용 가이드
   - 튜토리얼
   - 예제 코드

2. **문서 작성 가이드**
   - 명확하고 간결하게
   - 예제 코드 포함
   - 한국어/영어 모두 환영

## 개발 가이드라인

### 아키텍처 원칙

1. **Clean Architecture**
   - 레이어 분리 유지
   - 의존성 방향 준수
   - 인터페이스 활용

2. **SOLID 원칙**
   - Single Responsibility
   - Open/Closed
   - Liskov Substitution
   - Interface Segregation
   - Dependency Inversion

### 성능 고려사항

1. **메모리 효율성**
   - 대용량 데이터 처리 시 스트리밍
   - 불필요한 복사 방지
   - 적절한 데이터 구조 선택

2. **API 호출 최적화**
   - 배치 처리 활용
   - 적절한 타임아웃 설정
   - 재시도 로직 구현

### 보안 고려사항

1. **API 키 보호**
   - 환경 변수 사용
   - 코드에 하드코딩 금지
   - 로그에 노출 방지

2. **입력 검증**
   - 사용자 입력 검증
   - SQL 인젝션 방지
   - Path traversal 방지

## 릴리스 프로세스

1. **버전 관리**
   - Semantic Versioning (MAJOR.MINOR.PATCH)
   - 변경사항에 따른 버전 증가

2. **릴리스 체크리스트**
   - [ ] 버전 번호 업데이트
   - [ ] CHANGELOG.md 업데이트
   - [ ] 문서 업데이트
   - [ ] 태그 생성
   - [ ] PyPI 배포

## 도움 받기

질문이나 도움이 필요하면:

ntts9990@gmail.com

## 라이선스

기여하신 코드는 프로젝트의 듀얼 라이선스(MIT/Apache 2.0)를 따릅니다.

## 감사의 말

모든 기여자분들께 감사드립니다! 🎉
