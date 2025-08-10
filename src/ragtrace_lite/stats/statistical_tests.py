"""Core statistical testing functionality"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy import stats
from scipy.stats import power

logger = logging.getLogger(__name__)


@dataclass
class StatisticalTestResult:
    """Result of a statistical test"""
    test_name: str
    statistic: float
    p_value: float
    effect_size: float
    interpretation: str
    sample_sizes: Dict[str, int]
    confidence_interval: Optional[Tuple[float, float]] = None
    assumptions_met: Optional[Dict[str, bool]] = None
    recommendations: Optional[List[str]] = None


class StatisticalTestSuite:
    """Core statistical testing functionality"""
    
    def analyze_comparison(
        self,
        group_a: List[float],
        group_b: List[float],
        alpha: float = 0.05
    ) -> StatisticalTestResult:
        """
        Perform comprehensive statistical comparison between two groups
        
        Args:
            group_a: First group data
            group_b: Second group data
            alpha: Significance level
            
        Returns:
            Statistical test result with interpretation
        """
        # Select appropriate test
        test_type = self._select_test(group_a, group_b)
        
        # Perform the selected test
        if test_type == "t_test":
            result = self._perform_t_test(group_a, group_b, alpha)
        elif test_type == "welch":
            result = self._perform_welch_test(group_a, group_b, alpha)
        else:  # mann_whitney
            result = self._perform_mann_whitney(group_a, group_b, alpha)
        
        return result
    
    def _select_test(
        self,
        group_a: List[float],
        group_b: List[float]
    ) -> str:
        """Select appropriate statistical test based on data characteristics"""
        # Check sample sizes
        n_a, n_b = len(group_a), len(group_b)
        
        # For small samples, prefer non-parametric
        if n_a < 30 or n_b < 30:
            return "mann_whitney"
        
        # Check normality
        normal_a = self._check_normality(group_a)
        normal_b = self._check_normality(group_b)
        
        if not (normal_a and normal_b):
            return "mann_whitney"
        
        # Check variance equality
        equal_var = self._check_equal_variance(group_a, group_b)
        
        if equal_var:
            return "t_test"
        else:
            return "welch"
    
    def _check_normality(self, data: List[float]) -> bool:
        """Check if data follows normal distribution"""
        if len(data) < 3:
            return False
        
        try:
            _, p_value = stats.shapiro(data)
            return p_value > 0.05
        except:
            return False
    
    def _check_equal_variance(
        self,
        group_a: List[float],
        group_b: List[float]
    ) -> bool:
        """Check if two groups have equal variance"""
        try:
            _, p_value = stats.levene(group_a, group_b)
            return p_value > 0.05
        except:
            return False
    
    def _perform_t_test(
        self,
        group_a: List[float],
        group_b: List[float],
        alpha: float
    ) -> StatisticalTestResult:
        """Perform independent samples t-test"""
        t_stat, p_value = stats.ttest_ind(group_a, group_b)
        
        # Calculate effect size (Cohen's d)
        mean_a, mean_b = np.mean(group_a), np.mean(group_b)
        std_a, std_b = np.std(group_a, ddof=1), np.std(group_b, ddof=1)
        n_a, n_b = len(group_a), len(group_b)
        
        pooled_std = np.sqrt(((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2))
        cohens_d = (mean_b - mean_a) / pooled_std if pooled_std > 0 else 0
        
        # Confidence interval for mean difference
        se = pooled_std * np.sqrt(1/n_a + 1/n_b)
        df = n_a + n_b - 2
        t_crit = stats.t.ppf(1 - alpha/2, df)
        mean_diff = mean_b - mean_a
        ci = (mean_diff - t_crit * se, mean_diff + t_crit * se)
        
        return StatisticalTestResult(
            test_name="Independent t-test",
            statistic=t_stat,
            p_value=p_value,
            effect_size=cohens_d,
            interpretation="",  # Will be set by interpreter
            sample_sizes={"group_a": n_a, "group_b": n_b},
            confidence_interval=ci,
            assumptions_met={"normality": True, "equal_variance": True}
        )
    
    def _perform_welch_test(
        self,
        group_a: List[float],
        group_b: List[float],
        alpha: float
    ) -> StatisticalTestResult:
        """Perform Welch's t-test (unequal variance)"""
        t_stat, p_value = stats.ttest_ind(group_a, group_b, equal_var=False)
        
        # Calculate effect size
        mean_a, mean_b = np.mean(group_a), np.mean(group_b)
        std_a, std_b = np.std(group_a, ddof=1), np.std(group_b, ddof=1)
        n_a, n_b = len(group_a), len(group_b)
        
        # Use separate variances for effect size
        pooled_std = np.sqrt((std_a**2 + std_b**2) / 2)
        cohens_d = (mean_b - mean_a) / pooled_std if pooled_std > 0 else 0
        
        return StatisticalTestResult(
            test_name="Welch's t-test",
            statistic=t_stat,
            p_value=p_value,
            effect_size=cohens_d,
            interpretation="",
            sample_sizes={"group_a": n_a, "group_b": n_b},
            assumptions_met={"normality": True, "equal_variance": False}
        )
    
    def _perform_mann_whitney(
        self,
        group_a: List[float],
        group_b: List[float],
        alpha: float
    ) -> StatisticalTestResult:
        """Perform Mann-Whitney U test"""
        u_stat, p_value = stats.mannwhitneyu(group_a, group_b, alternative='two-sided')
        
        # Calculate effect size (rank biserial correlation)
        n_a, n_b = len(group_a), len(group_b)
        r = 1 - (2 * u_stat) / (n_a * n_b)
        
        return StatisticalTestResult(
            test_name="Mann-Whitney U test",
            statistic=u_stat,
            p_value=p_value,
            effect_size=r,
            interpretation="",
            sample_sizes={"group_a": n_a, "group_b": n_b},
            assumptions_met={"normality": False}
        )
    
    def perform_anova(
        self,
        groups: Dict[str, List[float]],
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Perform one-way ANOVA analysis
        
        Args:
            groups: Dictionary of group names to data
            alpha: Significance level
            
        Returns:
            ANOVA results with post-hoc tests if significant
        """
        # Prepare data for ANOVA
        data_lists = list(groups.values())
        
        # Perform ANOVA
        f_stat, p_value = stats.f_oneway(*data_lists)
        
        # Calculate effect size (eta squared)
        grand_mean = np.mean([val for group in data_lists for val in group])
        ss_between = sum(len(group) * (np.mean(group) - grand_mean)**2 for group in data_lists)
        ss_total = sum((val - grand_mean)**2 for group in data_lists for val in group)
        eta_squared = ss_between / ss_total if ss_total > 0 else 0
        
        results = {
            "f_statistic": f_stat,
            "p_value": p_value,
            "effect_size": eta_squared,
            "significant": p_value < alpha,
            "group_sizes": {name: len(data) for name, data in groups.items()}
        }
        
        # Perform post-hoc tests if significant
        if results["significant"] and len(groups) > 2:
            results["post_hoc"] = self._perform_post_hoc(groups, alpha)
        
        return results
    
    def _perform_post_hoc(
        self,
        groups: Dict[str, List[float]],
        alpha: float
    ) -> Dict[str, Any]:
        """Perform post-hoc pairwise comparisons with Bonferroni correction"""
        group_names = list(groups.keys())
        n_comparisons = len(group_names) * (len(group_names) - 1) // 2
        corrected_alpha = alpha / n_comparisons  # Bonferroni correction
        
        comparisons = {}
        for i, name1 in enumerate(group_names):
            for name2 in group_names[i+1:]:
                result = self.analyze_comparison(
                    groups[name1],
                    groups[name2],
                    corrected_alpha
                )
                comparisons[f"{name1}_vs_{name2}"] = {
                    "p_value": result.p_value,
                    "effect_size": result.effect_size,
                    "significant": result.p_value < corrected_alpha
                }
        
        return comparisons
    
    def calculate_sample_size(
        self,
        effect_size: float = 0.5,
        power: float = 0.8,
        alpha: float = 0.05
    ) -> int:
        """
        Calculate required sample size for given parameters
        
        Args:
            effect_size: Expected effect size (Cohen's d)
            power: Desired statistical power
            alpha: Significance level
            
        Returns:
            Required sample size per group
        """
        try:
            from scipy.stats import power as pwr
            analysis = pwr.TTestPower()
            sample_size = analysis.solve_power(
                effect_size=effect_size,
                power=power,
                alpha=alpha
            )
            return int(np.ceil(sample_size))
        except:
            # Fallback approximation
            z_alpha = stats.norm.ppf(1 - alpha/2)
            z_beta = stats.norm.ppf(power)
            n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
            return int(np.ceil(n))