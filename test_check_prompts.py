#!/usr/bin/env python3
"""
RAGAS가 실제로 사용하는 프롬프트 확인
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

# 각 메트릭의 프롬프트 확인
print("=" * 80)
print("RAGAS 메트릭별 프롬프트 확인")
print("=" * 80)

# 메트릭 리스트
metrics = [
    ("faithfulness", faithfulness),
    ("answer_relevancy", answer_relevancy),
    ("context_precision", context_precision),
    ("context_recall", context_recall),
    ("answer_correctness", answer_correctness),
]

for name, metric in metrics:
    print(f"\n📊 {name}")
    print("-" * 60)
    
    # 메트릭의 속성 확인
    if hasattr(metric, '__dict__'):
        for attr, value in metric.__dict__.items():
            if 'prompt' in attr.lower():
                print(f"  {attr}: {type(value)}")
                if hasattr(value, 'instruction'):
                    print(f"    instruction: {value.instruction[:100]}...")
                elif hasattr(value, 'name'):
                    print(f"    name: {value.name}")
    
    # 메트릭이 사용하는 프롬프트 이름들
    if hasattr(metric, '_required_columns'):
        print(f"  required_columns: {metric._required_columns()}")
    
    if hasattr(metric, 'name'):
        print(f"  metric name: {metric.name}")

print("\n" + "=" * 80)