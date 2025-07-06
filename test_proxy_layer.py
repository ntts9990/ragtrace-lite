#!/usr/bin/env python3
"""
HCX-RAGAS 프록시 레이어 테스트
"""
import os
import json
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ragtrace_lite.config_loader import load_config
from ragtrace_lite.llm_factory import create_llm
from ragtrace_lite.hcx_proxy import HCXRAGASProxy


# RAGAS가 실제로 보내는 프롬프트 예시
RAGAS_PROMPTS = {
    'faithfulness': """Given the following information, extract factual statements:
Question: 한국의 수도는 어디인가요?
Answer: 한국의 수도는 서울입니다. 서울은 약 950만 명의 인구가 거주하는 대한민국 최대의 도시입니다.

Extract all factual claims from the answer.""",
    
    'answer_relevancy': """Generate a question for the given answer.
Answer: 서울은 대한민국의 수도이며 약 950만 명이 거주합니다.

The question should be relevant to the answer.""",
    
    'context_precision': """Given the following context and question, determine if the context is relevant.
Context: 서울특별시는 대한민국의 수도이자 최대 도시로, 정치, 경제, 문화의 중심지입니다.
Question: 한국의 수도는 어디인가요?

Is the context relevant? Respond with relevant: 1 or relevant: 0""",
    
    'context_recall': """Analyze if the statements are supported by the context.
Context: 라면을 만들려면 물을 끓인 후 면과 스프를 넣고 3-4분간 조리합니다.
Statements:
1. 라면 조리에는 물이 필요하다
2. 면과 스프를 넣어야 한다
3. 조리 시간은 10분이다

For each statement, indicate 1 if supported, 0 if not."""
}


def test_proxy_functionality():
    """프록시 기능 테스트"""
    print("=" * 70)
    print("🧪 HCX-RAGAS 프록시 레이어 테스트")
    print("=" * 70)
    
    # 설정 로드
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    config = load_config()
    
    # LLM 생성 (프록시 포함)
    print("\n1️⃣ LLM 생성 (프록시 적용)")
    print("-" * 50)
    
    try:
        llm = create_llm(config)
        print(f"✅ LLM 타입: {type(llm).__name__}")
        print(f"✅ 프록시 적용 확인: {'HCXRAGASProxy' in str(type(llm))}")
        
        if isinstance(llm, HCXRAGASProxy):
            print("✅ HCX가 프록시로 감싸짐")
        else:
            print("❌ 프록시가 적용되지 않음")
            return
            
    except Exception as e:
        print(f"❌ LLM 생성 실패: {e}")
        return
    
    # 각 메트릭별 테스트
    print("\n2️⃣ 메트릭별 프록시 테스트")
    print("-" * 50)
    
    for metric_name, prompt in RAGAS_PROMPTS.items():
        print(f"\n📊 {metric_name.upper()} 테스트")
        print("=" * 40)
        
        try:
            # 프록시 호출
            response = llm._call(prompt)
            print(f"📤 프록시 응답:\n{response}")
            
            # JSON 파싱 확인
            try:
                data = json.loads(response)
                print(f"\n✅ JSON 파싱 성공!")
                print(f"   구조: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                # 스키마 검증
                if metric_name == 'faithfulness' and 'statements' in data:
                    print(f"   ✅ statements 필드 확인: {len(data['statements'])}개")
                elif metric_name == 'answer_relevancy' and 'question' in data:
                    print(f"   ✅ question 필드 확인: {data['question'][:50]}...")
                elif metric_name == 'context_precision' and 'relevant' in data:
                    print(f"   ✅ relevant 필드 확인: {data['relevant']}")
                elif metric_name == 'context_recall' and 'attributed' in data:
                    print(f"   ✅ attributed 필드 확인: {data['attributed']}")
                    
            except json.JSONDecodeError as e:
                print(f"\n❌ JSON 파싱 실패: {e}")
                
        except Exception as e:
            print(f"\n❌ 프록시 호출 실패: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "-" * 40)
    
    # 엣지 케이스 테스트
    print("\n3️⃣ 엣지 케이스 테스트")
    print("-" * 50)
    
    # 알 수 없는 프롬프트
    unknown_prompt = "이것은 RAGAS 메트릭이 아닌 일반 질문입니다."
    try:
        response = llm._call(unknown_prompt)
        print(f"일반 프롬프트 응답: {response[:100]}...")
        print("✅ 알 수 없는 프롬프트도 정상 처리")
    except Exception as e:
        print(f"❌ 일반 프롬프트 실패: {e}")
    
    print("\n" + "=" * 70)
    print("테스트 완료!")


def test_schema_validation():
    """스키마 검증 테스트"""
    print("\n\n4️⃣ 스키마 검증 테스트")
    print("-" * 50)
    
    # 가짜 프록시로 내부 메서드 테스트
    from ragtrace_lite.llm_factory import LLMAdapterWrapper, HcxAdapter
    
    # 더미 HCX 생성
    class DummyHCX:
        def _call(self, prompt, **kwargs):
            return "테스트 응답"
    
    proxy = HCXRAGASProxy(DummyHCX())
    
    # 각 메트릭별 변환 테스트
    test_cases = {
        'faithfulness': [
            "1. 첫 번째 문장입니다. 2. 두 번째 문장입니다.",
            "- 라면은 맛있다\n- 김치도 맛있다",
            "단일 문장 테스트"
        ],
        'answer_relevancy': [
            '"한국의 수도는 어디인가요?"라는 질문',
            '질문: 서울의 인구는 몇 명인가요?',
            '이것은 질문 생성 테스트입니다'
        ],
        'context_precision': [
            "예, 매우 관련이 있습니다.",
            "아니오, 전혀 관련이 없습니다.",
            "관련성이 애매합니다."
        ]
    }
    
    for metric, test_inputs in test_cases.items():
        print(f"\n{metric} 변환 테스트:")
        for inp in test_inputs:
            result = proxy._force_convert(inp, metric)
            print(f"  입력: {inp[:30]}...")
            print(f"  출력: {json.dumps(result, ensure_ascii=False)}")


if __name__ == "__main__":
    # 메인 테스트
    test_proxy_functionality()
    
    # 스키마 검증 테스트
    test_schema_validation()