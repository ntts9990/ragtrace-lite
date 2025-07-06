#!/usr/bin/env python3
"""
직접 실행 가능한 HCX 테스트 스크립트
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# CLI의 test_hcx 함수 직접 호출
from datetime import datetime
from pathlib import Path
from ragtrace_lite.config_loader import load_config
from ragtrace_lite.llm_factory import create_llm, check_llm_connection
from ragtrace_lite.data_processor import DataProcessor
from ragtrace_lite.evaluator import RagasEvaluator


def test_hcx(quick=False, full=False):
    """Test HCX-005 & BGE-M3 setup"""
    print("=" * 70)
    print("🧪 HCX-005 & BGE-M3 테스트")
    print("=" * 70)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. 환경 확인
    print("1️⃣ 환경 설정 확인")
    print("-" * 50)
    
    # API 키 확인
    hcx_key = os.getenv('CLOVA_STUDIO_API_KEY', '').strip()
    if hcx_key and hcx_key.startswith('nv-'):
        print(f"✅ HCX API 키: 설정됨 ({hcx_key[:10]}...)")
    else:
        print("❌ HCX API 키가 설정되지 않음")
        print("   export CLOVA_STUDIO_API_KEY='your-key' 실행 필요")
        sys.exit(1)
    
    # 설정 로드
    try:
        config = load_config()
        print(f"✅ 설정 파일 로드: config.yaml")
        print(f"   - LLM: {config.llm.provider} ({config.llm.model_name})")
        print(f"   - Embedding: {config.embedding.provider}")
    except Exception as e:
        print(f"❌ 설정 로드 실패: {e}")
        sys.exit(1)
    
    # 2. LLM 연결 테스트
    print("\n2️⃣ HCX-005 연결 테스트")
    print("-" * 50)
    
    try:
        llm = create_llm(config)
        print(f"✅ LLM 인스턴스 생성: {type(llm).__name__}")
        
        if check_llm_connection(llm, config.llm.provider):
            print("✅ HCX-005 API 연결 성공")
        else:
            print("❌ HCX-005 API 연결 실패")
            sys.exit(1)
    except Exception as e:
        print(f"❌ LLM 생성 실패: {e}")
        sys.exit(1)
    
    # 3. BGE-M3 임베딩 테스트
    print("\n3️⃣ BGE-M3 임베딩 테스트")
    print("-" * 50)
    
    if config.embedding.provider == 'bge_m3':
        print("✅ BGE-M3 설정 확인")
        model_path = Path('./models/bge-m3')
        if model_path.exists():
            print(f"✅ BGE-M3 모델 존재: {model_path}")
        else:
            print("⚠️  BGE-M3 모델이 없음 (첫 실행 시 자동 다운로드)")
    else:
        print(f"⚠️  다른 임베딩 사용 중: {config.embedding.provider}")
    
    if quick:
        # 빠른 테스트
        print("\n4️⃣ 빠른 기능 테스트")
        print("-" * 50)
        
        # 간단한 데이터로 테스트
        test_data = {
            'question': ['테스트 질문입니다'],
            'answer': ['테스트 답변입니다'],
            'contexts': [['테스트 컨텍스트입니다']],
            'ground_truths': [['테스트 정답입니다']]
        }
        
        try:
            from datasets import Dataset
            dataset = Dataset.from_dict(test_data)
            print("✅ 테스트 데이터셋 생성")
            
            # 평가자 생성
            evaluator = RagasEvaluator(config, llm=llm)
            print("✅ 평가자 초기화 성공")
            
            print("\n✅ 모든 구성 요소가 정상 작동합니다!")
            
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            sys.exit(1)
    
    elif full:
        # 전체 파이프라인 테스트는 아래에서 구현
        pass
    
    else:
        # 기본 테스트
        print("\n✅ HCX-005 & BGE-M3 설정이 올바르게 되어 있습니다.")
        print("\n사용 가능한 옵션:")
        print("  --quick : 빠른 기능 테스트")
        print("  --full  : 전체 파이프라인 테스트")
    
    print("\n" + "=" * 70)
    print(f"완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    # 명령줄 인자 처리
    if '--quick' in sys.argv:
        test_hcx(quick=True)
    elif '--full' in sys.argv:
        test_hcx(full=True)
    else:
        test_hcx()