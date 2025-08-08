"""Statistical analysis interpreter using LLM"""

import logging
from typing import Dict, Any, Optional
from ..core.llm_adapter import LLMAdapter
from ..config.config_loader import get_config

logger = logging.getLogger(__name__)


class StatisticalInterpreter:
    """Interpret statistical analysis results using LLM"""
    
    def __init__(self, llm_config: Optional[Dict] = None):
        """
        Initialize interpreter with LLM configuration
        
        Args:
            llm_config: LLM configuration (uses default if None)
        """
        if llm_config is None:
            config_loader = get_config()
            llm_config = config_loader.get_llm_config()
        
        self.llm = LLMAdapter.from_config(llm_config)
        logger.info(f"Statistical interpreter initialized with {self.llm._llm_type}")
    
    def interpret_comparison(self, comparison_result: Any) -> str:
        """
        Interpret window comparison results
        
        Args:
            comparison_result: WindowComparisonResult object
            
        Returns:
            Natural language interpretation
        """
        # Build context for LLM
        context = self._build_comparison_context(comparison_result)
        
        prompt = f"""You are a data scientist analyzing RAG evaluation results. 
Please provide a concise, professional interpretation of the following statistical comparison between two time windows.

Context:
{context}

Provide your interpretation in the following structure:
1. Key Finding: One sentence summary of the main result
2. Statistical Significance: Explain what the p-value and effect size mean
3. Practical Implications: What this means for the RAG system's performance
4. Recommendation: Brief actionable advice based on the results

Keep the interpretation under 200 words and use clear, non-technical language where possible."""

        try:
            interpretation = self.llm.invoke(prompt)
            return interpretation.strip()
        except Exception as e:
            logger.error(f"Failed to generate interpretation: {e}")
            return self._get_fallback_interpretation(comparison_result)
    
    def interpret_metrics(self, metrics: Dict[str, float], dataset_name: str = "") -> str:
        """
        Interpret evaluation metrics
        
        Args:
            metrics: Dictionary of metric scores
            dataset_name: Name of the evaluated dataset
            
        Returns:
            Natural language interpretation
        """
        metrics_text = "\n".join([f"- {k}: {v:.3f}" for k, v in metrics.items()])
        
        prompt = f"""You are analyzing RAG evaluation metrics{f' for dataset "{dataset_name}"' if dataset_name else ''}.

Metrics:
{metrics_text}

Please provide a brief interpretation covering:
1. Overall Performance: How well is the RAG system performing?
2. Strengths: Which metrics show good performance (>0.7)?
3. Weaknesses: Which metrics need improvement (<0.5)?
4. Priority Actions: What should be improved first?

Metric meanings:
- faithfulness: How well the answer is grounded in the context (1.0 = perfect)
- answer_relevancy: How relevant the answer is to the question (1.0 = perfect)
- context_precision: Quality of retrieved context (1.0 = perfect)
- context_recall: Coverage of ground truth by context (1.0 = perfect)
- answer_correctness: Correctness compared to ground truth (1.0 = perfect)

Keep the interpretation under 150 words."""

        try:
            interpretation = self.llm.invoke(prompt)
            return interpretation.strip()
        except Exception as e:
            logger.error(f"Failed to generate metrics interpretation: {e}")
            return self._get_fallback_metrics_interpretation(metrics)
    
    def interpret_trend(self, trend_data: Dict[str, Any]) -> str:
        """
        Interpret performance trends over time
        
        Args:
            trend_data: Dictionary containing trend analysis data
            
        Returns:
            Natural language interpretation
        """
        prompt = f"""Analyze the following RAG system performance trend:

Period: {trend_data.get('start_date', 'N/A')} to {trend_data.get('end_date', 'N/A')}
Number of evaluations: {trend_data.get('num_runs', 0)}
Metric: {trend_data.get('metric', 'ragas_score')}

Statistics:
- Starting value: {trend_data.get('start_value', 0):.3f}
- Ending value: {trend_data.get('end_value', 0):.3f}
- Average: {trend_data.get('mean', 0):.3f}
- Std deviation: {trend_data.get('std', 0):.3f}
- Trend direction: {trend_data.get('trend', 'stable')}
- Change: {trend_data.get('change_pct', 0):.1f}%

Provide a brief interpretation covering:
1. Trend Summary: Is performance improving, declining, or stable?
2. Variability: Is performance consistent or volatile?
3. Outlook: What does this trend suggest for future performance?

Keep the interpretation under 100 words."""

        try:
            interpretation = self.llm.invoke(prompt)
            return interpretation.strip()
        except Exception as e:
            logger.error(f"Failed to generate trend interpretation: {e}")
            return self._get_fallback_trend_interpretation(trend_data)
    
    def _build_comparison_context(self, result) -> str:
        """Build context string for comparison interpretation"""
        lines = []
        
        # Basic information
        lines.append(f"Metric analyzed: {result.metric_name}")
        lines.append(f"Comparison type: {result.test_type}")
        lines.append(f"Significance level: α = {result.alpha}")
        
        # Window A statistics
        lines.append(f"\nWindow A ({result.window_a['start']} to {result.window_a['end']}):")
        lines.append(f"  - Sample size: {result.window_a['runs']} runs")
        lines.append(f"  - Mean: {result.stats_a['mean']:.4f}")
        lines.append(f"  - Std dev: {result.stats_a['std']:.4f}")
        lines.append(f"  - 95% CI: [{result.confidence_interval_a[0]:.4f}, {result.confidence_interval_a[1]:.4f}]")
        
        # Window B statistics
        lines.append(f"\nWindow B ({result.window_b['start']} to {result.window_b['end']}):")
        lines.append(f"  - Sample size: {result.window_b['runs']} runs")
        lines.append(f"  - Mean: {result.stats_b['mean']:.4f}")
        lines.append(f"  - Std dev: {result.stats_b['std']:.4f}")
        lines.append(f"  - 95% CI: [{result.confidence_interval_b[0]:.4f}, {result.confidence_interval_b[1]:.4f}]")
        
        # Results
        lines.append(f"\nResults:")
        lines.append(f"  - Change: {result.improvement:.4f} ({result.improvement_pct:+.1f}%)")
        lines.append(f"  - P-value: {result.p_value:.4f}" if result.p_value else "  - P-value: N/A")
        lines.append(f"  - Significant: {'Yes' if result.significant else 'No'}")
        
        if result.cohens_d is not None:
            lines.append(f"  - Effect size: {result.effect_size} (Cohen's d = {result.cohens_d:.3f})")
        
        if result.warnings:
            lines.append(f"\nWarnings: {', '.join(result.warnings)}")
        
        return "\n".join(lines)
    
    def _get_fallback_interpretation(self, result) -> str:
        """Fallback interpretation when LLM fails"""
        interpretation = []
        
        # Key finding
        if result.significant:
            direction = "improved" if result.improvement > 0 else "declined"
            interpretation.append(
                f"**Key Finding:** Window B shows a statistically significant "
                f"{abs(result.improvement_pct):.1f}% {direction} in {result.metric_name} "
                f"compared to Window A."
            )
        else:
            interpretation.append(
                f"**Key Finding:** No statistically significant difference in {result.metric_name} "
                f"was found between the two windows (p={result.p_value:.3f})."
            )
        
        # Statistical significance
        interpretation.append(
            f"\n**Statistical Significance:** The p-value of {result.p_value:.3f} "
            f"{'indicates' if result.significant else 'does not indicate'} "
            f"a significant difference at the {result.alpha} level."
        )
        
        if result.cohens_d is not None:
            interpretation.append(
                f"The effect size is {result.effect_size} (d={result.cohens_d:.2f})."
            )
        
        # Practical implications
        if result.significant and abs(result.improvement_pct) > 10:
            interpretation.append(
                f"\n**Practical Implications:** This {abs(result.improvement_pct):.1f}% change "
                f"represents a meaningful shift in system performance that warrants attention."
            )
        else:
            interpretation.append(
                "\n**Practical Implications:** The observed difference is not substantial enough "
                "to indicate a meaningful change in system behavior."
            )
        
        # Recommendation
        if result.significant and result.improvement < 0:
            interpretation.append(
                "\n**Recommendation:** Investigate recent changes that may have caused "
                "this performance degradation."
            )
        elif result.significant and result.improvement > 0:
            interpretation.append(
                "\n**Recommendation:** Document and maintain the improvements that led "
                "to this performance gain."
            )
        else:
            interpretation.append(
                "\n**Recommendation:** Continue monitoring performance; current variation "
                "appears to be within normal bounds."
            )
        
        return "\n".join(interpretation)
    
    def _get_fallback_metrics_interpretation(self, metrics: Dict[str, float]) -> str:
        """Fallback metrics interpretation when LLM fails"""
        interpretation = []
        
        # Calculate overall score
        overall = sum(metrics.values()) / len(metrics) if metrics else 0
        
        # Overall performance
        if overall >= 0.7:
            interpretation.append(f"**Overall Performance:** Good ({overall:.2f}/1.0)")
        elif overall >= 0.5:
            interpretation.append(f"**Overall Performance:** Moderate ({overall:.2f}/1.0)")
        else:
            interpretation.append(f"**Overall Performance:** Needs improvement ({overall:.2f}/1.0)")
        
        # Strengths and weaknesses
        strengths = [k for k, v in metrics.items() if v >= 0.7]
        weaknesses = [k for k, v in metrics.items() if v < 0.5]
        
        if strengths:
            interpretation.append(f"\n**Strengths:** {', '.join(strengths)}")
        
        if weaknesses:
            interpretation.append(f"\n**Weaknesses:** {', '.join(weaknesses)}")
        
        # Priority actions
        if weaknesses:
            lowest = min(metrics.items(), key=lambda x: x[1])
            interpretation.append(
                f"\n**Priority:** Focus on improving {lowest[0]} (currently {lowest[1]:.2f})"
            )
        else:
            interpretation.append("\n**Priority:** Maintain current performance levels")
        
        return "\n".join(interpretation)
    
    def _get_fallback_trend_interpretation(self, trend_data: Dict[str, Any]) -> str:
        """Fallback trend interpretation when LLM fails"""
        change_pct = trend_data.get('change_pct', 0)
        std = trend_data.get('std', 0)
        mean = trend_data.get('mean', 0)
        
        interpretation = []
        
        # Trend summary
        if abs(change_pct) < 5:
            interpretation.append("**Trend:** Performance is stable")
        elif change_pct > 0:
            interpretation.append(f"**Trend:** Performance improving ({change_pct:+.1f}%)")
        else:
            interpretation.append(f"**Trend:** Performance declining ({change_pct:.1f}%)")
        
        # Variability
        cv = (std / mean * 100) if mean > 0 else 0
        if cv < 10:
            interpretation.append("**Variability:** Consistent performance")
        elif cv < 20:
            interpretation.append("**Variability:** Moderate variation")
        else:
            interpretation.append("**Variability:** High variation")
        
        # Outlook
        if change_pct > 5:
            interpretation.append("**Outlook:** Positive trajectory")
        elif change_pct < -5:
            interpretation.append("**Outlook:** Needs intervention")
        else:
            interpretation.append("**Outlook:** Stable continuation expected")
        
        return " | ".join(interpretation)