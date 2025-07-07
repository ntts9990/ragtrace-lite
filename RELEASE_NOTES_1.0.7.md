# Release Notes for v1.0.7

## 완료된 작업

### 1. 오픈소스 공개 준비
- `.gitignore` 업데이트: 개발 테스트 파일들 제외
- 불필요한 파일들을 git에서 제외하도록 설정

### 2. 윈도우 호환성 문제 수정
- `main.py:153`: `results_df.empty` → `len(results_df) == 0`
- pandas DataFrame의 ambiguous truth value 에러 해결

### 3. 문서 업데이트
- `CHANGELOG.md`: v1.0.7 엔트리 추가 및 날짜 수정
  - 모든 과거 버전 날짜를 2025-07-07로 통일
  - v1.0.7은 2025-07-08로 설정
- `DEVELOPMENT_GUIDE.md`: 개발자 가이드 신규 작성

### 4. 버전 업데이트
- `__init__.py`: 1.0.6 → 1.0.7
- `pyproject.toml`: 1.0.6 → 1.0.7

## PyPI 업로드 명령어

### TestPyPI 업로드 (테스트용)
```bash
# 1. 빌드 아티팩트 정리
rm -rf dist/ build/ *.egg-info/

# 2. 패키지 빌드
python -m pip install --upgrade build
python -m build

# 3. TestPyPI 업로드
python -m pip install --upgrade twine
python -m twine upload --repository testpypi dist/*

# 4. TestPyPI에서 설치 테스트
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ragtrace-lite==1.0.7
```

### PyPI 정식 업로드
```bash
# TestPyPI 테스트 완료 후 실행
python -m twine upload dist/*

# 설치 확인
pip install --upgrade ragtrace-lite==1.0.7
```

## 주요 변경사항 요약

1. **버그 수정**: 윈도우 환경에서 발생하는 pandas 에러 해결
2. **문서 개선**: 개발자를 위한 상세한 가이드 추가
3. **프로젝트 정리**: 오픈소스 배포를 위한 파일 구조 개선

## 참고사항

- README.md의 PyPI 배지는 자동으로 최신 버전을 표시하므로 별도 수정 불필요
- 개발 테스트 파일들은 `.gitignore`에 추가되어 배포에서 제외됨
- 폐쇄망 환경 지원 및 LLM/임베딩 모델 교체 가이드 포함