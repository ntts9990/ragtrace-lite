#!/usr/bin/env python3
"""
Debug RAGAS parsing issues by examining the exact flow
"""
import os
import sys
import json
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ragtrace_lite.config_loader import load_config
from ragtrace_lite.llm_factory import create_llm
from ragtrace_lite.hcx_proxy import HCXRAGASProxy
from ragas.metrics import context_precision, context_recall, answer_correctness
from ragas import EvaluationDataset, evaluate, SingleTurnSample


async def test_ragas_parsing():
    """Test RAGAS parsing with different response formats"""
    print("=" * 80)
    print("🔍 RAGAS Parsing Debug Test")
    print("=" * 80)
    
    # Setup
    config = load_config()
    base_llm = create_llm(config)
    proxy_llm = HCXRAGASProxy(base_llm)
    
    # Test data - RAGAS expects list of dicts, not dict of lists
    test_data = [
        {
            "user_input": "한국의 수도는 어디인가요?",
            "response": "서울입니다.",
            "retrieved_contexts": ["서울특별시는 대한민국의 수도이자 최대 도시입니다."],
            "reference": "서울은 한국의 수도입니다."
        }
    ]
    
    dataset = EvaluationDataset.from_list(test_data)
    
    # Test 1: Direct prompt test
    print("\n1️⃣ Direct Prompt Test")
    print("-" * 60)
    
    test_prompt = """Given question, answer and context verify if the context was useful in arriving at the given answer. Give verdict as "1" if useful and "0" if not with json output.
Please return the output in a JSON format that complies with the following schema as specified in JSON Schema:
{"type": "object", "properties": {"reason": {"type": "string", "description": "Reason for verification"}, "verdict": {"type": "integer", "description": "Binary (0/1) verdict of verification"}}, "required": ["reason", "verdict"], "title": "Verification", "additionalProperties": false}

Input: {"question": "한국의 수도는 어디인가요?", "context": "서울특별시는 대한민국의 수도이자 최대 도시입니다.", "answer": "서울입니다."}
Output: """
    
    try:
        # Test base LLM response
        print("Testing base LLM...")
        base_response = base_llm._call(test_prompt)
        print(f"Base response: {base_response}")
        
        # Test proxy response
        print("\nTesting proxy LLM...")
        proxy_response = proxy_llm._call(test_prompt)
        print(f"Proxy response: {proxy_response}")
        
        # Try parsing
        try:
            parsed = json.loads(proxy_response)
            print(f"✅ Parsed successfully: {parsed}")
        except Exception as e:
            print(f"❌ Parse error: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: RAGAS evaluation
    print("\n\n2️⃣ RAGAS Evaluation Test")
    print("-" * 60)
    
    try:
        # Configure metrics
        context_precision.llm = proxy_llm
        context_recall.llm = proxy_llm
        answer_correctness.llm = proxy_llm
        
        # Run evaluation
        print("Running RAGAS evaluation...")
        result = evaluate(
            dataset, 
            metrics=[context_precision, context_recall, answer_correctness],
            llm=proxy_llm
        )
        
        print(f"\n✅ Success! Results: {result}")
        
    except Exception as e:
        print(f"\n❌ RAGAS evaluation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Check what RAGAS expects
    print("\n\n3️⃣ RAGAS Expected Format Analysis")
    print("-" * 60)
    
    # Check the output parser
    from ragas.prompt.pydantic_prompt import RagasOutputParser
    from ragas.metrics._context_precision import Verification
    
    parser = RagasOutputParser(pydantic_object=Verification)
    
    # Test different response formats
    test_responses = [
        '{"reason": "Context provides the answer", "verdict": 1}',
        '{"verdict": 1, "reason": "Context is useful"}',
        '{"relevant": 1}',
        '1',
        '{"reason": "유용함", "verdict": "1"}',  # String instead of int
        '{"reason": "유용함", "verdict": 1.0}',  # Float instead of int
    ]
    
    for i, resp in enumerate(test_responses):
        print(f"\nTest response {i+1}: {resp}")
        try:
            # Import required classes
            from langchain_core.prompt_values import StringPromptValue
            from ragas.prompt.utils import extract_json
            
            # Try extract_json first
            extracted = extract_json(resp)
            print(f"  Extracted JSON: {extracted}")
            
            # Try parsing
            parsed = parser.parse(extracted)
            print(f"  ✅ Parsed: {parsed}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Set API key
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    
    # Run async test
    asyncio.run(test_ragas_parsing())