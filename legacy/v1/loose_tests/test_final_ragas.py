#!/usr/bin/env python3
"""
최종 RAGAS 테스트
"""
import os
import sys
from datasets import Dataset
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ragtrace_lite.config_loader import load_config
from ragtrace_lite.llm_factory import create_llm
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall


def test_all_metrics():
    """모든 RAGAS 메트릭 테스트"""
    print("🎯 최종 RAGAS 메트릭 테스트")
    print("=" * 70)
    
    # 환경 설정
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    config = load_config()
    
    # 프록시가 적용된 LLM 생성
    print("\n1️⃣ 프록시 LLM 생성")
    llm = create_llm(config)
    print(f"✅ LLM 타입: {type(llm).__name__}")
    
    # 테스트 데이터
    test_data = {
        'question': [
            '한국의 수도는 어디인가요?',
            '파이썬은 어떤 언어인가요?'
        ],
        'answer': [
            '한국의 수도는 서울입니다. 서울은 600년 이상의 역사를 가진 도시입니다.',
            '파이썬은 간결하고 읽기 쉬운 프로그래밍 언어입니다. 1991년에 개발되었습니다.'
        ],
        'contexts': [
            ['서울특별시는 대한민국의 수도이자 최대 도시입니다. 조선 시대부터 수도 역할을 해왔습니다.'],
            ['파이썬(Python)은 1991년 귀도 반 로섬이 발표한 고급 프로그래밍 언어로, 플랫폼에 독립적이며 인터프리터식, 객체지향적 언어입니다.']
        ],
        'ground_truths': [
            ['서울은 한국의 수도이다.'],
            ['파이썬은 프로그래밍 언어이다.']
        ]
    }
    
    dataset = Dataset.from_dict(test_data)
    print(f"✅ 테스트 데이터셋 생성: {len(dataset)}개 항목")
    
    # 메트릭 설정
    print("\n2️⃣ 메트릭 설정")
    metrics_to_test = [
        (faithfulness, "Faithfulness"),
        (answer_relevancy, "Answer Relevancy"),
        (context_precision, "Context Precision"),
        (context_recall, "Context Recall")
    ]
    
    # 각 메트릭 개별 테스트
    for metric, name in metrics_to_test:
        print(f"\n{'='*50}")
        print(f"📊 {name} 테스트")
        print(f"{'='*50}")
        
        metric.llm = llm
        
        try:
            result = evaluate(
                dataset=dataset,
                metrics=[metric],
                llm=llm,
                raise_exceptions=False,
                show_progress=False
            )
            
            if hasattr(result, 'to_pandas'):
                df = result.to_pandas()
                metric_col = metric.name
                
                if metric_col in df.columns:
                    scores = df[metric_col].tolist()
                    print(f"✅ {name} 점수:")
                    for i, score in enumerate(scores):
                        print(f"   샘플 {i+1}: {score}")
                    
                    # 평균 점수 계산 (NaN이 아닌 값만)
                    valid_scores = [s for s in scores if str(s) != 'nan']
                    if valid_scores:
                        avg_score = sum(valid_scores) / len(valid_scores)
                        print(f"   평균: {avg_score:.3f}")
                    else:
                        print(f"   ⚠️ 모든 점수가 NaN")
                else:
                    print(f"❌ {name} 컬럼을 찾을 수 없음")
            
        except Exception as e:
            print(f"❌ {name} 평가 실패: {e}")
            import traceback
            traceback.print_exc()
    
    # 전체 메트릭 동시 테스트
    print(f"\n\n{'='*70}")
    print("📊 전체 메트릭 동시 평가")
    print(f"{'='*70}")
    
    # 모든 메트릭에 LLM 설정
    for metric, _ in metrics_to_test:
        metric.llm = llm
    
    try:
        result = evaluate(
            dataset=dataset,
            metrics=[m for m, _ in metrics_to_test],
            llm=llm,
            raise_exceptions=False,
            show_progress=True
        )
        
        print("\n✅ 전체 평가 완료!")
        
        if hasattr(result, 'to_pandas'):
            df = result.to_pandas()
            
            print("\n📊 최종 결과:")
            print("-" * 50)
            
            for metric, name in metrics_to_test:
                metric_col = metric.name
                if metric_col in df.columns:
                    scores = df[metric_col].tolist()
                    valid_scores = [s for s in scores if str(s) != 'nan']
                    if valid_scores:
                        avg_score = sum(valid_scores) / len(valid_scores)
                        print(f"{name:20s}: {avg_score:.3f}")
                    else:
                        print(f"{name:20s}: NaN")
            
            # 전체 데이터프레임 출력
            print("\n전체 데이터:")
            print(df)
            
    except Exception as e:
        print(f"\n❌ 전체 평가 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_all_metrics()