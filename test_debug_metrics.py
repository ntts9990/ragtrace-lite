#!/usr/bin/env python3
"""
HCX 응답 디버깅을 위한 직접 테스트
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ragtrace_lite.config_loader import load_config
from ragtrace_lite.llm_factory import create_llm


def test_metric_responses():
    """각 메트릭의 실제 응답 확인"""
    print("=" * 80)
    print("🔍 HCX 메트릭별 응답 디버깅")
    print("=" * 80)
    
    # 설정 및 LLM 로드
    config = load_config()
    llm = create_llm(config)
    
    # 테스트할 프롬프트들
    test_prompts = {
        "context_precision": """Given question, answer and context verify if the context was useful in arriving at the given answer. Give verdict as "1" if useful and "0" if not with json output.

Question: 한국의 수도는 어디인가요?
Answer: 서울입니다.
Context: 서울특별시는 대한민국의 수도이자 최대 도시입니다.

중요: 컨텍스트가 답변을 생성하는데 유용했는지 판단하세요.
반드시 다음 중 하나로만 답하세요:
- "1" (유용함)
- "0" (유용하지 않음)

숫자만 답하세요. 설명은 필요없습니다.""",

        "context_recall": """Given a context, and an answer, analyze each sentence in the answer and classify if the sentence can be attributed to the given context or not.

Context: Python의 리스트는 대괄호 []를 사용하며, 동적으로 크기가 변할 수 있습니다.
Answer: 리스트는 가변 객체로 요소를 추가할 수 있습니다. 리스트는 대괄호를 사용합니다.

각 문장이 컨텍스트에서 지원되는지 확인하고, 다음 형식으로 답하세요:
[1, 0, 1, 1, 0]

각 숫자는:
- 1: 해당 문장이 컨텍스트에서 지원됨
- 0: 해당 문장이 컨텍스트에서 지원되지 않음

대괄호 안에 쉼표로 구분된 숫자만 답하세요.""",

        "answer_correctness": """Given a ground truth and an answer statements, analyze each statement and classify them in one of the following categories:

Ground Truth: 리스트는 변경 가능하고 튜플은 변경 불가능하다.
Answer: 리스트는 가변 객체이고 튜플은 불변 객체입니다. 리스트는 대괄호를 사용합니다.

Ground truth와 answer를 비교하여 다음 형식으로 분류하세요:
{
  "TP": ["정답과 일치하는 문장1", "문장2"],
  "FP": ["정답에 없는 잘못된 문장3"],
  "FN": ["정답에는 있지만 답변에 없는 문장4"]
}

TP=True Positive, FP=False Positive, FN=False Negative"""
    }
    
    # 각 프롬프트 테스트
    for metric_name, prompt in test_prompts.items():
        print(f"\n📊 {metric_name}")
        print("-" * 60)
        print(f"프롬프트:\n{prompt[:100]}...")
        
        try:
            # HCX 호출
            response = llm._call(prompt)
            print(f"\n응답:\n{response}")
            
            # JSON 파싱 시도
            try:
                import json
                if response.strip().startswith('{') or response.strip().startswith('['):
                    parsed = json.loads(response)
                    print(f"\n✅ JSON 파싱 성공: {parsed}")
                else:
                    print(f"\n⚠️ JSON이 아닌 응답")
            except json.JSONDecodeError as e:
                print(f"\n❌ JSON 파싱 실패: {e}")
                
        except Exception as e:
            print(f"\n❌ 호출 실패: {e}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # API 키 설정
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    
    # 테스트 실행
    test_metric_responses()