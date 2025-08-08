"""테스트 데이터 생성 스크립트"""

import pandas as pd
from pathlib import Path
import json

def create_test_excel():
    """실제 테스트용 Excel 파일 생성"""
    
    # RAG 평가용 샘플 데이터
    data = {
        'question': [
            'RAG란 무엇인가요?',
            'LLM의 한계점은 무엇인가요?',
            'Vector Database의 역할은?',
            'Fine-tuning과 RAG의 차이점은?',
            'Embedding이란 무엇인가요?',
            'Prompt Engineering의 중요성은?',
            'Hallucination을 줄이는 방법은?',
            'Context window란 무엇인가요?',
            'Semantic search의 원리는?',
            'Chain of Thought란?'
        ],
        'answer': [
            'RAG(Retrieval-Augmented Generation)는 검색과 생성을 결합한 AI 기술로, 외부 지식을 참조하여 더 정확한 답변을 생성합니다.',
            'LLM의 주요 한계점은 학습 데이터 시점 이후 정보 부재, 환각 현상, 높은 컴퓨팅 비용 등이 있습니다.',
            'Vector Database는 고차원 벡터 데이터를 효율적으로 저장하고 유사도 검색을 빠르게 수행하는 역할을 합니다.',
            'Fine-tuning은 모델 자체를 재학습시키는 것이고, RAG는 외부 지식을 검색하여 활용하는 방식입니다.',
            'Embedding은 텍스트나 이미지 등을 고정된 크기의 벡터로 변환하여 의미를 수치화한 표현입니다.',
            'Prompt Engineering은 LLM에서 원하는 결과를 얻기 위해 입력을 최적화하는 과정으로 매우 중요합니다.',
            'Hallucination을 줄이기 위해 RAG 사용, 프롬프트 개선, 온도 파라미터 조정 등의 방법이 있습니다.',
            'Context window는 모델이 한 번에 처리할 수 있는 최대 토큰 수를 의미합니다.',
            'Semantic search는 단순 키워드가 아닌 의미적 유사성을 기반으로 검색하는 기술입니다.',
            'Chain of Thought는 복잡한 문제를 단계별로 풀어가는 추론 방식입니다.'
        ],
        'contexts': [
            'RAG는 2020년 Facebook AI Research에서 처음 제안되었습니다. 검색 시스템과 언어 모델을 결합하여 지식 기반 질의응답을 개선합니다.',
            'LLM은 대규모 언어 모델로 수십억 개의 파라미터를 가집니다. 하지만 실시간 정보 부족과 환각 현상이 주요 문제입니다.',
            'Pinecone, Weaviate, Milvus 등이 대표적인 Vector Database입니다. 코사인 유사도나 유클리드 거리로 검색합니다.',
            'Fine-tuning은 특정 도메인에 특화시키는 방법입니다. RAG는 외부 문서를 참조하여 답변의 정확도를 높입니다.',
            'Word2Vec, BERT, OpenAI Embeddings 등 다양한 임베딩 기법이 있습니다. 차원은 보통 768~1536입니다.',
            'Few-shot learning, Chain of Thought, System prompts 등이 프롬프트 엔지니어링 기법입니다.',
            'Temperature를 낮추고, Top-p를 조정하며, 검증 가능한 소스를 제공하면 환각을 줄일 수 있습니다.',
            'GPT-4는 8k~32k 토큰, Claude는 100k 토큰의 context window를 지원합니다.',
            'Semantic search는 BERT나 Sentence Transformers를 사용하여 의미적 유사도를 계산합니다.',
            'CoT prompting은 "Let\'s think step by step"과 같은 프롬프트로 단계적 추론을 유도합니다.'
        ],
        'ground_truth': [
            'RAG는 Retrieval-Augmented Generation의 약자로 검색 증강 생성 기술입니다.',
            'LLM의 한계는 최신 정보 부족, 환각, 높은 비용, 제한된 context window입니다.',
            'Vector DB는 임베딩 벡터를 저장하고 유사도 기반 검색을 제공합니다.',
            'Fine-tuning은 모델 수정, RAG는 외부 지식 활용이 핵심 차이입니다.',
            'Embedding은 데이터를 벡터 공간에 매핑하는 기술입니다.',
            'Prompt Engineering은 AI 시스템의 성능을 최대화하는 핵심 기술입니다.',
            'RAG, 낮은 temperature, 소스 제공이 hallucination 감소에 효과적입니다.',
            'Context window는 모델의 입력 길이 제한을 의미합니다.',
            'Semantic search는 의미 기반 검색으로 키워드 검색보다 우수합니다.',
            'Chain of Thought는 단계별 추론으로 복잡한 문제 해결을 돕습니다.'
        ],
        # 환경 조건 (첫 번째 행에만 값 설정)
        'env_sys_prompt_version': ['v2.0', '', '', '', '', '', '', '', '', ''],
        'env_es_nodes': [3, '', '', '', '', '', '', '', '', ''],
        'env_quantized': ['false', '', '', '', '', '', '', '', '', ''],
        'env_embedding_model': ['text-embedding-ada-002', '', '', '', '', '', '', '', '', ''],
        'env_retriever_top_k': [5, '', '', '', '', '', '', '', '', ''],
        'env_temperature': [0.1, '', '', '', '', '', '', '', '', ''],
        'env_test_batch': ['batch_001', '', '', '', '', '', '', '', '', '']
    }
    
    # DataFrame 생성
    df = pd.DataFrame(data)
    
    # Excel 파일 저장
    output_path = Path('test_evaluation_data.xlsx')
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Data', index=False)
        
        # 메타데이터 시트 추가
        metadata = pd.DataFrame({
            'Key': ['Created', 'Purpose', 'Items', 'Version'],
            'Value': [
                pd.Timestamp.now().isoformat(),
                'RAGTrace Lite v2 Test Data',
                len(df),
                '2.0'
            ]
        })
        metadata.to_excel(writer, sheet_name='Metadata', index=False)
    
    print(f"✅ Test Excel file created: {output_path}")
    print(f"   - {len(df)} test items")
    print(f"   - 7 environment conditions")
    print(f"   - Ready for evaluation")
    
    return output_path


