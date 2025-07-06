# 개발 가이드 - RAGTrace Lite

## 🌳 브랜치 구조

### 메인 브랜치
- **`main`**: 안정화된 프로덕션 코드
  - 릴리즈 준비 완료된 코드만 포함
  - 직접 커밋 금지, PR을 통해서만 병합
  - 자동 배포 및 릴리즈 태그 생성

- **`develop`**: 개발 통합 브랜치
  - 새로운 기능들이 통합되는 브랜치
  - 다음 릴리즈를 위한 기능들이 모이는 곳
  - feature 브랜치들이 병합되는 대상

### 작업 브랜치
- **`feature/enhancement`**: 새로운 기능 개발
  - `develop`에서 분기
  - 기능 완성 후 `develop`으로 PR

- **`hotfix/production`**: 긴급 버그 수정
  - `main`에서 분기
  - 수정 후 `main`과 `develop` 양쪽에 병합

## 🚀 개발 워크플로우

### 1. 새로운 기능 개발
```bash
# develop 브랜치에서 시작
git checkout develop
git pull origin develop

# feature 브랜치에서 작업
git checkout feature/enhancement
git pull origin feature/enhancement

# 개발 및 커밋
git add .
git commit -m "feat: Add new evaluation metric"
git push origin feature/enhancement

# GitHub에서 develop으로 PR 생성
```

### 2. 긴급 버그 수정
```bash
# main 브랜치에서 시작
git checkout main
git pull origin main

# hotfix 브랜치에서 작업
git checkout hotfix/production
git pull origin hotfix/production

# 수정 및 커밋
git add .
git commit -m "fix: Critical API connection bug"
git push origin hotfix/production

# GitHub에서 main으로 PR 생성 후 develop에도 백포트
```

## 📝 커밋 메시지 규칙

### 커밋 타입
- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅 (로직 변경 없음)
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드 설정, 의존성 업데이트

### 예시
```
feat: Add BGE-M3 embedding support with auto download
fix: Resolve HCX rate limiting issues with exponential backoff
docs: Update cross-platform installation guide
test: Add integration tests for web dashboard
refactor: Simplify config loading with Pydantic v2
```

## 🧪 테스트 가이드

### 로컬 테스트 실행
```bash
# 전체 테스트 실행
uv run pytest

# 커버리지 포함
uv run pytest --cov=ragtrace_lite

# 샘플 데이터로 평가 테스트
uv run python -m ragtrace_lite.cli evaluate data/sample_data.json --llm hcx

# 웹 대시보드 테스트
uv run python -m ragtrace_lite.cli dashboard --open
```

## 🔧 개발 환경 설정

### 1. 저장소 클론 및 환경 설정
```bash
git clone https://github.com/ntts9990/ragtrace-lite.git
cd ragtrace-lite
uv sync --dev
```

### 2. API 키 설정
```bash
cp .env.example .env
# .env 파일에 API 키 입력
```

### 3. 브랜치 전환 및 개발
```bash
# 기능 개발
git checkout feature/enhancement

# 버그 수정
git checkout hotfix/production

# 안정 버전으로 돌아가기
git checkout main
```

## 📦 현재 브랜치 상태

- ✅ **main**: 프로덕션 안정 버전 (v1.0.4)
- ✅ **develop**: 개발 통합 브랜치
- ✅ **feature/enhancement**: 새 기능 개발용
- ✅ **hotfix/production**: 긴급 수정용

## 🤝 기여 방법

1. 적절한 브랜치에서 작업 브랜치 생성
2. 개발 및 테스트
3. PR 생성 및 리뷰 요청
4. 승인 후 병합

## 📞 문의

- GitHub Issues: 버그 리포트, 기능 요청
- GitHub Discussions: 일반적인 질문, 아이디어 공유