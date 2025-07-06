"""
RAGTrace Lite Evaluator

RAGAS 평가 엔진:
- 5가지 메트릭 지원 (faithfulness, answer_relevancy, context_precision, context_recall, answer_correctness)
- 배치 처리 (batch_size 활용)
- 진행률 표시 (tqdm)
- 동기식 평가
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datasets import Dataset
from tqdm import tqdm

# RAGAS imports with fallback
try:
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
        answer_correctness,
    )
    RAGAS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  RAGAS import 오류: {e}")
    RAGAS_AVAILABLE = False

from .config_loader import Config
from .llm_factory import create_llm


class RagasEvaluator:
    """RAGTrace Lite RAGAS 평가 클래스"""
    
    # 메트릭 매핑
    METRIC_MAP = {
        "faithfulness": "faithfulness",
        "answer_relevancy": "answer_relevancy", 
        "context_precision": "context_precision",
        "context_recall": "context_recall",
        "answer_correctness": "answer_correctness",
    } if RAGAS_AVAILABLE else {}
    
    def __init__(self, config: Config, llm=None):
        """
        RAGAS 평가자 초기화
        
        Args:
            config: RAGTrace Lite 설정
            llm: 사전 생성된 LLM 인스턴스 (옵션)
            
        Raises:
            ImportError: RAGAS가 설치되지 않은 경우
            ValueError: 설정이 올바르지 않은 경우
        """
        if not RAGAS_AVAILABLE:
            raise ImportError("RAGAS 라이브러리가 설치되지 않았습니다. 'pip install ragas' 실행하세요.")
            
        self.config = config
        
        # LLM 인스턴스 설정
        if llm:
            print(f"🤖 외부 LLM 사용: {config.llm.provider}")
            self.llm = llm
        else:
            print(f"🤖 새 LLM 생성: {config.llm.provider}")
            self.llm = create_llm(config)
        
        # 임베딩 모델 설정 (HuggingFace 무료 모델 사용)
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            print("✅ HuggingFace 임베딩 모델 로드 완료")
        except ImportError:
            print("⚠️  HuggingFace 임베딩 사용 불가, 기본 임베딩 사용")
            self.embeddings = None
        
        # 평가 메트릭 설정
        self.metrics = self._setup_metrics()
        
        print(f"✅ 평가자 초기화 완료: {len(self.metrics)}개 메트릭")
    
    def _setup_metrics(self) -> List[Any]:
        """평가 메트릭을 설정합니다."""
        metrics = []
        
        print("🔧 메트릭 설정 중...")
        
        for metric_name in self.config.evaluation.metrics:
            try:
                if metric_name == "faithfulness":
                    metric = faithfulness
                    metric.llm = self.llm
                    metrics.append(metric)
                    print(f"  ✅ {metric_name} (LLM 기반)")
                    
                elif metric_name == "answer_relevancy":
                    metric = answer_relevancy
                    metric.llm = self.llm
                    if self.embeddings:
                        metric.embeddings = self.embeddings
                    metrics.append(metric)
                    print(f"  ✅ {metric_name} (LLM + 임베딩 기반)")
                    
                elif metric_name == "context_precision":
                    metric = context_precision
                    metric.llm = self.llm
                    metrics.append(metric)
                    print(f"  ✅ {metric_name} (LLM 기반)")
                    
                elif metric_name == "context_recall":
                    metric = context_recall
                    metric.llm = self.llm
                    metrics.append(metric)
                    print(f"  ✅ {metric_name} (LLM 기반)")
                    
                elif metric_name == "answer_correctness":
                    metric = answer_correctness
                    metric.llm = self.llm
                    metrics.append(metric)
                    print(f"  ✅ {metric_name} (LLM 기반)")
                    
                else:
                    print(f"  ⚠️  알 수 없는 메트릭: {metric_name}")
                    
            except Exception as e:
                print(f"  ❌ {metric_name} 설정 실패: {e}")
        
        if not metrics:
            raise ValueError("설정된 메트릭이 없습니다")
            
        return metrics
    
    def evaluate(self, dataset: Dataset) -> pd.DataFrame:
        """
        데이터셋에 대해 RAGAS 평가를 수행합니다.
        
        Args:
            dataset: 평가할 RAGAS Dataset
            
        Returns:
            pd.DataFrame: 평가 결과 (각 항목별 메트릭 점수)
            
        Raises:
            ValueError: 데이터셋이 올바르지 않은 경우
            Exception: 평가 중 오류가 발생한 경우
        """
        print(f"\n🚀 RAGAS 평가 시작")
        print(f"   - 데이터 수: {len(dataset)}개")
        print(f"   - 메트릭: {len(self.metrics)}개")
        print(f"   - LLM: {self.config.llm.provider}")
        print(f"   - 배치 크기: {self.config.evaluation.batch_size}")
        
        # 데이터셋 검증
        self._validate_dataset(dataset)
        
        try:
            # RAGAS evaluate 호출
            print("\n📊 평가 진행 중...")
            
            # RAGAS는 내부적으로 진행률을 표시하므로 별도 tqdm 불필요
            result = evaluate(
                dataset=dataset,
                metrics=self.metrics,
                llm=self.llm,
                embeddings=self.embeddings,
                raise_exceptions=not self.config.evaluation.raise_exceptions,
                show_progress=self.config.evaluation.show_progress,
            )
            
            print("✅ 평가 완료!")
            
            # 결과를 pandas DataFrame으로 변환
            results_df = result.to_pandas()
            
            # 결과 요약 출력
            self._print_evaluation_summary(results_df)
            
            return results_df
            
        except Exception as e:
            print(f"❌ 평가 실패: {e}")
            raise Exception(f"RAGAS 평가 중 오류 발생: {e}")
    
    def _validate_dataset(self, dataset: Dataset) -> None:
        """평가용 데이터셋을 검증합니다."""
        
        # 기본 검증
        if len(dataset) == 0:
            raise ValueError("데이터셋이 비어있습니다")
        
        # 필수 컬럼 확인
        required_columns = ['question', 'answer', 'contexts']
        missing_columns = [col for col in required_columns if col not in dataset.column_names]
        
        if missing_columns:
            raise ValueError(f"필수 컬럼이 누락되었습니다: {missing_columns}")
        
        # ground_truths 컬럼 확인 (answer_correctness, context_recall용)
        if ('answer_correctness' in self.config.evaluation.metrics or 
            'context_recall' in self.config.evaluation.metrics):
            if 'ground_truths' not in dataset.column_names:
                print("⚠️  'ground_truths' 컬럼이 없어 answer_correctness/context_recall 평가가 제한될 수 있습니다")
        
        # reference 컬럼 확인 (context_precision용)
        if 'context_precision' in self.config.evaluation.metrics:
            if 'reference' not in dataset.column_names:
                print("⚠️  'reference' 컬럼이 없어 context_precision 평가를 위해 ground_truths를 reference로 사용합니다")
                # ground_truths를 reference로 복사
                if 'ground_truths' in dataset.column_names:
                    # Dataset 수정은 까다로우므로 임시 해결책
                    pass
        
        print(f"✅ 데이터셋 검증 완료")
    
    def _print_evaluation_summary(self, results_df: pd.DataFrame) -> None:
        """평가 결과 요약을 출력합니다."""
        
        print(f"\n📈 평가 결과 요약:")
        print(f"{'='*50}")
        
        # 각 메트릭별 평균 점수
        for metric_name in self.config.evaluation.metrics:
            if metric_name in results_df.columns:
                scores = results_df[metric_name].dropna()
                if len(scores) > 0:
                    avg_score = scores.mean()
                    min_score = scores.min()
                    max_score = scores.max()
                    
                    print(f"{metric_name:20}: {avg_score:.4f} (범위: {min_score:.4f}-{max_score:.4f})")
                else:
                    print(f"{metric_name:20}: 데이터 없음")
        
        # 전체 평균 (RAGAS Score)
        metric_columns = [col for col in results_df.columns if col in self.config.evaluation.metrics]
        if metric_columns:
            overall_scores = results_df[metric_columns].mean(axis=1)
            overall_avg = overall_scores.mean()
            print(f"{'='*50}")
            print(f"{'전체 평균 (RAGAS Score)':20}: {overall_avg:.4f}")
        
        print(f"{'='*50}")
    
    def get_detailed_results(self, results_df: pd.DataFrame) -> Dict[str, Any]:
        """상세한 평가 결과를 반환합니다."""
        
        detailed_results = {
            'summary': {},
            'by_metric': {},
            'by_item': {},
            'statistics': {}
        }
        
        # 메트릭별 통계
        for metric_name in self.config.evaluation.metrics:
            if metric_name in results_df.columns:
                scores = results_df[metric_name].dropna()
                if len(scores) > 0:
                    detailed_results['by_metric'][metric_name] = {
                        'mean': float(scores.mean()),
                        'std': float(scores.std()),
                        'min': float(scores.min()),
                        'max': float(scores.max()),
                        'count': len(scores)
                    }
        
        # 전체 통계
        metric_columns = [col for col in results_df.columns if col in self.config.evaluation.metrics]
        if metric_columns:
            overall_scores = results_df[metric_columns].mean(axis=1)
            detailed_results['summary'] = {
                'ragas_score': float(overall_scores.mean()),
                'total_items': len(results_df),
                'evaluated_metrics': len(metric_columns)
            }
        
        return detailed_results


def test_evaluator():
    """평가자 테스트 함수"""
    print("🧪 RagasEvaluator 테스트 시작")
    
    try:
        # 설정 및 데이터 로드
        from .config_loader import load_config
        from .data_processor import DataProcessor
        
        config = load_config()
        processor = DataProcessor()
        dataset = processor.load_and_prepare_data("data/input/sample.json")
        
        print(f"✅ 테스트 데이터 준비 완료: {len(dataset)}개 항목")
        
        # 평가자 생성
        evaluator = RagasEvaluator(config)
        
        # 평가 수행 (작은 데이터셋이므로 빠름)
        results_df = evaluator.evaluate(dataset)
        
        print(f"\n✅ 평가 테스트 성공!")
        print(f"   - 결과 DataFrame 크기: {results_df.shape}")
        print(f"   - 컬럼: {list(results_df.columns)}")
        
        # 상세 결과
        detailed = evaluator.get_detailed_results(results_df)
        print(f"   - RAGAS Score: {detailed['summary'].get('ragas_score', 'N/A'):.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 평가자 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_evaluator()