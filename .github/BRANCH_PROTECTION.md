# GitHub 브랜치 보호 규칙 설정 가이드

## 설정 방법

GitHub 저장소 → Settings → Branches에서 다음 규칙을 설정하세요.

## Main 브랜치 보호 규칙

### 1. Branch protection rule for `main`
- **Branch name pattern**: `main`
- **Protect matching branches**: ✅

### 2. 필수 설정
- ✅ **Require a pull request before merging**
  - ✅ Require approvals: 1
  - ✅ Dismiss stale reviews when new commits are pushed
  - ✅ Require review from code owners

- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - Status checks (CI/CD 설정 후 추가):
    - `ci/tests`
    - `ci/lint`
    - `ci/type-check`

- ✅ **Require conversation resolution before merging**
- ✅ **Require signed commits**
- ✅ **Require linear history**
- ✅ **Include administrators**

### 3. 추가 제한사항
- ✅ **Allow force pushes**: ❌ (비활성화)
- ✅ **Allow deletions**: ❌ (비활성화)

## Develop 브랜치 보호 규칙

### 1. Branch protection rule for `develop`
- **Branch name pattern**: `develop`
- **Protect matching branches**: ✅

### 2. 필수 설정
- ✅ **Require a pull request before merging**
  - ✅ Require approvals: 1
  - ✅ Dismiss stale reviews when new commits are pushed

- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging

- ✅ **Require conversation resolution before merging**

### 3. 유연한 설정
- ⚠️ **Include administrators**: ❌ (개발 편의성)
- ⚠️ **Require signed commits**: ❌ (선택사항)

## 자동화 워크플로우 (옵션)

### GitHub Actions 설정
`.github/workflows/ci.yml` 파일 생성:

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install uv
      run: pip install uv
    
    - name: Install dependencies
      run: uv sync --dev
    
    - name: Run tests
      run: uv run pytest --cov=ragtrace_lite
    
    - name: Lint
      run: |
        uv run black --check src/ tests/
        uv run isort --check-only src/ tests/
        uv run flake8 src/ tests/
    
    - name: Type check
      run: uv run mypy src/
```

## 권장 사항

### 1. 코드 리뷰 가이드라인
- 기능적 정확성 확인
- 코드 스타일 및 컨벤션 준수
- 테스트 커버리지 확인
- 문서 업데이트 확인
- 성능 및 보안 고려사항 검토

### 2. PR 템플릿
`.github/pull_request_template.md` 생성:

```markdown
## 변경 사항
- [ ] 기능 추가
- [ ] 버그 수정
- [ ] 문서 업데이트
- [ ] 테스트 추가
- [ ] 리팩토링

## 설명
<!-- 무엇을 왜 변경했는지 설명 -->

## 테스트
- [ ] 유닛 테스트 통과
- [ ] 통합 테스트 통과
- [ ] 수동 테스트 완료

## 체크리스트
- [ ] 코드 스타일 준수
- [ ] 문서 업데이트
- [ ] 호환성 확인
- [ ] 리뷰 요청
```

### 3. Issue 템플릿
`.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
---
name: Bug Report
about: 버그 리포트
title: '[BUG] '
labels: bug
assignees: ''
---

## 버그 설명
<!-- 버그에 대한 명확하고 간결한 설명 -->

## 재현 방법
1. '...' 으로 이동
2. '...' 클릭
3. '...' 스크롤
4. 오류 확인

## 예상 동작
<!-- 예상했던 동작 설명 -->

## 실제 동작
<!-- 실제로 일어난 일 설명 -->

## 환경
- OS: [e.g. Windows 10, macOS 12, Ubuntu 20.04]
- Python: [e.g. 3.9.7]
- RAGTrace Lite: [e.g. 1.0.0]

## 추가 정보
<!-- 스크린샷, 로그 등 -->
```

이제 완전한 브랜치 구조와 개발 워크플로우가 설정되었습니다!