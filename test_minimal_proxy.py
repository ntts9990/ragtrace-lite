#!/usr/bin/env python3
"""
최소한의 프록시 테스트
"""
import os
import json
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ragtrace_lite.config_loader import load_config
from ragtrace_lite.llm_factory import create_llm


def test_proxy_direct():
    """프록시가 RAGAS가 원하는 형식을 반환하는지 직접 확인"""
    
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    config = load_config()
    llm = create_llm(config)
    
    print(f"LLM 타입: {type(llm).__name__}")
    
    # 각 메트릭 테스트
    test_prompts = {
        'faithfulness': """Extract factual statements from: 
한국의 수도는 서울입니다. 서울의 인구는 약 950만 명입니다.""",
        
        'answer_relevancy': """Generate a question for:
서울은 대한민국의 수도입니다.""",
        
        'context_precision': """Is the context relevant?
Context: 서울은 한국의 수도입니다.
Question: 한국의 수도는?""",
        
        'context_recall': """Check if statements are supported:
Context: 라면은 3-4분간 끓입니다.
Statements: 1. 라면은 끓여야 한다 2. 조리시간은 10분이다"""
    }
    
    for metric, prompt in test_prompts.items():
        print(f"\n\n=== {metric} ===")
        print(f"프롬프트: {prompt[:50]}...")
        
        try:
            # 프록시 호출
            response = llm._call(prompt)
            print(f"응답: {response}")
            
            # JSON 검증
            data = json.loads(response)
            print(f"✅ JSON 파싱 성공: {list(data.keys())}")
            
            # 필드 검증
            if metric == 'faithfulness' and 'statements' in data:
                print(f"   statements 수: {len(data['statements'])}")
            elif metric == 'answer_relevancy' and 'question' in data:
                print(f"   question: {data['question']}")
            elif metric == 'context_precision' and 'relevant' in data:
                print(f"   relevant: {data['relevant']}")
            elif metric == 'context_recall' and 'attributed' in data:
                print(f"   attributed: {data['attributed']}")
                
        except Exception as e:
            print(f"❌ 오류: {e}")


if __name__ == "__main__":
    test_proxy_direct()