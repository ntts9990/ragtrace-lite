#!/usr/bin/env python3
"""
간단한 RAGAS 평가 테스트
"""
import os
import sys
import pandas as pd
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ragtrace_lite.config_loader import load_config
from ragtrace_lite.llm_factory import create_llm
from ragtrace_lite.evaluator import RagasEvaluator
from datasets import Dataset


def test_simple_evaluation():
    """간단한 평가 테스트"""
    print("=" * 80)
    print("🧪 간단한 RAGAS 평가 테스트")
    print("=" * 80)
    
    # 설정 로드
    config = load_config()
    llm = create_llm(config)
    print(f"✅ LLM 로드: {type(llm).__name__}")
    
    # 테스트 데이터 (더 복잡한 예제)
    test_data = {
        'question': [
            '한국의 수도는 어디인가요?',
            'Python에서 리스트와 튜플의 차이점은 무엇인가요?'
        ],
        'answer': [
            '한국의 수도는 서울입니다. 서울은 약 950만 명의 인구가 거주하는 대한민국 최대의 도시입니다. 서울은 조선시대부터 현재까지 600년 이상 한국의 수도 역할을 해왔습니다.',
            '리스트는 가변(mutable) 객체로 요소를 추가, 삭제, 수정할 수 있지만, 튜플은 불변(immutable) 객체로 한 번 생성되면 변경할 수 없습니다. 리스트는 대괄호 []를 사용하고, 튜플은 소괄호 ()를 사용합니다.'
        ],
        'contexts': [
            [
                '서울특별시는 대한민국의 수도이자 최대 도시로, 정치, 경제, 문화의 중심지입니다.',
                '서울의 인구는 약 950만 명으로 전체 인구의 약 18%가 거주합니다.',
                '서울은 1394년 조선의 수도로 정해진 이후 현재까지 한국의 수도입니다.'
            ],
            [
                'Python의 리스트는 대괄호 []를 사용하며, 동적으로 크기가 변할 수 있습니다.',
                '튜플은 소괄호 ()를 사용하며, 메모리 효율적이고 해시 가능합니다.',
                '리스트는 append(), remove() 등의 메서드로 수정 가능하지만, 튜플은 수정할 수 없습니다.'
            ]
        ],
        'ground_truths': [
            ['한국의 수도는 서울이다.'],
            ['리스트는 변경 가능하고 튜플은 변경 불가능하다.']
        ]
    }
    
    dataset = Dataset.from_dict(test_data)
    print(f"✅ 데이터셋 생성: {len(dataset)}개 항목\n")
    
    # 평가자 생성 및 평가 실행
    evaluator = RagasEvaluator(config, llm=llm)
    
    print("📊 RAGAS 평가 실행...")
    results_df = evaluator.evaluate(dataset)
    
    print("\n" + "="*60)
    print("📈 평가 결과")
    print("="*60)
    
    # 결과 확인
    if isinstance(results_df, pd.DataFrame):
        print(f"✅ 결과 DataFrame 크기: {results_df.shape}")
        print(f"✅ 컬럼: {list(results_df.columns)}")
        
        # 점수 출력
        metric_cols = [col for col in results_df.columns 
                      if col not in ['user_input', 'retrieved_contexts', 'response', 'reference', 
                                     'question', 'answer', 'contexts', 'ground_truths']]
        
        print("\n📊 메트릭별 점수:")
        for metric in metric_cols:
            if metric in results_df.columns:
                scores = pd.to_numeric(results_df[metric], errors='coerce')
                valid_scores = scores.dropna()
                if len(valid_scores) > 0:
                    print(f"  - {metric}: {valid_scores.mean():.3f} (±{valid_scores.std():.3f})")
                    for i, score in enumerate(scores):
                        if pd.notna(score):
                            print(f"    • 항목 {i+1}: {score:.3f}")
                        else:
                            print(f"    • 항목 {i+1}: NaN")
                else:
                    print(f"  - {metric}: 모든 점수가 NaN")
        
        # 상세 결과 저장
        output_path = "test_results_detail.csv"
        results_df.to_csv(output_path, index=False)
        print(f"\n✅ 상세 결과 저장: {output_path}")
        
    else:
        print(f"❌ 예상치 못한 결과 타입: {type(results_df)}")
    
    print("\n" + "="*80)
    print("✅ 테스트 완료")
    print("="*80)


if __name__ == "__main__":
    # 테스트 실행
    test_simple_evaluation()