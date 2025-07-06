#!/usr/bin/env python3
"""
RAGAS 비동기 호출 추적
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ragtrace_lite.config_loader import load_config
from ragtrace_lite.llm_factory import create_llm
from ragtrace_lite.hcx_proxy import HCXRAGASProxy
from langchain_core.outputs import LLMResult, Generation
from typing import List, Any, Union
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness


class TracingProxy(HCXRAGASProxy):
    """호출 추적을 위한 프록시"""
    
    async def agenerate(self, prompts: List[Union[str, Any]], **kwargs: Any):
        """추적 기능이 있는 agenerate"""
        print(f"\n🔍 agenerate 호출됨")
        print(f"  - prompts 타입: {type(prompts)}")
        print(f"  - prompts 개수: {len(prompts) if isinstance(prompts, list) else 1}")
        
        # 원래 메서드 호출
        coro = super().agenerate(prompts, **kwargs)
        print(f"  - 반환 타입: {type(coro)}")
        print(f"  - 코루틴?: {asyncio.iscoroutine(coro)}")
        
        # 실행하고 결과 확인
        try:
            result = await coro
            print(f"  - await 후 결과 타입: {type(result)}")
            print(f"  - LLMResult?: {isinstance(result, LLMResult)}")
            return result
        except Exception as e:
            print(f"  - ❌ await 실패: {type(e).__name__}: {e}")
            raise
    
    def generate(self, prompts: List[Union[str, Any]], **kwargs: Any):
        """추적 기능이 있는 generate"""
        print(f"\n🔍 generate 호출됨")
        print(f"  - 비동기 컨텍스트?: ", end="")
        try:
            loop = asyncio.get_running_loop()
            print("예")
            # 비동기 컨텍스트에서는 agenerate 호출
            return self.agenerate(prompts, **kwargs)
        except RuntimeError:
            print("아니오")
            # 동기 컨텍스트
            return super().generate(prompts, **kwargs)


async def test_with_ragas():
    """RAGAS로 직접 테스트"""
    print("🧪 RAGAS 비동기 호출 추적")
    print("=" * 70)
    
    # 환경 설정
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    config = load_config()
    
    # TracingProxy로 감싸기
    from ragtrace_lite.llm_factory import LLMAdapterWrapper, HcxAdapter
    adapter = HcxAdapter(config.llm.api_key, config.llm.model_name or "HCX-005")
    base_llm = LLMAdapterWrapper(adapter)
    llm = TracingProxy(base_llm)
    
    print(f"✅ 추적 프록시 설정 완료")
    
    # 간단한 테스트 데이터
    test_data = {
        'question': ['한국의 수도는?'],
        'answer': ['서울입니다.'],
        'contexts': [['서울은 대한민국의 수도이다.']],
        'ground_truths': [['서울']]
    }
    
    dataset = Dataset.from_dict(test_data)
    
    # 메트릭 설정
    faithfulness.llm = llm
    
    print("\n📊 RAGAS 평가 시작")
    print("-" * 50)
    
    try:
        result = await asyncio.create_task(
            asyncio.to_thread(
                evaluate,
                dataset=dataset,
                metrics=[faithfulness],
                llm=llm,
                raise_exceptions=True,
                show_progress=False
            )
        )
        print("\n✅ 평가 성공!")
    except Exception as e:
        print(f"\n❌ 평가 실패: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_with_ragas())