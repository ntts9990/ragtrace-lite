#!/usr/bin/env python3
"""
RAGAS 프롬프트 분석
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ragas.metrics import faithfulness, answer_relevancy
# from ragas.metrics._faithfulness import FaithfulnessStatements
from datasets import Dataset


def test_ragas_prompts():
    """RAGAS가 사용하는 실제 프롬프트 확인"""
    print("🔍 RAGAS 프롬프트 분석")
    print("=" * 70)
    
    # 1. Faithfulness 프롬프트 확인
    print("\n1️⃣ Faithfulness 프롬프트:")
    print("-" * 50)
    
    # statement_generator_prompt 확인
    if hasattr(faithfulness, 'statement_generator_prompt'):
        prompt = faithfulness.statement_generator_prompt
        print(f"프롬프트 타입: {type(prompt)}")
        
        # 프롬프트 템플릿 확인
        if hasattr(prompt, 'instruction'):
            print(f"\n지시사항:")
            print(prompt.instruction)
        
        if hasattr(prompt, 'examples'):
            print(f"\n예시 개수: {len(prompt.examples) if prompt.examples else 0}")
        
        if hasattr(prompt, 'output_model'):
            print(f"\n출력 모델: {prompt.output_model}")
            # Pydantic 모델 필드 확인
            if hasattr(prompt.output_model, '__fields__'):
                print("필드들:")
                for field_name, field_info in prompt.output_model.__fields__.items():
                    print(f"  - {field_name}: {field_info}")
    
    # 2. NLI 프롬프트 확인
    print("\n\n2️⃣ NLI (Natural Language Inference) 프롬프트:")
    print("-" * 50)
    
    if hasattr(faithfulness, 'nli_prompt'):
        prompt = faithfulness.nli_prompt
        print(f"프롬프트 타입: {type(prompt)}")
        
        if hasattr(prompt, 'instruction'):
            print(f"\n지시사항:")
            print(prompt.instruction)
        
        if hasattr(prompt, 'output_model'):
            print(f"\n출력 모델: {prompt.output_model}")
    
    # 3. Answer Relevancy 프롬프트 확인
    print("\n\n3️⃣ Answer Relevancy 프롬프트:")
    print("-" * 50)
    
    if hasattr(answer_relevancy, 'question_generation_prompt'):
        prompt = answer_relevancy.question_generation_prompt
        print(f"프롬프트 타입: {type(prompt)}")
        
        if hasattr(prompt, 'instruction'):
            print(f"\n지시사항:")
            print(prompt.instruction)
        
        if hasattr(prompt, 'output_model'):
            print(f"\n출력 모델: {prompt.output_model}")
            if hasattr(prompt.output_model, '__fields__'):
                print("필드들:")
                for field_name, field_info in prompt.output_model.__fields__.items():
                    print(f"  - {field_name}: {field_info}")


def test_expected_output_format():
    """예상 출력 형식 테스트"""
    print("\n\n🔍 예상 출력 형식")
    print("=" * 70)
    
    # faithfulness 메트릭의 속성 확인
    print("\n1️⃣ Faithfulness 메트릭 속성:")
    print(f"메트릭 이름: {faithfulness.name}")
    print(f"속성들: {[attr for attr in dir(faithfulness) if not attr.startswith('_')]}")


if __name__ == "__main__":
    test_ragas_prompts()
    test_expected_output_format()