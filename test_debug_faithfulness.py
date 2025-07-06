#!/usr/bin/env python3
"""
Faithfulness 문제 디버깅
"""
import os
import sys
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ragtrace_lite.config_loader import load_config
from ragtrace_lite.llm_factory import create_llm
from langchain_core.prompt_values import StringPromptValue


def test_ragas_calls():
    """RAGAS가 호출하는 방식 테스트"""
    print("🔍 RAGAS 호출 방식 테스트")
    print("=" * 70)
    
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    config = load_config()
    llm = create_llm(config)
    
    # 1. _call 테스트
    print("\n1️⃣ _call 메서드 테스트:")
    prompt = """Given a question and an answer, analyze the complexity of each sentence in the answer. Break down each sentence into one or more fully understandable statements. Ensure that no pronouns are used in any statement. Format the outputs in JSON.

question: 한국의 수도는 어디인가요?
answer: 한국의 수도는 서울입니다.

output:"""
    
    response = llm._call(prompt)
    print(f"응답: {response}")
    print(f"타입: {type(response)}")
    
    # 2. generate 테스트 (RAGAS가 사용하는 방식)
    print("\n\n2️⃣ generate 메서드 테스트:")
    prompt_value = StringPromptValue(text=prompt)
    result = llm.generate([prompt_value])
    print(f"결과 타입: {type(result)}")
    print(f"generations: {result.generations}")
    if result.generations and result.generations[0]:
        text = result.generations[0][0].text
        print(f"텍스트: {text}")
        print(f"텍스트 타입: {type(text)}")
        
        # JSON 파싱 테스트
        try:
            data = json.loads(text)
            print(f"✅ JSON 파싱 성공: {data}")
        except Exception as e:
            print(f"❌ JSON 파싱 실패: {e}")
    
    # 3. agenerate 테스트
    print("\n\n3️⃣ agenerate 메서드 테스트:")
    import asyncio
    
    async def test_agenerate():
        result = await llm.agenerate([prompt_value])
        print(f"비동기 결과 타입: {type(result)}")
        if result.generations and result.generations[0]:
            text = result.generations[0][0].text
            print(f"텍스트: {text}")
    
    asyncio.run(test_agenerate())
    
    # 4. NLI 프롬프트 테스트
    print("\n\n4️⃣ NLI 프롬프트 테스트:")
    nli_prompt = """Your task is to judge the faithfulness of a series of statements based on a given context. For each statement you must return a verdict.

Context: 서울특별시는 대한민국의 수도이자 최대 도시입니다.

statements:
sentence_1: 한국의 수도는 서울입니다.

output:"""
    
    response = llm._call(nli_prompt)
    print(f"NLI 응답: {response}")


if __name__ == "__main__":
    test_ragas_calls()