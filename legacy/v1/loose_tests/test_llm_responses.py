#!/usr/bin/env python3
"""
HCX vs OpenAI 응답 스타일 비교 테스트
"""
import os
import json
import asyncio
from dotenv import load_dotenv
import sys
sys.path.append('src')
from ragtrace_lite.llm_factory import HcxAdapter

# RAGAS가 사용하는 프롬프트 예시
FAITHFULNESS_PROMPT = """Given a question and answer, create statements from the answer.

Given Q: What is the capital of France?
Given A: The capital of France is Paris.

Your task is to identify statements from the answer that can be inferred from the answer.

Provide your answer in JSON with only the following keys:
statements: [list of statements]

Example format:
{
  "statements": ["The capital of France is Paris"]
}"""

ANSWER_RELEVANCY_PROMPT = """Generate a question based on the given answer.

Given answer: "The capital of France is Paris, which is known for the Eiffel Tower."

Your response must be a JSON with these keys:
- question: The generated question
- noncommittal: 1 if the answer is noncommittal, 0 otherwise

Example format:
{
  "question": "What is the capital of France?",
  "noncommittal": 0
}"""

async def test_hcx_response():
    """HCX 응답 테스트"""
    load_dotenv()
    api_key = os.getenv('CLOVA_STUDIO_API_KEY', '').strip()
    
    if not api_key or not api_key.startswith('nv-'):
        print("❌ 유효한 HCX API 키가 필요합니다")
        return None
        
    hcx = HcxAdapter(api_key)
    
    print("=== HCX 테스트 ===")
    print("프롬프트:", FAITHFULNESS_PROMPT[:100] + "...")
    
    response = await hcx.agenerate_answer(FAITHFULNESS_PROMPT)
    print("\nHCX 응답:")
    print(response)
    print("\n응답 타입:", type(response))
    
    # JSON 파싱 시도
    try:
        parsed = json.loads(response)
        print("✅ JSON 파싱 성공:", parsed)
    except json.JSONDecodeError as e:
        print("❌ JSON 파싱 실패:", e)
        print("   응답이 JSON 형식이 아닙니다")
    
    return response

async def test_with_structure_prompt():
    """구조화된 프롬프트로 HCX 테스트"""
    load_dotenv()
    api_key = os.getenv('CLOVA_STUDIO_API_KEY', '').strip()
    
    if not api_key:
        return None
        
    hcx = HcxAdapter(api_key)
    
    # 더 명확한 JSON 지시사항
    structured_prompt = """다음 질문과 답변을 보고, 답변에서 추출할 수 있는 문장들을 나열하세요.

질문: 라면은 어떻게 만드나요?
답변: 라면을 만들기 위해서는 먼저 물을 끓인 후 면과 스프를 넣고 3-4분간 끓여주면 됩니다.

반드시 다음과 같은 JSON 형식으로만 응답하세요. 다른 설명은 추가하지 마세요:
{
  "statements": [
    "추출된 문장 1",
    "추출된 문장 2"
  ]
}

JSON 응답:"""
    
    print("\n=== 구조화된 프롬프트 테스트 ===")
    response = await hcx.agenerate_answer(structured_prompt)
    print("HCX 응답:")
    print(response)
    
    try:
        parsed = json.loads(response)
        print("✅ JSON 파싱 성공")
    except:
        print("❌ JSON 파싱 실패")
    
    return response

async def main():
    """메인 테스트 함수"""
    print("HCX vs OpenAI 스타일 응답 비교\n")
    
    # 1. 기본 RAGAS 프롬프트 테스트
    await test_hcx_response()
    
    # 2. 구조화된 프롬프트 테스트
    await test_with_structure_prompt()
    
    print("\n=== OpenAI 스타일 예시 ===")
    print("OpenAI는 다음과 같은 형식으로 응답합니다:")
    print(json.dumps({
        "statements": [
            "The capital of France is Paris",
            "Paris is the capital city of France"
        ]
    }, indent=2))

if __name__ == "__main__":
    asyncio.run(main())