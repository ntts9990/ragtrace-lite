#!/usr/bin/env python3
"""
응답 형식 확인
"""
import os
import sys
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ragtrace_lite.config_loader import load_config
from ragtrace_lite.llm_factory import create_llm


def test_faithfulness_response():
    """Faithfulness 응답 형식 확인"""
    print("🔍 Faithfulness 응답 형식 테스트")
    print("=" * 70)
    
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    config = load_config()
    llm = create_llm(config)
    
    # RAGAS가 사용하는 실제 프롬프트
    prompt = """Given the following question, answer, and context, 
extract factual statements from the answer.

Question: 한국의 수도는?
Answer: 서울입니다.
Context: 서울은 대한민국의 수도이다.

Extract statements from the answer that can be verified."""
    
    print("📝 프롬프트:")
    print(prompt)
    print("\n" + "-" * 50)
    
    # 1. 프록시 응답
    print("\n1️⃣ 프록시 응답:")
    response = llm._call(prompt)
    print(f"타입: {type(response)}")
    print(f"내용: {response}")
    
    # JSON 파싱 시도
    try:
        data = json.loads(response)
        print(f"✅ JSON 파싱 성공: {list(data.keys())}")
        print(f"값 타입들: {[(k, type(v)) for k, v in data.items()]}")
    except Exception as e:
        print(f"❌ JSON 파싱 실패: {e}")
    
    # 2. 베이스 LLM 직접 호출
    print("\n2️⃣ 베이스 LLM 직접 호출:")
    if hasattr(llm, 'hcx'):
        base_response = llm.hcx._call(prompt)
        print(f"타입: {type(base_response)}")
        print(f"내용: {base_response}")
        
        try:
            base_data = json.loads(base_response)
            print(f"✅ JSON 파싱 성공: {list(base_data.keys())}")
        except:
            print("❌ JSON 파싱 실패")
    
    # 3. 어댑터 직접 호출
    print("\n3️⃣ 어댑터 직접 호출:")
    if hasattr(llm, 'hcx') and hasattr(llm.hcx, 'adapter'):
        adapter_response = llm.hcx.adapter.generate_answer(prompt)
        print(f"타입: {type(adapter_response)}")
        print(f"내용: {adapter_response}")


def test_answer_relevancy_response():
    """Answer Relevancy 응답 형식 확인"""
    print("\n\n🔍 Answer Relevancy 응답 형식 테스트")
    print("=" * 70)
    
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    config = load_config()
    llm = create_llm(config)
    
    # RAGAS가 사용하는 프롬프트 형식
    prompt = """Generate a question for the given answer.

Answer: 서울입니다.
Context: 서울은 대한민국의 수도이다.

Generate a question to which the given answer would be appropriate."""
    
    print("📝 프롬프트:")
    print(prompt)
    print("\n" + "-" * 50)
    
    # 프록시 응답
    print("\n프록시 응답:")
    response = llm._call(prompt)
    print(f"내용: {response}")
    
    try:
        data = json.loads(response)
        print(f"✅ JSON 구조: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ JSON 파싱 실패: {e}")


if __name__ == "__main__":
    test_faithfulness_response()
    test_answer_relevancy_response()