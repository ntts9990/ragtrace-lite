#!/usr/bin/env python3
"""
RAGAS 직접 테스트 - 각 메트릭별로 개별 실행
"""
import os
import sys
import json
import asyncio
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ragtrace_lite.config_loader import load_config
from ragtrace_lite.llm_factory import create_llm
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall


async def test_single_metric(metric, dataset, llm, embeddings=None):
    """단일 메트릭 테스트"""
    print(f"\n{'='*60}")
    print(f"📊 {metric.__class__.__name__} 테스트")
    print(f"{'='*60}")
    
    try:
        # 메트릭 설정
        if hasattr(metric, 'llm'):
            metric.llm = llm
        if hasattr(metric, 'embeddings') and embeddings:
            metric.embeddings = embeddings
            
        print(f"⏳ 평가 시작...")
        start_time = datetime.now()
        
        # 평가 실행
        result = evaluate(
            dataset=dataset,
            metrics=[metric],
            llm=llm,
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"✅ 평가 완료 ({elapsed:.1f}초)")
        
        # 결과 출력
        metric_name = metric.__class__.__name__.lower()
        if metric_name in result.scores:
            score = result.scores[metric_name]
            print(f"📈 점수: {score}")
            
            # 상세 결과
            if hasattr(result, 'to_pandas'):
                df = result.to_pandas()
                if metric_name in df.columns:
                    detail_score = df[metric_name].iloc[0]
                    print(f"   상세: {detail_score}")
        else:
            print(f"❌ 점수를 찾을 수 없음")
            print(f"   사용 가능한 점수: {list(result.scores.keys())}")
            
    except Exception as e:
        print(f"❌ 평가 실패: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """메인 테스트 함수"""
    print("=" * 80)
    print("🔍 RAGAS 직접 테스트")
    print("=" * 80)
    
    # 설정 및 LLM 로드
    config = load_config()
    llm = create_llm(config)
    print(f"✅ LLM 로드: {type(llm).__name__}")
    
    # 임베딩 모델 로드 (answer_relevancy에 필요)
    from langchain_community.embeddings import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    print(f"✅ 임베딩 로드: BGE-M3")
    
    # 테스트 데이터
    test_data = {
        'question': ['한국의 수도는 어디인가요?'],
        'answer': ['한국의 수도는 서울입니다. 서울은 약 950만 명의 인구가 거주하는 대한민국 최대의 도시입니다.'],
        'contexts': [['서울특별시는 대한민국의 수도이자 최대 도시로, 정치, 경제, 문화의 중심지입니다.']],
        'ground_truths': [['한국의 수도는 서울이다.']]
    }
    
    dataset = Dataset.from_dict(test_data)
    print(f"✅ 데이터셋 생성: {len(dataset)}개 항목")
    
    # 각 메트릭 테스트
    metrics = [
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall
    ]
    
    for metric in metrics:
        await test_single_metric(metric, dataset, llm, embeddings)
    
    print("\n" + "="*80)
    print("✅ 테스트 완료")
    print("="*80)


if __name__ == "__main__":
    # API 키 설정
    os.environ['CLOVA_STUDIO_API_KEY'] = "nv-d78e840d8f5c4e2faed883a52ea91375gmj8"
    
    # 비동기 실행
    asyncio.run(main())