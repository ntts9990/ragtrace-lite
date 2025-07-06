# RAGTrace Lite 테스트 가이드

이 디렉토리는 RAGTrace Lite의 기본 기능을 테스트하기 위한 예제입니다.

## 🚀 빠른 시작

### 1. API 키 설정
`.env` 파일을 열어 HCX API 키를 입력하세요:
```bash
CLOVA_STUDIO_API_KEY=your_actual_api_key_here
```

### 2. 테스트 실행

**Linux/Mac:**
```bash
cd test_evaluation
source .env  # 환경변수 로드
./run_test.sh
```

**Windows:**
```batch
cd test_evaluation
# .env 파일의 키를 환경변수로 설정
set CLOVA_STUDIO_API_KEY=your_actual_api_key_here
run_test.bat
```

또는 직접 명령어 실행:
```bash
# 환경변수 설정
export CLOVA_STUDIO_API_KEY="your_api_key"  # Linux/Mac
set CLOVA_STUDIO_API_KEY=your_api_key       # Windows

# 평가 실행
ragtrace-lite evaluate data/test_rag_data.json --config config.yaml

# 대시보드 생성
ragtrace-lite dashboard --open
```

## 📁 디렉토리 구조

```
test_evaluation/
├── data/
│   └── test_rag_data.json    # 테스트용 RAG 데이터
├── config.yaml               # 설정 파일
├── .env                      # API 키 설정
├── run_test.sh              # Linux/Mac 실행 스크립트
├── run_test.bat             # Windows 실행 스크립트
└── README.md                # 이 파일
```

## 🔧 설정 설명

### config.yaml
- **LLM**: HCX-005 (CLOVA Studio) 사용
- **임베딩**: BGE-M3 (로컬 실행, GPU 자동 감지)
- **메트릭**: 5가지 RAGAS 메트릭 모두 평가
- **출력**: JSON 형식, HTML 대시보드 생성

### test_rag_data.json
3개의 한국어 질문-답변 쌍:
1. 한국의 수도에 대한 질문
2. 인공지능의 정의
3. RAG의 의미

## 📊 결과 확인

테스트 완료 후 다음 위치에서 결과를 확인할 수 있습니다:

- **데이터베이스**: `evaluation_results.db`
- **로그**: `logs/evaluation.log`
- **리포트**: `reports/` 디렉토리
- **대시보드**: `reports/dashboard.html` (브라우저에서 열기)

## ⚠️ 주의사항

1. HCX API 키가 유효해야 합니다
2. 인터넷 연결이 필요합니다 (HCX API 호출)
3. 첫 실행 시 BGE-M3 모델을 다운로드합니다 (약 2GB)
4. GPU가 있으면 자동으로 사용됩니다

## 🆘 문제 해결

### "API 키가 설정되지 않았습니다" 오류
- `.env` 파일에 올바른 API 키를 입력했는지 확인
- 환경변수가 제대로 설정되었는지 확인

### "모델을 찾을 수 없습니다" 오류
- 인터넷 연결 확인
- HuggingFace에서 모델 다운로드가 차단되지 않았는지 확인

### 메모리 부족 오류
- `config.yaml`의 `batch_size`를 줄여보세요
- CPU 사용 시 `device: cpu`로 명시적 설정