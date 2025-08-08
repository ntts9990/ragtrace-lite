"""윈도우 기반 통계 비교 분석"""

import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ComparisonResult:
    """비교 결과 데이터 클래스"""
    window_a: Dict
    window_b: Dict
    metric_name: str
    stats_a: Dict
    stats_b: Dict
    test_type: str
    statistic: float
    p_value: float
    significant: bool
    cohens_d: float
    effect_size: str
    confidence_interval_a: Tuple[float, float]
    confidence_interval_b: Tuple[float, float]
    ci_overlap: bool
    improvement: float
    improvement_pct: float
    warnings: List[str]


class WindowComparator:
    """시간 윈도우 기반 통계 비교"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def compare_windows(
        self,
        window_a: Tuple[str, str],
        window_b: Tuple[str, str],
        metric: str = 'ragas_score',
        env_filters: Optional[Dict[str, str]] = None,
        mode: str = 'run_mean',
        alpha: float = 0.05
    ) -> ComparisonResult:
        """
        두 시간 윈도우의 메트릭 비교
        
        Args:
            window_a: (start_date, end_date) for window A
            window_b: (start_date, end_date) for window B
            metric: 비교할 메트릭 이름
            env_filters: 환경 필터 조건
            mode: 'run_mean' (런 평균) or 'item_level' (항목 레벨)
            alpha: 유의수준
        
        Returns:
            ComparisonResult 객체
        """
        warnings = []
        
        # 윈도우 데이터 조회
        runs_a = self.db.get_runs_by_window(window_a[0], window_a[1], env_filters)
        runs_b = self.db.get_runs_by_window(window_b[0], window_b[1], env_filters)
        
        if not runs_a or not runs_b:
            raise ValueError(f"Insufficient data: Window A has {len(runs_a)} runs, Window B has {len(runs_b)} runs")
        
        # 윈도우 중첩 확인
        if self._check_window_overlap(window_a, window_b):
            warnings.append("Windows overlap - results may not be independent")
        
        # 메트릭 값 추출
        if mode == 'run_mean':
            values_a = self._get_run_means(runs_a, metric)
            values_b = self._get_run_means(runs_b, metric)
        else:
            raise NotImplementedError("Item-level comparison not yet implemented")
        
        if len(values_a) < 3 or len(values_b) < 3:
            warnings.append(f"Limited samples: A={len(values_a)}, B={len(values_b)}. Results may be unreliable.")
        
        # 기초 통계
        stats_a = self._calculate_stats(values_a)
        stats_b = self._calculate_stats(values_b)
        
        # 통계 검정
        test_result = self._perform_test(values_a, values_b, alpha)
        
        # 신뢰구간
        ci_a = self._bootstrap_ci(values_a, alpha)
        ci_b = self._bootstrap_ci(values_b, alpha)
        ci_overlap = self._check_ci_overlap(ci_a, ci_b)
        
        # 개선도 계산
        improvement = stats_b['mean'] - stats_a['mean']
        improvement_pct = (improvement / stats_a['mean'] * 100) if stats_a['mean'] != 0 else 0
        
        return ComparisonResult(
            window_a={'start': window_a[0], 'end': window_a[1], 'runs': len(runs_a)},
            window_b={'start': window_b[0], 'end': window_b[1], 'runs': len(runs_b)},
            metric_name=metric,
            stats_a=stats_a,
            stats_b=stats_b,
            test_type=test_result['test_type'],
            statistic=test_result['statistic'],
            p_value=test_result['p_value'],
            significant=test_result['significant'],
            cohens_d=test_result.get('cohens_d', 0),
            effect_size=test_result.get('effect_size', 'unknown'),
            confidence_interval_a=ci_a,
            confidence_interval_b=ci_b,
            ci_overlap=ci_overlap,
            improvement=improvement,
            improvement_pct=improvement_pct,
            warnings=warnings
        )
    
    def _check_window_overlap(
        self,
        window_a: Tuple[str, str],
        window_b: Tuple[str, str]
    ) -> bool:
        """윈도우 중첩 확인"""
        a_start, a_end = window_a
        b_start, b_end = window_b
        
        # 날짜 문자열 비교 (ISO 형식이므로 문자열 비교 가능)
        return not (a_end < b_start or b_end < a_start)
    
    def _get_run_means(self, runs: List[Dict], metric: str) -> np.ndarray:
        """런별 평균 메트릭 값 추출"""
        run_ids = [run['run_id'] for run in runs]
        
        if metric == 'ragas_score':
            # ragas_score는 이미 계산된 평균값
            values = [run['ragas_score'] for run in runs if run['ragas_score'] is not None]
        else:
            # 개별 메트릭은 summary 테이블에서 조회
            values = self.db.get_metric_values_for_runs(run_ids, metric)
        
        return np.array(values)
    
    def _calculate_stats(self, values: np.ndarray) -> Dict:
        """기초 통계량 계산"""
        if len(values) == 0:
            return {'mean': 0, 'std': 0, 'median': 0, 'q1': 0, 'q3': 0, 
                   'min': 0, 'max': 0, 'count': 0}
        
        return {
            'mean': float(np.mean(values)),
            'std': float(np.std(values, ddof=1)) if len(values) > 1 else 0,
            'median': float(np.median(values)),
            'q1': float(np.percentile(values, 25)),
            'q3': float(np.percentile(values, 75)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'count': len(values)
        }
    
    def _perform_test(
        self,
        values_a: np.ndarray,
        values_b: np.ndarray,
        alpha: float
    ) -> Dict:
        """단순화된 통계 검정 - Welch's t-test를 기본으로 사용"""
        result = {}
        
        if len(values_a) < 2 or len(values_b) < 2:
            result['test_type'] = 'insufficient_data'
            result['statistic'] = None
            result['p_value'] = None
            result['significant'] = None
            return result
        
        # Welch's t-test (기본 - 분산이 다른 두 그룹 비교에 적합)
        statistic, p_value = stats.ttest_ind(values_a, values_b, equal_var=False)
        result['test_type'] = "Welch's t-test"
        
        result['statistic'] = float(statistic) if statistic is not None else None
        result['p_value'] = float(p_value) if p_value is not None else None
        result['significant'] = p_value < alpha if p_value is not None else None
        
        # Cohen's d (효과 크기)
        if len(values_a) > 1 and len(values_b) > 1:
            pooled_std = np.sqrt((np.var(values_a, ddof=1) + np.var(values_b, ddof=1)) / 2)
            if pooled_std > 0:
                cohens_d = (np.mean(values_b) - np.mean(values_a)) / pooled_std
                result['cohens_d'] = float(cohens_d)
                result['effect_size'] = self._interpret_cohens_d(cohens_d)
        
        return result
    
    def _check_normality(self, values: np.ndarray) -> bool:
        """Shapiro-Wilk 정규성 검정"""
        if len(values) < 3:
            return False
        
        try:
            _, p_value = stats.shapiro(values)
            return p_value > 0.05
        except:
            return False
    
    def _interpret_cohens_d(self, d: float) -> str:
        """Cohen's d 해석"""
        abs_d = abs(d)
        if abs_d < 0.2:
            return 'negligible'
        elif abs_d < 0.5:
            return 'small'
        elif abs_d < 0.8:
            return 'medium'
        else:
            return 'large'
    
    def _bootstrap_ci(
        self,
        values: np.ndarray,
        alpha: float = 0.05,
        n_bootstrap: int = 10000
    ) -> Tuple[float, float]:
        """부트스트랩 신뢰구간 계산"""
        if len(values) < 2:
            mean = float(values[0]) if len(values) == 1 else 0
            return (mean, mean)
        
        # 부트스트랩 샘플링
        bootstrap_means = []
        n = len(values)
        
        np.random.seed(42)  # 재현성
        for _ in range(n_bootstrap):
            sample = np.random.choice(values, size=n, replace=True)
            bootstrap_means.append(np.mean(sample))
        
        # 백분위수 방법
        lower = np.percentile(bootstrap_means, (alpha/2) * 100)
        upper = np.percentile(bootstrap_means, (1 - alpha/2) * 100)
        
        return (float(lower), float(upper))
    
    def _check_ci_overlap(
        self,
        ci_a: Tuple[float, float],
        ci_b: Tuple[float, float]
    ) -> bool:
        """신뢰구간 중첩 여부"""
        return not (ci_a[1] < ci_b[0] or ci_b[1] < ci_a[0])