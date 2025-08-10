# RAGTrace Lite v2 리팩토링 계획

## 🚨 Phase 1: 긴급 정리 (1-2일)

### 1.1 프로젝트 구조 정리
```bash
# 중복 제거
- [ ] BGE-M3 모델 중복 제거 (4.3GB 절약)
- [ ] 가상환경 통합 (venv 하나로)
- [ ] v1 코드 아카이브 처리
```

### 1.2 데이터베이스 통합
```bash
# DB 위치 표준화
- [ ] 표준 DB 위치: ragtrace-lite-v2/data/ragtrace.db
- [ ] 나머지 DB 파일 제거
- [ ] config.yaml에서 DB 경로 통일
```

### 1.3 테스트 파일 정리
```bash
# 테스트 구조화
- [ ] 루트의 test_*.py 파일들을 tests/ 폴더로 이동
- [ ] 테스트 카테고리별 서브폴더 생성:
    - tests/unit/
    - tests/integration/
    - tests/e2e/
```

---

## 🔧 Phase 2: 구조 개선 (3-4일)

### 2.1 대시보드 통합
```python
# 단일 대시보드 구현
- [ ] start_dashboard.py를 메인으로 선택
- [ ] 나머지 대시보드 파일 제거
- [ ] CLI 명령 통합: ragtrace-lite dashboard
```

### 2.2 임베딩 어댑터 정리
```python
# 어댑터 마이그레이션 완료
- [ ] embeddings_adapter.py 제거
- [ ] embeddings_adapter_v2.py → embeddings_adapter.py 리네임
- [ ] 모든 import 경로 업데이트
```

### 2.3 대형 파일 분할
```python
# 500줄 이상 파일 리팩토링
- [ ] db/manager.py 분할:
    - db/connection.py
    - db/queries.py
    - db/migrations.py
    
- [ ] report/generator.py 분할:
    - report/html_generator.py
    - report/markdown_generator.py
    - report/base_generator.py
```

---

## 🏗️ Phase 3: 아키텍처 개선 (5-7일)

### 3.1 Provider 패턴 완성
```python
# Provider 아키텍처 표준화
- [ ] 모든 LLM provider가 base.LLMProvider 상속
- [ ] 모든 Embedding provider가 base.EmbeddingProvider 상속
- [ ] Factory 패턴으로 provider 생성 통일
```

### 3.2 설정 관리 개선
```yaml
# 계층적 설정 구조
- [ ] config/
    - base.yaml (공통 설정)
    - development.yaml (개발 환경)
    - production.yaml (운영 환경)
    - test.yaml (테스트 환경)
```

### 3.3 의존성 주입 구현
```python
# DI 컨테이너 도입
- [ ] core/container.py 생성
- [ ] 서비스 레지스트리 구현
- [ ] 순환 의존성 제거
```

---

## 📦 Phase 4: 패키징 및 배포 준비 (2-3일)

### 4.1 패키지 메타데이터 정리
```toml
# pyproject.toml 통합
- [ ] 버전 2.0.0으로 통일
- [ ] 의존성 정리 (중복 제거)
- [ ] 선택적 의존성 그룹화 (llm, dev, test)
```

### 4.2 CI/CD 파이프라인
```yaml
# GitHub Actions 설정
- [ ] .github/workflows/test.yml
- [ ] .github/workflows/lint.yml
- [ ] .github/workflows/release.yml
```

### 4.3 문서화
```markdown
# 문서 정리
- [ ] README.md 업데이트
- [ ] CHANGELOG.md 생성
- [ ] API 문서 생성 (Sphinx)
- [ ] 마이그레이션 가이드 작성
```

---

## 📊 예상 결과

### 저장 공간
- **현재:** ~10GB
- **목표:** ~5GB (50% 절감)

### 코드 품질
- **테스트 커버리지:** 42% → 80%
- **코드 중복:** 30% → 5%
- **평균 파일 크기:** 300줄 이하

### 유지보수성
- **순환 복잡도:** 감소
- **결합도:** 낮음
- **응집도:** 높음

---

## 🚀 실행 우선순위

1. **즉시 실행 (오늘)**
   - BGE-M3 모델 중복 제거
   - 데이터베이스 통합
   - 테스트 파일 정리

2. **단기 (이번 주)**
   - 대시보드 통합
   - 임베딩 어댑터 정리
   - 대형 파일 분할

3. **중기 (다음 주)**
   - Provider 패턴 완성
   - 설정 관리 개선
   - DI 구현

4. **장기 (2주 후)**
   - 패키징 최적화
   - CI/CD 구축
   - 문서화 완성

---

## ⚠️ 리스크 관리

### 주요 리스크
1. **데이터 손실:** DB 통합 시 백업 필수
2. **기능 파손:** 단계별 테스트 필수
3. **호환성 문제:** v1 사용자 마이그레이션 가이드 필요

### 완화 전략
- 모든 변경사항 git 브랜치에서 작업
- 단계별 PR 및 리뷰
- 롤백 계획 수립

---

## 📈 성공 지표

- [ ] 저장 공간 50% 절감
- [ ] 테스트 커버리지 80% 달성
- [ ] 0 중복 코드
- [ ] 모든 파일 500줄 이하
- [ ] CI/CD 파이프라인 구축
- [ ] 완전한 문서화

---

## 🎯 최종 목표

**"깨끗하고, 확장 가능하며, 유지보수가 쉬운 RAGTrace Lite v2"**

- 명확한 아키텍처
- 표준화된 패턴
- 완벽한 테스트
- 우수한 문서화
- 쉬운 배포