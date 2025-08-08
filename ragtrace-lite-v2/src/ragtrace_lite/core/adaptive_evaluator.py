"""Adaptive Evaluator with dynamic batch size handling"""

import logging
from typing import Dict, Any, Optional
from datasets import Dataset
import time

from .evaluator import Evaluator

logger = logging.getLogger(__name__)


class AdaptiveEvaluator(Evaluator):
    """배치 크기를 동적으로 조정하는 평가기"""
    
    def __init__(self, llm_config: Optional[Dict] = None):
        super().__init__(llm_config)
        self.initial_batch_size = 5
        self.min_batch_size = 1
        self.current_batch_size = self.initial_batch_size
    
    def evaluate(
        self,
        dataset: Dataset,
        environment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adaptive batch size를 사용한 RAGAS 평가 실행
        
        Args:
            dataset: 평가할 데이터셋
            environment: 환경 조건
            
        Returns:
            결과 딕셔너리 (metrics, details)
        """
        # LLM 초기화
        self._setup_llm()
        
        # 메트릭 선택
        self._select_metrics(dataset, environment)
        
        # 데이터셋 크기 확인
        total_items = len(dataset)
        logger.info(f"Starting adaptive evaluation with {total_items} items")
        
        # 작은 데이터셋은 그대로 처리
        if total_items <= self.min_batch_size:
            return super().evaluate(dataset, environment)
        
        # 배치 처리
        all_results = []
        processed = 0
        self.current_batch_size = min(self.initial_batch_size, total_items)
        
        while processed < total_items:
            batch_size = min(self.current_batch_size, total_items - processed)
            batch_end = min(processed + batch_size, total_items)
            
            # 배치 데이터셋 생성
            batch_data = dataset.select(range(processed, batch_end))
            
            logger.info(f"Processing batch: items {processed+1}-{batch_end} (batch size: {batch_size})")
            
            try:
                # 배치 평가 실행
                batch_results = super().evaluate(batch_data, environment)
                all_results.append(batch_results)
                
                # 성공 시 배치 크기 점진적 증가 (최대 initial_batch_size까지)
                if self.current_batch_size < self.initial_batch_size:
                    self.current_batch_size = min(self.current_batch_size + 1, self.initial_batch_size)
                    logger.debug(f"Batch size increased to {self.current_batch_size}")
                
                processed = batch_end
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Rate limit 또는 오버로드 에러 감지
                if any(keyword in error_msg for keyword in ['429', 'rate', 'too many', 'overload', 'timeout']):
                    # 배치 크기 감소
                    if self.current_batch_size > self.min_batch_size:
                        self.current_batch_size = max(self.min_batch_size, self.current_batch_size // 2)
                        logger.warning(f"Rate limit/overload detected. Reducing batch size to {self.current_batch_size}")
                        
                        # 추가 대기
                        wait_time = 10.0
                        logger.info(f"Waiting {wait_time}s before retry with smaller batch...")
                        time.sleep(wait_time)
                        continue
                    else:
                        # 최소 배치 크기에서도 실패하면 개별 항목 건너뛰기
                        logger.error(f"Failed even with minimum batch size. Skipping item {processed+1}")
                        processed += 1
                        
                        # 빈 결과 추가
                        all_results.append({
                            'metrics': {m.name: 0.0 for m in self.metrics},
                            'details': []
                        })
                else:
                    # 다른 에러는 재시도
                    logger.warning(f"Batch evaluation failed: {e}. Retrying...")
                    time.sleep(5.0)
                    continue
        
        # 결과 병합
        return self._merge_results(all_results)
    
    def _merge_results(self, results_list: list) -> Dict[str, Any]:
        """여러 배치 결과를 병합"""
        if not results_list:
            return {'metrics': {}, 'details': []}
        
        # 첫 번째 결과를 기준으로
        merged = {
            'metrics': {},
            'details': []
        }
        
        # 메트릭별 점수 수집
        metric_scores = {}
        for result in results_list:
            for metric_name, score in result.get('metrics', {}).items():
                if metric_name not in metric_scores:
                    metric_scores[metric_name] = []
                if score is not None:
                    metric_scores[metric_name].append(score)
        
        # 평균 계산
        for metric_name, scores in metric_scores.items():
            if scores:
                merged['metrics'][metric_name] = sum(scores) / len(scores)
        
        # RAGAS 종합 점수
        if merged['metrics']:
            merged['metrics']['ragas_score'] = sum(merged['metrics'].values()) / len(merged['metrics'])
        
        # 상세 결과 병합
        for result in results_list:
            merged['details'].extend(result.get('details', []))
        
        return merged