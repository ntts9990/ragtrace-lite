#!/usr/bin/env python3
"""
HCX RAGAS 호환성 개선 테스트
"""
import os
import json
import asyncio
from dotenv import load_dotenv
import sys
sys.path.append('src')

from ragtrace_lite.llm_factory import HcxAdapter
# hcx_ragas_adapter를 직접 import
sys.path.append('src/ragtrace_lite')
import hcx_ragas_adapter
HCXRAGASAdapter = hcx_ragas_adapter.HCXRAGASAdapter


# RAGAS에서 실제 사용하는 프롬프트들
TEST_PROMPTS = {
    "faithfulness": """Given the following statements, please extract factual claims:
Question: 라면은 어떻게 만드나요?
Answer: 라면을 만들기 위해서는 먼저 물을 끓인 후 면과 스프를 넣고 3-4분간 끓여주면 됩니다.

Extract statements from the answer.""",
    
    "answer_relevancy": """Generate a question for the given answer.
Answer: 서울은 대한민국의 수도이며 약 950만 명이 거주합니다.

Generate a question that this answer would address.""",
    
    "context_precision": """Given the context and question, determine if the context is relevant.
Context: 서울은 한국의 수도이자 최대 도시입니다.
Question: 한국의 수도는 어디인가요?

Is the context relevant to answering the question?"""
}


async def test_improved_hcx():
    """개선된 HCX 어댑터 테스트"""
    load_dotenv()
    api_key = os.getenv('CLOVA_STUDIO_API_KEY', '').strip()
    
    if not api_key or not api_key.startswith('nv-'):
        print("❌ 유효한 HCX API 키가 필요합니다")
        return
    
    hcx = HcxAdapter(api_key)
    
    print("=== HCX RAGAS 호환성 개선 테스트 ===\n")
    
    for metric_name, prompt in TEST_PROMPTS.items():
        print(f"\n📊 {metric_name.upper()} 테스트")
        print("-" * 50)
        
        # 1. 메트릭 타입 감지 테스트
        detected_type = HCXRAGASAdapter.detect_metric_type(prompt)
        print(f"✅ 감지된 메트릭 타입: {detected_type}")
        
        # 2. 프롬프트 강화 확인
        enhanced = HCXRAGASAdapter.enhance_prompt_for_hcx(prompt, detected_type)
        print(f"✅ 프롬프트 강화 적용됨 (추가 {len(enhanced) - len(prompt)}자)")
        
        # 3. HCX API 호출
        try:
            response = await hcx.agenerate_answer(prompt)
            print(f"\n📥 HCX 원본 응답:")
            print(f"   {response[:100]}..." if len(response) > 100 else f"   {response}")
            
            # 4. 정리된 응답 확인
            cleaned = hcx._clean_response_for_ragas(response)
            print(f"\n📤 RAGAS 형식 변환:")
            print(f"   {cleaned}")
            
            # 5. JSON 파싱 확인
            try:
                parsed = json.loads(cleaned)
                print(f"\n✅ JSON 파싱 성공!")
                print(f"   키: {list(parsed.keys())}")
                
                # RAGAS 형식 검증
                if metric_name == "faithfulness" and "statements" in parsed:
                    print(f"   ✅ statements 필드 확인: {len(parsed['statements'])}개")
                elif metric_name == "answer_relevancy" and "question" in parsed:
                    print(f"   ✅ question 필드 확인: {parsed['question'][:50]}...")
                elif metric_name == "context_precision" and "relevant" in parsed:
                    print(f"   ✅ relevant 필드 확인: {parsed['relevant']}")
                    
            except json.JSONDecodeError:
                print(f"\n❌ JSON 파싱 실패 - 텍스트 응답으로 처리됨")
                
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
        
        # Rate limit 대기
        if metric_name != list(TEST_PROMPTS.keys())[-1]:
            print("\n⏳ Rate limit 대기 중...")
            await asyncio.sleep(10)


async def test_edge_cases():
    """엣지 케이스 테스트"""
    print("\n\n=== 엣지 케이스 테스트 ===\n")
    
    test_responses = [
        ('{"text": "이것은 텍스트입니다"}', "faithfulness"),
        ('여기에 몇 가지 문장이 있습니다. 첫 번째 문장. 두 번째 문장.', "faithfulness"),
        ('{"generated_question": "무엇인가요?"}', "answer_relevancy"),
        ('질문: "서울의 인구는?"', "answer_relevancy"),
        ('{"is_relevant": true}', "context_precision"),
        ('예, 관련이 있습니다.', "context_precision"),
    ]
    
    for response, metric_type in test_responses:
        print(f"\n테스트: {metric_type}")
        print(f"입력: {response}")
        result = HCXRAGASAdapter.parse_hcx_response(response, metric_type)
        print(f"출력: {json.dumps(result, ensure_ascii=False)}")


async def main():
    """메인 실행 함수"""
    # 실제 API 테스트
    await test_improved_hcx()
    
    # 엣지 케이스 테스트
    await test_edge_cases()


if __name__ == "__main__":
    asyncio.run(main())