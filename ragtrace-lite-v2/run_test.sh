#!/bin/bash
# RAGTrace Lite v2 배치 테스트 스크립트

echo "🚀 Starting batch evaluation test..."
echo ""

# 환경 확인
if [ ! -f .env ]; then
    echo "❌ .env file not found"
    echo "Please create .env file with API keys"
    exit 1
fi

# 가상환경 활성화
if [ -d venv ]; then
    source venv/bin/activate
else
    echo "⚠️  Virtual environment not found"
    echo "Run ./install.sh first"
    exit 1
fi

# 테스트 데이터 생성
echo "📊 Creating test data..."
python create_test_data.py

# 평가 실행 (--yes 플래그로 자동 실행)
echo ""
echo "🔬 Running evaluation..."
ragtrace evaluate --excel test_evaluation_data.xlsx --name "Test Run" --yes

# 결과 확인
echo ""
echo "📈 Checking results..."
ragtrace history --limit 5

echo ""
echo "✅ Batch test completed!"
