# RAGTrace Lite v2.0

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey)](https://github.com/your-org/ragtrace-lite)

경량 RAG (Retrieval-Augmented Generation) 평가 프레임워크

## 🎯 주요 특징

- ✅ **단일 Excel 파일**: 데이터와 환경 조건을 하나의 파일로 관리
- ✅ **동적 환경 관리**: `env_` 접두어로 무제한 조건 추가
- ✅ **통계적 비교**: 기간별 A/B 테스트 with 통계적 유의성 검정
- ✅ **크로스 플랫폼**: Windows/macOS/Linux 완벽 호환
- ✅ **EAV 패턴**: SQLite 기반 유연한 데이터 저장

## 🚀 빠른 시작

### 설치

```bash
# Windows
install.bat

# macOS/Linux
./install.sh

# 또는 pip
pip install -e .
```

### 사용법

```bash
# 템플릿 생성
ragtrace create-template

# 평가 실행
ragtrace evaluate --excel data.xlsx --name "Test v1"

# 기간 비교
ragtrace compare-windows \
  --a-start 2024-12-01 --a-end 2024-12-07 \
  --b-start 2024-12-08 --b-end 2024-12-14 \
  --metric ragas_score

# 환경 키 목록
ragtrace list-env
```

## 📊 Excel 형식

| question | answer | contexts | ground_truth | env_sys_prompt_version | env_es_nodes | env_quantized | ... |
|----------|--------|----------|--------------|----------------------|--------------|---------------|-----|
| 질문1 | 답변1 | 컨텍스트1 | 정답1 | v2.0 | 3 | false | ... |
| 질문2 | 답변2 | 컨텍스트2 | 정답2 | | | | |

## 📋 환경 조건 (env_ 컬럼)

### 권장 조건
- `env_sys_prompt_version`: 시스템 프롬프트 버전
- `env_es_nodes`: Elasticsearch 노드 수
- `env_quantized`: 양자화 여부
- `env_embedding_model`: 임베딩 모델
- `env_intent_analysis`: 의도 분석 여부

### 커스텀 조건
`env_` 접두어를 사용하여 자유롭게 추가:
- `env_custom_param1`
- `env_my_feature_flag`
- ...

## 📈 통계 분석

### 윈도우 비교
- Welch's t-test (기본)
- Cohen's d (효과 크기)
- Bootstrap 신뢰구간
- 중첩 기간 허용

### 시계열 분석
- 이동 평균
- 트렌드 분석
- 그룹별 비교

## 🔧 개발

```bash
# 테스트
pytest tests/

# 포맷팅
black src/
isort src/

# 타입 체크
mypy src/
```

## 📚 문서

- [개발 가이드](docs/DEVELOPMENT.md)
- [API 문서](docs/API.md)
- [Windows 호환성](docs/WINDOWS.md)

## 📄 라이선스

MIT License - 자유롭게 사용/수정/배포 가능

## 🤝 기여

1. Fork & Clone
2. 브랜치 생성
3. 변경사항 커밋
4. PR 생성

## 📧 문의

- Issues: https://github.com/your-org/ragtrace-lite/issues
- Email: ragtrace@example.com