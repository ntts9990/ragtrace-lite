#!/usr/bin/env python3
"""
비동기 호출 디버깅
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ragtrace_lite.config_loader import load_config
from ragtrace_lite.llm_factory import create_llm


async def test_async_methods():
    """비동기 메서드 테스트"""
    print("🔍 비동기 메서드 디버깅")
    print("=" * 70)
    
    # 환경 설정
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    config = load_config()
    
    # LLM 생성
    llm = create_llm(config)
    print(f"✅ LLM 타입: {type(llm).__name__}")
    
    # 1. _acall 테스트
    print("\n1️⃣ _acall 메서드 테스트")
    try:
        response = await llm._acall("Hello, respond with 'OK'")
        print(f"✅ _acall 성공: {response}")
    except Exception as e:
        print(f"❌ _acall 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. agenerate 테스트
    print("\n2️⃣ agenerate 메서드 테스트")
    try:
        # agenerate가 코루틴을 반환하는지 확인
        coro = llm.agenerate(["Hello, respond with 'OK'"])
        print(f"agenerate 반환 타입: {type(coro)}")
        print(f"코루틴인가?: {asyncio.iscoroutine(coro)}")
        
        # 코루틴 실행
        result = await coro
        print(f"✅ agenerate 성공: {type(result)}")
        print(f"결과: {result}")
    except Exception as e:
        print(f"❌ agenerate 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. generate 메서드 테스트 (비동기 컨텍스트에서)
    print("\n3️⃣ generate 메서드 테스트 (비동기 컨텍스트)")
    try:
        result = llm.generate(["Hello, respond with 'OK'"])
        print(f"generate 반환 타입: {type(result)}")
        
        # 코루틴이면 await
        if asyncio.iscoroutine(result):
            print("generate가 코루틴 반환 (비동기 컨텍스트)")
            actual_result = await result
            print(f"✅ 결과: {type(actual_result)}")
        else:
            print(f"✅ 직접 결과 반환: {type(result)}")
    except Exception as e:
        print(f"❌ generate 실패: {e}")
        import traceback
        traceback.print_exc()


def test_sync_methods():
    """동기 메서드 테스트"""
    print("\n\n4️⃣ 동기 메서드 테스트")
    print("=" * 70)
    
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    config = load_config()
    llm = create_llm(config)
    
    try:
        result = llm.generate(["Hello, respond with 'OK'"])
        print(f"generate 반환 타입 (동기): {type(result)}")
        print(f"✅ 동기 generate 성공")
    except Exception as e:
        print(f"❌ 동기 generate 실패: {e}")


if __name__ == "__main__":
    # 비동기 테스트
    asyncio.run(test_async_methods())
    
    # 동기 테스트
    test_sync_methods()