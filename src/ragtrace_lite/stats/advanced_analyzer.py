"""Advanced statistical analysis for RAG evaluation"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Any, Tuple, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StatisticalTestResult:
    """통계 검정 결과"""
    test_name: str
    statistic: float
    p_value: float
    significant: bool
    effect_size: float
    confidence_interval: Tuple[float, float]
    interpretation: str
    power: Optional[float] = None
    assumptions_met: Optional[Dict[str, bool]] = None


class AdvancedStatisticalAnalyzer:
    """고급 통계 분석기"""
    
    def __init__(self, alpha: float = 0.05):
        """
        Args:
            alpha: 유의수준 (기본 0.05)
        """
        self.alpha = alpha
    
    def analyze_comparison(
        self, 
        group_a: List[float], 
        group_b: List[float],
        test_type: str = "auto"
    ) -> StatisticalTestResult:
        """
        두 그룹 비교 분석
        
        Args:
            group_a: 그룹 A 데이터
            group_b: 그룹 B 데이터
            test_type: 검정 방법 ("auto", "t-test", "mann-whitney", "welch")
        
        Returns:
            통계 검정 결과
        """
        if test_type == "auto":
            test_type = self._select_test(group_a, group_b)
        
        if test_type == "t-test":
            return self._perform_t_test(group_a, group_b)
        elif test_type == "mann-whitney":
            return self._perform_mann_whitney(group_a, group_b)
        elif test_type == "welch":
            return self._perform_welch_test(group_a, group_b)
        else:
            raise ValueError(f"Unknown test type: {test_type}")
    
    def _select_test(self, group_a: List[float], group_b: List[float]) -> str:
        """적절한 검정 방법 자동 선택"""
        
        # 샘플 크기 확인
        n_a, n_b = len(group_a), len(group_b)
        
        # 정규성 검정
        normal_a = self._check_normality(group_a) if n_a >= 8 else False
        normal_b = self._check_normality(group_b) if n_b >= 8 else False
        
        # 등분산성 검정
        equal_var = self._check_equal_variance(group_a, group_b)
        
        # 검정 방법 선택
        if normal_a and normal_b:
            if equal_var:
                return "t-test"
            else:
                return "welch"
        else:
            return "mann-whitney"
    
    def _check_normality(self, data: List[float]) -> bool:
        """정규성 검정 (Shapiro-Wilk)"""
        if len(data) < 3:
            return False
        
        try:
            _, p_value = stats.shapiro(data)
            return p_value > 0.05
        except:
            return False
    
    def _check_equal_variance(self, group_a: List[float], group_b: List[float]) -> bool:
        """등분산성 검정 (Levene)"""
        try:
            _, p_value = stats.levene(group_a, group_b)
            return p_value > 0.05
        except:
            return False
    
    def _perform_t_test(self, group_a: List[float], group_b: List[float]) -> StatisticalTestResult:
        """독립표본 t-검정"""
        t_stat, p_value = stats.ttest_ind(group_a, group_b)
        
        # 효과 크기 (Cohen's d)
        pooled_std = np.sqrt((np.var(group_a) + np.var(group_b)) / 2)
        effect_size = (np.mean(group_b) - np.mean(group_a)) / pooled_std if pooled_std > 0 else 0
        
        # 신뢰구간
        mean_diff = np.mean(group_b) - np.mean(group_a)
        se = pooled_std * np.sqrt(1/len(group_a) + 1/len(group_b))
        ci = (mean_diff - 1.96*se, mean_diff + 1.96*se)
        
        # 검정력 계산
        from statsmodels.stats.power import ttest_power
        try:
            power = ttest_power(effect_size, len(group_a), self.alpha, alternative='two-sided')
        except:
            power = None
        
        return StatisticalTestResult(
            test_name="Independent t-test",
            statistic=float(t_stat),
            p_value=float(p_value),
            significant=p_value < self.alpha,
            effect_size=float(effect_size),
            confidence_interval=ci,
            interpretation=self._interpret_result(p_value, effect_size),
            power=power
        )
    
    def _perform_welch_test(self, group_a: List[float], group_b: List[float]) -> StatisticalTestResult:
        """Welch's t-test (등분산 가정 없음)"""
        t_stat, p_value = stats.ttest_ind(group_a, group_b, equal_var=False)
        
        # 효과 크기
        effect_size = (np.mean(group_b) - np.mean(group_a)) / np.sqrt((np.var(group_a) + np.var(group_b)) / 2)
        
        # 신뢰구간
        mean_diff = np.mean(group_b) - np.mean(group_a)
        se = np.sqrt(np.var(group_a)/len(group_a) + np.var(group_b)/len(group_b))
        ci = (mean_diff - 1.96*se, mean_diff + 1.96*se)
        
        return StatisticalTestResult(
            test_name="Welch's t-test",
            statistic=float(t_stat),
            p_value=float(p_value),
            significant=p_value < self.alpha,
            effect_size=float(effect_size),
            confidence_interval=ci,
            interpretation=self._interpret_result(p_value, effect_size),
            power=None
        )
    
    def _perform_mann_whitney(self, group_a: List[float], group_b: List[float]) -> StatisticalTestResult:
        """Mann-Whitney U 검정 (비모수)"""
        u_stat, p_value = stats.mannwhitneyu(group_a, group_b, alternative='two-sided')
        
        # 효과 크기 (rank-biserial correlation)
        n_a, n_b = len(group_a), len(group_b)
        effect_size = 1 - (2*u_stat) / (n_a * n_b)
        
        # 신뢰구간 (중앙값 차이)
        median_diff = np.median(group_b) - np.median(group_a)
        # Bootstrap CI would be more accurate
        ci = (median_diff - 0.5, median_diff + 0.5)  # Simplified
        
        return StatisticalTestResult(
            test_name="Mann-Whitney U test",
            statistic=float(u_stat),
            p_value=float(p_value),
            significant=p_value < self.alpha,
            effect_size=float(effect_size),
            confidence_interval=ci,
            interpretation=self._interpret_result(p_value, effect_size, nonparametric=True),
            power=None
        )
    
    def _interpret_result(self, p_value: float, effect_size: float, nonparametric: bool = False) -> str:
        """결과 해석"""
        
        # 통계적 유의성
        if p_value < 0.001:
            sig_text = "매우 강한 통계적 유의성 (p < 0.001)"
        elif p_value < 0.01:
            sig_text = "강한 통계적 유의성 (p < 0.01)"
        elif p_value < 0.05:
            sig_text = "통계적으로 유의미 (p < 0.05)"
        else:
            sig_text = "통계적으로 유의미하지 않음"
        
        # 효과 크기 해석
        if nonparametric:
            # Rank-biserial correlation
            if abs(effect_size) < 0.1:
                effect_text = "무시할 수준"
            elif abs(effect_size) < 0.3:
                effect_text = "작은 효과"
            elif abs(effect_size) < 0.5:
                effect_text = "중간 효과"
            else:
                effect_text = "큰 효과"
        else:
            # Cohen's d
            if abs(effect_size) < 0.2:
                effect_text = "무시할 수준"
            elif abs(effect_size) < 0.5:
                effect_text = "작은 효과"
            elif abs(effect_size) < 0.8:
                effect_text = "중간 효과"
            else:
                effect_text = "큰 효과"
        
        return f"{sig_text}, 효과 크기: {effect_text}"
    
    def perform_anova(self, *groups) -> Dict[str, Any]:
        """일원분산분석 (3개 이상 그룹 비교)"""
        f_stat, p_value = stats.f_oneway(*groups)
        
        # 효과 크기 (eta-squared)
        grand_mean = np.mean(np.concatenate(groups))
        ss_between = sum(len(g) * (np.mean(g) - grand_mean)**2 for g in groups)
        ss_total = sum((x - grand_mean)**2 for g in groups for x in g)
        eta_squared = ss_between / ss_total if ss_total > 0 else 0
        
        result = {
            'test': 'One-way ANOVA',
            'f_statistic': float(f_stat),
            'p_value': float(p_value),
            'significant': p_value < self.alpha,
            'eta_squared': float(eta_squared),
            'interpretation': self._interpret_anova(p_value, eta_squared)
        }
        
        # 사후 검정 (Post-hoc)
        if p_value < self.alpha and len(groups) > 2:
            result['post_hoc'] = self._perform_post_hoc(groups)
        
        return result
    
    def _interpret_anova(self, p_value: float, eta_squared: float) -> str:
        """ANOVA 결과 해석"""
        if p_value < self.alpha:
            effect = "큰" if eta_squared > 0.14 else "중간" if eta_squared > 0.06 else "작은"
            return f"그룹 간 유의미한 차이 존재 (p={p_value:.4f}), {effect} 효과 크기 (η²={eta_squared:.3f})"
        else:
            return f"그룹 간 유의미한 차이 없음 (p={p_value:.4f})"
    
    def _perform_post_hoc(self, groups: Tuple) -> List[Dict]:
        """Tukey HSD 사후 검정"""
        from statsmodels.stats.multicomp import pairwise_tukeyhsd
        
        # 데이터 준비
        data = []
        labels = []
        for i, group in enumerate(groups):
            data.extend(group)
            labels.extend([f"Group{i+1}"] * len(group))
        
        # Tukey HSD
        tukey = pairwise_tukeyhsd(data, labels, alpha=self.alpha)
        
        results = []
        for row in tukey.summary().data[1:]:  # Skip header
            results.append({
                'group1': row[0],
                'group2': row[1],
                'mean_diff': float(row[2]),
                'p_adj': float(row[5]),
                'reject': row[6]
            })
        
        return results
    
    def calculate_sample_size(
        self,
        effect_size: float,
        power: float = 0.8,
        alpha: float = 0.05
    ) -> int:
        """필요한 샘플 크기 계산"""
        from statsmodels.stats.power import tt_solve_power
        
        try:
            n = tt_solve_power(
                effect_size=effect_size,
                alpha=alpha,
                power=power,
                alternative='two-sided'
            )
            return int(np.ceil(n))
        except:
            return 30  # Default fallback
    
    def perform_correlation_analysis(self, x: List[float], y: List[float]) -> Dict[str, Any]:
        """상관 분석"""
        
        # Pearson 상관계수
        pearson_r, pearson_p = stats.pearsonr(x, y)
        
        # Spearman 상관계수
        spearman_r, spearman_p = stats.spearmanr(x, y)
        
        # Kendall's tau
        kendall_tau, kendall_p = stats.kendalltau(x, y)
        
        return {
            'pearson': {
                'correlation': float(pearson_r),
                'p_value': float(pearson_p),
                'interpretation': self._interpret_correlation(pearson_r)
            },
            'spearman': {
                'correlation': float(spearman_r),
                'p_value': float(spearman_p),
                'interpretation': self._interpret_correlation(spearman_r)
            },
            'kendall': {
                'correlation': float(kendall_tau),
                'p_value': float(kendall_p),
                'interpretation': self._interpret_correlation(kendall_tau)
            }
        }
    
    def _interpret_correlation(self, r: float) -> str:
        """상관계수 해석"""
        abs_r = abs(r)
        
        if abs_r < 0.1:
            strength = "무시할 수준"
        elif abs_r < 0.3:
            strength = "약한"
        elif abs_r < 0.5:
            strength = "중간"
        elif abs_r < 0.7:
            strength = "강한"
        else:
            strength = "매우 강한"
        
        direction = "양의" if r > 0 else "음의"
        
        return f"{strength} {direction} 상관관계 (r={r:.3f})"
    
    def detect_outliers(self, data: List[float], method: str = "iqr") -> Dict[str, Any]:
        """이상치 탐지"""
        
        if method == "iqr":
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = [x for x in data if x < lower_bound or x > upper_bound]
            
        elif method == "zscore":
            z_scores = np.abs(stats.zscore(data))
            outliers = [data[i] for i, z in enumerate(z_scores) if z > 3]
            
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return {
            'method': method,
            'outliers': outliers,
            'outlier_count': len(outliers),
            'outlier_percentage': len(outliers) / len(data) * 100 if data else 0,
            'bounds': (lower_bound, upper_bound) if method == "iqr" else None
        }