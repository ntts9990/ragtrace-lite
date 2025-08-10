#!/usr/bin/env python3
"""
프록시를 통한 RAGAS 직접 테스트
"""
import os
import sys
import json
from datasets import Dataset
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ragtrace_lite.config_loader import load_config
from ragtrace_lite.llm_factory import create_llm
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy


def test_ragas_with_proxy():
    """RAGAS와 프록시 통합 테스트"""
    print("=" * 70)
    print("🧪 RAGAS-프록시 통합 테스트")
    print("=" * 70)
    
    # 환경 설정
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    config = load_config()
    
    # 프록시가 적용된 LLM 생성
    print("\n1️⃣ 프록시 LLM 생성")
    llm = create_llm(config)
    print(f"✅ LLM 타입: {type(llm).__name__}")
    
    # 간단한 테스트 데이터
    test_data = {
        'question': ['한국의 수도는 어디인가요?'],
        'answer': ['한국의 수도는 서울입니다.'],
        'contexts': [['서울특별시는 대한민국의 수도이자 최대 도시입니다.']],
        'ground_truths': [['한국의 수도는 서울이다.']]
    }
    
    dataset = Dataset.from_dict(test_data)
    print(f"✅ 테스트 데이터셋 생성: {len(dataset)}개 항목")
    
    # 메트릭 설정
    print("\n2️⃣ 메트릭 설정")
    faithfulness.llm = llm
    answer_relevancy.llm = llm
    
    metrics = [faithfulness, answer_relevancy]
    print(f"✅ 메트릭 설정 완료: {[m.name for m in metrics]}")
    
    # 평가 실행
    print("\n3️⃣ RAGAS 평가 실행")
    print("-" * 50)
    
    try:
        result = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=llm,
            raise_exceptions=False,  # 파싱 오류 무시
            show_progress=True
        )
        
        print("\n✅ 평가 완료!")
        
        # 결과 확인
        if hasattr(result, 'to_pandas'):
            df = result.to_pandas()
            print("\n📊 평가 결과:")
            print(df)
            
            # 메트릭별 점수 확인
            print("\n📈 메트릭별 점수:")
            for col in df.columns:
                if col not in ['question', 'answer', 'contexts', 'ground_truths']:
                    print(f"  - {col}: {df[col].dtype}")
                    if df[col].dtype in ['float64', 'int64']:
                        print(f"    값: {df[col].iloc[0]}")
                    else:
                        print(f"    값 타입: {type(df[col].iloc[0])}")
                        print(f"    값: {str(df[col].iloc[0])[:50]}...")
        
        # 점수 딕셔너리 확인
        if hasattr(result, 'scores'):
            print("\n📊 점수 딕셔너리:")
            if isinstance(result.scores, dict):
                for key, value in result.scores.items():
                    print(f"  - {key}: {value}")
            else:
                print(f"scores 타입: {type(result.scores)}")
                print(f"scores 내용: {result.scores}")
                
    except Exception as e:
        print(f"\n❌ 평가 실패: {e}")
        import traceback
        traceback.print_exc()


def test_proxy_responses():
    """프록시의 실제 응답 확인"""
    print("\n\n4️⃣ 프록시 응답 상세 확인")
    print("=" * 70)
    
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    config = load_config()
    llm = create_llm(config)
    
    # faithfulness 테스트
    prompt = """Given the following information, extract factual statements:
Answer: 한국의 수도는 서울입니다. 서울의 인구는 약 950만 명입니다.

Extract all factual claims from the answer."""
    
    print("📊 Faithfulness 프롬프트:")
    print(prompt)
    print("\n응답:")
    response = llm._call(prompt)
    print(response)
    
    # JSON 파싱 확인
    try:
        data = json.loads(response)
        print(f"\n✅ JSON 파싱 성공: {list(data.keys())}")
    except:
        print("\n❌ JSON 파싱 실패")


if __name__ == "__main__":
    test_ragas_with_proxy()
    test_proxy_responses()