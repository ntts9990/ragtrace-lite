#!/usr/bin/env python3
"""
상세한 RAGAS 평가 테스트
각 메트릭별로 상세 로그 출력
"""
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ragtrace_lite.config_loader import load_config
from ragtrace_lite.llm_factory import create_llm
from ragtrace_lite.evaluator import RagasEvaluator
from datasets import Dataset


def test_detailed_evaluation():
    """각 메트릭별 상세 테스트"""
    print("=" * 80)
    print("🔍 상세 RAGAS 평가 테스트")
    print("=" * 80)
    
    # 설정 로드
    config = load_config()
    print(f"✅ 설정 로드: {config.llm.provider}")
    
    # LLM 생성
    llm = create_llm(config)
    print(f"✅ LLM 생성: {type(llm).__name__}")
    
    # 테스트 데이터
    test_data = {
        'question': ['한국의 수도는 어디인가요?'],
        'answer': ['한국의 수도는 서울입니다. 서울은 약 950만 명의 인구가 거주하는 대한민국 최대의 도시입니다.'],
        'contexts': [['서울특별시는 대한민국의 수도이자 최대 도시로, 정치, 경제, 문화의 중심지입니다.']],
        'ground_truths': [['한국의 수도는 서울이다.']]
    }
    
    dataset = Dataset.from_dict(test_data)
    print(f"✅ 데이터셋 생성: {len(dataset)}개 항목\n")
    
    # 각 메트릭별로 개별 테스트
    metrics_to_test = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']
    
    for metric_name in metrics_to_test:
        print(f"\n{'='*60}")
        print(f"📊 {metric_name} 메트릭 테스트")
        print(f"{'='*60}")
        
        try:
            # 단일 메트릭으로 평가자 생성
            evaluator = RagasEvaluator(config, llm=llm, metrics=[metric_name])
            
            # 평가 실행
            print(f"⏳ {metric_name} 평가 시작...")
            start_time = datetime.now()
            
            results_df = evaluator.evaluate(dataset)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"✅ {metric_name} 평가 완료 ({elapsed:.1f}초)")
            
            # 결과 확인
            if metric_name in results_df.columns:
                score = results_df[metric_name].iloc[0]
                print(f"📈 {metric_name} 점수: {score}")
                
                # NaN 체크
                import pandas as pd
                if pd.isna(score):
                    print(f"⚠️  {metric_name} 점수가 NaN입니다!")
                else:
                    print(f"✅ {metric_name} 점수 계산 성공: {score:.3f}")
            else:
                print(f"❌ {metric_name} 컬럼이 결과에 없습니다!")
                print(f"   사용 가능한 컬럼: {list(results_df.columns)}")
                
        except Exception as e:
            print(f"❌ {metric_name} 평가 실패: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("✅ 상세 테스트 완료")
    print("="*80)


if __name__ == "__main__":
    # API 키 설정
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    
    # 상세 테스트 실행
    test_detailed_evaluation()