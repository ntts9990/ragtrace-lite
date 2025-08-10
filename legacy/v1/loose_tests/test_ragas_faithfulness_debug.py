#!/usr/bin/env python3
"""
RAGAS Faithfulness 디버깅
"""
import os
import sys
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ragtrace_lite.config_loader import load_config
from ragtrace_lite.llm_factory import create_llm
from ragas.metrics import faithfulness
from ragas.metrics._faithfulness import StatementGeneratorOutput
from datasets import Dataset


def test_statement_generator():
    """Statement Generator 직접 테스트"""
    print("🔍 Statement Generator 테스트")
    print("=" * 70)
    
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    config = load_config()
    llm = create_llm(config)
    
    # faithfulness 메트릭에 LLM 설정
    faithfulness.llm = llm
    
    # 테스트 데이터
    test_row = {
        'question': '한국의 수도는 어디인가요?',
        'answer': '한국의 수도는 서울입니다. 서울은 대한민국의 가장 큰 도시입니다.',
        'contexts': ['서울특별시는 대한민국의 수도이자 최대 도시입니다.']
    }
    
    print("\n1️⃣ Statement Generator 프롬프트 생성:")
    prompt = faithfulness.statement_generator_prompt
    
    # 프롬프트에서 직접 generate 호출
    print("\n2️⃣ Statement Generator 실행:")
    try:
        import asyncio
        # 비동기 generate 호출
        result = asyncio.run(prompt.generate(
            data=test_row,
            llm=llm,
            callbacks=None
        ))
        print(f"✅ 생성 성공: {result}")
        print(f"결과 타입: {type(result)}")
        if hasattr(result, 'statements'):
            print(f"statements: {result.statements}")
    except Exception as e:
        print(f"❌ 생성 실패: {e}")
        import traceback
        traceback.print_exc()
    


def test_full_faithfulness():
    """전체 Faithfulness 평가 테스트"""
    print("\n\n🔍 전체 Faithfulness 평가")
    print("=" * 70)
    
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    config = load_config()
    llm = create_llm(config)
    
    # 테스트 데이터
    test_data = {
        'question': ['한국의 수도는 어디인가요?'],
        'answer': ['한국의 수도는 서울입니다.'],
        'contexts': [['서울특별시는 대한민국의 수도입니다.']],
        'ground_truths': [['서울']]
    }
    
    dataset = Dataset.from_dict(test_data)
    
    # 메트릭 설정
    faithfulness.llm = llm
    
    from ragas import evaluate
    
    print("\n평가 실행:")
    try:
        result = evaluate(
            dataset=dataset,
            metrics=[faithfulness],
            llm=llm,
            raise_exceptions=True,  # 오류 발생시 예외 던지기
            show_progress=True
        )
        
        print("\n✅ 평가 성공!")
        print(f"결과: {result}")
        
        if hasattr(result, 'to_pandas'):
            df = result.to_pandas()
            print(f"\nFaithfulness 점수: {df['faithfulness'].iloc[0]}")
            
    except Exception as e:
        print(f"\n❌ 평가 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_statement_generator()
    test_full_faithfulness()