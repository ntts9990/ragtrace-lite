"""RAGAS 평가 엔진"""

import os
from typing import Dict, List, Any, Optional
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness
)
import logging
from pathlib import Path



from .llm_adapter import LLMAdapter
from .embeddings_adapter import EmbeddingsAdapter
from ..config.config_loader import get_config

logger = logging.getLogger(__name__)


class Evaluator:
    """RAGAS 평가 실행기"""
    
    def __init__(self, llm_config: Optional[Dict] = None, embeddings_config: Optional[Dict] = None):
        """
        Args:
            llm_config: LLM 설정 (provider, api_key, model_name 등)
            embeddings_config: Embeddings 설정
        """
        config_loader = get_config()
        self.llm_config = llm_config or config_loader.get_llm_config()
        self.embeddings_config = embeddings_config or config_loader.get_embeddings_config()
        
        self.llm = None
        self.embeddings = None
        self.metrics = []
    
    
    
    def evaluate(
        self,
        dataset: Dataset,
        environment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        RAGAS 평가 실행
        
        Args:
            dataset: 평가할 데이터셋
            environment: 환경 조건
            
        Returns:
            결과 딕셔너리 (metrics, details)
        """
        # LLM 초기화
        self._setup_models()
        
        # 메트릭 선택
        self._select_metrics(dataset, environment)
        
        # 평가 실행
        logger.info(f"Running evaluation with {len(self.metrics)} metrics...")
        
        try:
            results = evaluate(
                dataset=dataset,
                metrics=self.metrics,
                llm=self.llm,
                embeddings=self.embeddings,
                raise_exceptions=False
            )
            
            # 결과 정리
            output = self._process_results(results)
            
            logger.info("Evaluation completed successfully")
            return output
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            raise RuntimeError(f"RAGAS evaluation failed: {e}")
    
    def _setup_models(self):
        """LLM 및 임베딩 인스턴스 생성"""
        self.llm = LLMAdapter.from_config(self.llm_config)
        logger.info(f"LLM initialized: {self.llm._llm_type}")
        
        # 설정 기반 임베딩 사용 (local or API)
        self.embeddings = EmbeddingsAdapter(self.embeddings_config)
        logger.info(f"Embeddings initialized: {self.embeddings.provider}")
    
    def _select_metrics(self, dataset: Dataset, environment: Dict):
        """단순화된 메트릭 선택: 3개 기본 + 2개 조건부"""
        
        # 기본 3개 메트릭 (항상 사용)
        self.metrics = [
            faithfulness,
            answer_relevancy,
            context_precision
        ]
        
        # ground_truth가 있을 때만 2개 추가
        if self._has_ground_truth(dataset):
            self.metrics.extend([
                context_recall,
                answer_correctness
            ])
        
        logger.info(f"Selected metrics: {[m.name for m in self.metrics]}")
    
    def _has_ground_truth(self, dataset: Dataset) -> bool:
        """ground_truth 존재 여부 확인"""
        if 'ground_truths' not in dataset.column_names:
            return False
        
        # 첫 번째 항목 확인
        first_item = dataset[0]
        ground_truths = first_item.get('ground_truths', [])
        
        return len(ground_truths) > 0 and ground_truths[0] != ""
    
    def _process_results(self, results: Any) -> Dict[str, Any]:
        """DataFrame 기반 안정적인 결과 처리"""
        import pandas as pd
        
        output = {
            'metrics': {},
            'details': []
        }
        
        # DataFrame으로 통일된 처리
        try:
            # 결과를 DataFrame으로 변환
            if hasattr(results, 'to_pandas'):
                df = results.to_pandas()
            elif hasattr(results, 'dataset'):
                df = pd.DataFrame(results.dataset)
            else:
                # 딕셔너리로부터 직접 생성
                df = pd.DataFrame([results])
            
            # 메트릭 점수 추출 (DataFrame에서)
            for metric in self.metrics:
                metric_name = metric.name
                if metric_name in df.columns:
                    # 평균값 계산 (여러 샘플의 경우)
                    score = df[metric_name].mean()
                    if pd.notna(score):
                        output['metrics'][metric_name] = float(score)
            
            # RAGAS 종합 점수 계산 (단순 평균)
            if output['metrics']:
                output['metrics']['ragas_score'] = sum(output['metrics'].values()) / len(output['metrics'])
            
            # 상세 결과 저장
            output['details'] = df.to_dict('records')
            
        except Exception as e:
            logger.warning(f"Failed to process with DataFrame: {e}", exc_info=True)
            # 폴백: 기본 처리
            for metric in self.metrics:
                metric_name = metric.name
                if hasattr(results, metric_name):
                    score = getattr(results, metric_name)
                    if score is not None:
                        output['metrics'][metric_name] = float(score)
        
        return output