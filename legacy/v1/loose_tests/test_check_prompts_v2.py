#!/usr/bin/env python3
"""
RAGAS가 실제로 사용하는 프롬프트 상세 확인
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness,
)

print("=" * 80)
print("RAGAS 메트릭별 프롬프트 상세 정보")
print("=" * 80)

# 각 메트릭의 프롬프트 확인
metrics = {
    "faithfulness": faithfulness,
    "answer_relevancy": answer_relevancy,
    "context_precision": context_precision,
    "context_recall": context_recall,
    "answer_correctness": answer_correctness,
}

for name, metric in metrics.items():
    print(f"\n📊 {name}")
    print("-" * 60)
    
    # 모든 속성 확인
    attrs = dir(metric)
    prompt_attrs = [attr for attr in attrs if 'prompt' in attr.lower()]
    
    for attr in prompt_attrs:
        try:
            value = getattr(metric, attr)
            print(f"  {attr}: {type(value).__name__}")
            
            # Prompt 객체의 속성 확인
            if hasattr(value, 'instruction'):
                print(f"    instruction preview: {str(value.instruction)[:150]}...")
            if hasattr(value, 'name'):
                print(f"    name: {value.name}")
            if hasattr(value, 'input_keys'):
                print(f"    input_keys: {value.input_keys}")
            if hasattr(value, 'output_key'):
                print(f"    output_key: {value.output_key}")
            if hasattr(value, 'output_type'):
                print(f"    output_type: {value.output_type}")
                
        except Exception as e:
            print(f"    Error accessing {attr}: {e}")

print("\n" + "=" * 80)