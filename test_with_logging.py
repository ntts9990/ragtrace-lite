#!/usr/bin/env python3
"""
로깅을 활성화한 RAGAS 평가 테스트
"""
import os
import sys
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ragtrace_lite.config_loader import load_config
from ragtrace_lite.llm_factory import create_llm
from ragtrace_lite.evaluator import RagasEvaluator
from datasets import Dataset


def test_with_logging():
    """로깅을 활성화한 테스트"""
    print("=" * 80)
    print("🔍 로깅을 활성화한 RAGAS 평가 테스트")
    print("=" * 80)
    
    # 설정 로드
    config = load_config()
    llm = create_llm(config)
    
    # 간단한 테스트 데이터
    test_data = {
        'question': ['한국의 수도는 어디인가요?'],
        'answer': ['한국의 수도는 서울입니다.'],
        'contexts': [['서울특별시는 대한민국의 수도입니다.']],
        'ground_truths': [['한국의 수도는 서울이다.']]
    }
    
    dataset = Dataset.from_dict(test_data)
    print(f"✅ 데이터셋 생성: {len(dataset)}개 항목\n")
    
    # 평가자 생성 및 평가 실행
    evaluator = RagasEvaluator(config, llm=llm)
    
    print("📊 RAGAS 평가 실행...")
    results_df = evaluator.evaluate(dataset)
    
    print("\n📈 평가 결과:")
    print(results_df)
    
    print("\n✅ 테스트 완료")


if __name__ == "__main__":
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    test_with_logging()