#!/bin/bash
# RAGTrace Lite 테스트 실행 스크립트

echo "=== RAGTrace Lite 테스트 시작 ==="
echo ""

# 1. 환경변수 설정 확인
if [ -z "$CLOVA_STUDIO_API_KEY" ]; then
    echo "⚠️  CLOVA_STUDIO_API_KEY가 설정되지 않았습니다."
    echo "   .env 파일을 수정하거나 다음 명령을 실행하세요:"
    echo "   export CLOVA_STUDIO_API_KEY='your_api_key'"
    exit 1
fi

# 2. 디렉토리 생성
echo "📁 필요한 디렉토리 생성 중..."
mkdir -p logs
mkdir -p reports

# 3. 평가 실행
echo ""
echo "🚀 RAG 평가 실행 중..."
echo "   데이터: data/test_rag_data.json"
echo "   설정: config.yaml"
echo ""

ragtrace-lite evaluate data/test_rag_data.json \
    --config config.yaml \
    --output-dir reports \
    --llm hcx \
    --embedding huggingface

# 4. 대시보드 생성
echo ""
echo "📊 웹 대시보드 생성 중..."
ragtrace-lite dashboard

echo ""
echo "=== 테스트 완료 ==="
echo "결과 확인:"
echo "  - 데이터베이스: evaluation_results.db"
echo "  - 리포트: reports/ 디렉토리"
echo "  - 로그: logs/evaluation.log"
echo "  - 대시보드: reports/dashboard.html"