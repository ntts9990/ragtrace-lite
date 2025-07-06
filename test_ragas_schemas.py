#!/usr/bin/env python3
"""
RAGAS의 정확한 스키마 확인
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# RAGAS 메트릭 임포트
from ragas.metrics import (
    context_precision,
    context_recall,
    answer_correctness,
)

# Pydantic 모델 확인
print("=" * 80)
print("RAGAS 메트릭별 Pydantic 스키마 분석")
print("=" * 80)

# Context Precision
print("\n📊 Context Precision")
print("-" * 60)
if hasattr(context_precision, 'context_precision_prompt'):
    prompt = context_precision.context_precision_prompt
    if hasattr(prompt, 'output_type'):
        print(f"Output Type: {prompt.output_type}")
        if hasattr(prompt.output_type, '__fields__'):
            print("Fields:")
            for field_name, field_info in prompt.output_type.__fields__.items():
                print(f"  - {field_name}: {field_info.annotation}")

# Context Recall
print("\n📊 Context Recall")  
print("-" * 60)
if hasattr(context_recall, 'context_recall_prompt'):
    prompt = context_recall.context_recall_prompt
    if hasattr(prompt, 'output_type'):
        print(f"Output Type: {prompt.output_type}")
        if hasattr(prompt.output_type, '__fields__'):
            print("Fields:")
            for field_name, field_info in prompt.output_type.__fields__.items():
                print(f"  - {field_name}: {field_info.annotation}")

# Answer Correctness
print("\n📊 Answer Correctness")
print("-" * 60)
if hasattr(answer_correctness, 'correctness_prompt'):
    prompt = answer_correctness.correctness_prompt
    if hasattr(prompt, 'output_type'):
        print(f"Output Type: {prompt.output_type}")
        if hasattr(prompt.output_type, '__fields__'):
            print("Fields:")
            for field_name, field_info in prompt.output_type.__fields__.items():
                print(f"  - {field_name}: {field_info.annotation}")

# 실제 프롬프트 예제 생성
print("\n\n📝 프롬프트 출력 타입 예제:")
print("=" * 80)

# 각 메트릭의 프롬프트 객체 확인
for metric_name, metric in [
    ("context_precision", context_precision),
    ("context_recall", context_recall),
    ("answer_correctness", answer_correctness)
]:
    print(f"\n{metric_name}:")
    
    # 프롬프트 객체 찾기
    prompt_obj = None
    for attr in dir(metric):
        if 'prompt' in attr and not attr.startswith('_'):
            obj = getattr(metric, attr)
            if hasattr(obj, 'output_type'):
                prompt_obj = obj
                break
    
    if prompt_obj and hasattr(prompt_obj, 'output_type'):
        try:
            # 예제 인스턴스 생성
            if prompt_obj.output_type.__name__ == 'ContextPrecisionVerification':
                example = {"reason": "컨텍스트가 답변에 도움이 됨", "verdict": 1}
            elif prompt_obj.output_type.__name__ == 'ContextRecallClassifications':
                example = {"classifications": [
                    {"statement": "문장1", "reason": "컨텍스트에서 지원됨", "attributed": 1}
                ]}
            elif prompt_obj.output_type.__name__ == 'CorrectnessClassifications':
                example = {
                    "TP": [{"statement": "올바른 문장", "reason": "정답과 일치"}],
                    "FP": [{"statement": "틀린 문장", "reason": "정답에 없음"}],
                    "FN": []
                }
            else:
                example = "Unknown type"
            
            print(f"  Expected format: {example}")
        except Exception as e:
            print(f"  Error creating example: {e}")

print("\n" + "=" * 80)