def setup_env_file():
    """루트 폴더의 .env 파일에서 API 키 복사"""
    
    root_env = Path('/Users/isle/PycharmProjects/ragtrace-lite/.env')
    local_env = Path('.env')
    
    if root_env.exists():
        # 루트 .env 파일 읽기
        with open(root_env, 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        # 필요한 키만 추출
        lines = []
        for line in env_content.split('\n'):
            if any(key in line for key in ['CLOVA_STUDIO_API_KEY', 'GEMINI_API_KEY', 'OPENAI_API_KEY']):
                lines.append(line)
        
        # 추가 설정
        lines.extend([
            '',
            '# RAGTrace Lite v2 Settings',
            'LLM_PROVIDER=hcx',
            'DB_PATH=ragtrace.db',
            'LOG_LEVEL=INFO',
            'RATE_LIMIT_DELAY=2.0'
        ])
        
        # 로컬 .env 파일 생성
        with open(local_env, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ Environment file created: {local_env}")
        print("   - API keys copied from root folder")
        print("   - Default settings added")
    else:
        # .env.example 생성
        example_content = """# RAGTrace Lite v2 Configuration

# Required API Keys
CLOVA_STUDIO_API_KEY=your_hcx_key_here
GEMINI_API_KEY=your_gemini_key_here  # Optional

# Settings
LLM_PROVIDER=hcx
DB_PATH=ragtrace.db
LOG_LEVEL=INFO
RATE_LIMIT_DELAY=2.0
"""
        
        with open('.env.example', 'w', encoding='utf-8') as f:
            f.write(example_content)
        
        print("⚠️  Root .env not found")
        print(f"✅ Created .env.example")
        print("   Please add your API keys to .env file")


def create_batch_test_script():
    """배치 테스트 실행 스크립트 생성"""
    
    script_content = """#!/bin/bash
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
"""
    
    script_path = Path('run_test.sh')
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 실행 권한 부여
    script_path.chmod(0o755)
    
    print(f"✅ Test script created: {script_path}")
    print("   Run: ./run_test.sh")


def main():
    """메인 실행"""
    print("=" * 60)
    print("RAGTrace Lite v2 - Test Data Setup")
    print("=" * 60)
    print()
    
    # 1. 테스트 Excel 생성
    excel_path = create_test_excel()
    print()
    
    # 2. 환경 파일 설정
    setup_env_file()
    print()
    
    # 3. 배치 스크립트 생성
    create_batch_test_script()
    print()
    
    print("=" * 60)
    print("Setup completed! Next steps:")
    print("=" * 60)
    print("1. Check .env file for API keys")
    print("2. Run: ./run_test.sh")
    print("3. Or manually: ragtrace evaluate --excel test_evaluation_data.xlsx")


if __name__ == "__main__":
    main()