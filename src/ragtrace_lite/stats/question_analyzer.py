"""Individual question analysis and interpretation"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QuestionAnalysis:
    """개별 문항 분석 결과"""
    question_id: str
    question_text: str
    answer_text: str
    contexts: List[str]
    ground_truth: Optional[str]
    
    # 메트릭 점수
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float
    answer_correctness: float
    
    # 분석 결과
    overall_score: float
    status: str  # "good", "warning", "poor"
    issues: List[str]
    recommendations: List[str]
    interpretation: str


class QuestionAnalyzer:
    """개별 문항 분석기"""
    
    def __init__(self):
        self.thresholds = {
            'good': 0.8,
            'warning': 0.6,
            'poor': 0.0
        }
    
    def analyze_question(
        self,
        question_data: Dict[str, Any],
        metrics: Dict[str, float]
    ) -> QuestionAnalysis:
        """
        개별 문항 분석
        
        Args:
            question_data: 문항 데이터 (question, answer, contexts, ground_truth)
            metrics: 해당 문항의 메트릭 점수들
            
        Returns:
            문항 분석 결과
        """
        # 전체 점수 계산
        overall_score = np.mean(list(metrics.values()))
        
        # 상태 판정
        status = self._determine_status(overall_score)
        
        # 문제점 식별
        issues = self._identify_issues(metrics)
        
        # 개선 권장사항
        recommendations = self._generate_recommendations(metrics, issues)
        
        # 종합 해석
        interpretation = self._generate_interpretation(
            question_data, metrics, issues, status
        )
        
        return QuestionAnalysis(
            question_id=question_data.get('question_id', ''),
            question_text=question_data.get('question', ''),
            answer_text=question_data.get('answer', ''),
            contexts=question_data.get('contexts', []),
            ground_truth=question_data.get('ground_truth'),
            faithfulness=metrics.get('faithfulness', 0),
            answer_relevancy=metrics.get('answer_relevancy', 0),
            context_precision=metrics.get('context_precision', 0),
            context_recall=metrics.get('context_recall', 0),
            answer_correctness=metrics.get('answer_correctness', 0),
            overall_score=overall_score,
            status=status,
            issues=issues,
            recommendations=recommendations,
            interpretation=interpretation
        )
    
    def _determine_status(self, score: float) -> str:
        """점수에 따른 상태 판정"""
        if score >= self.thresholds['good']:
            return 'good'
        elif score >= self.thresholds['warning']:
            return 'warning'
        else:
            return 'poor'
    
    def _identify_issues(self, metrics: Dict[str, float]) -> List[str]:
        """문제점 식별"""
        issues = []
        
        # 충실도 문제
        if metrics.get('faithfulness', 1) < 0.6:
            issues.append("답변이 제공된 컨텍스트를 벗어난 내용 포함")
        
        # 관련성 문제
        if metrics.get('answer_relevancy', 1) < 0.6:
            issues.append("답변이 질문과 직접적인 관련성 부족")
        
        # 컨텍스트 정밀도 문제
        if metrics.get('context_precision', 1) < 0.6:
            issues.append("검색된 컨텍스트에 불필요한 정보 많음")
        
        # 컨텍스트 재현율 문제
        if metrics.get('context_recall', 1) < 0.6:
            issues.append("필요한 정보가 컨텍스트에서 누락됨")
        
        # 정확도 문제
        if metrics.get('answer_correctness', 1) < 0.5:
            issues.append("답변의 사실적 정확도가 낮음")
        
        # 복합 문제 분석
        if (metrics.get('context_recall', 1) > 0.8 and 
            metrics.get('answer_correctness', 1) < 0.5):
            issues.append("컨텍스트는 충분하나 답변 생성 품질 문제")
        
        if (metrics.get('context_precision', 1) < 0.5 and
            metrics.get('answer_relevancy', 1) < 0.5):
            issues.append("검색 및 생성 모두 개선 필요")
        
        return issues
    
    def _generate_recommendations(
        self, 
        metrics: Dict[str, float], 
        issues: List[str]
    ) -> List[str]:
        """개선 권장사항 생성"""
        recommendations = []
        
        # 충실도 개선
        if metrics.get('faithfulness', 1) < 0.6:
            recommendations.append(
                "프롬프트에 '제공된 컨텍스트만을 기반으로 답변' 지시 강화"
            )
        
        # 관련성 개선
        if metrics.get('answer_relevancy', 1) < 0.6:
            recommendations.append(
                "질문 이해 강화를 위한 프롬프트 엔지니어링 필요"
            )
        
        # 검색 개선
        if metrics.get('context_precision', 1) < 0.6:
            recommendations.append(
                "검색 쿼리 최적화 또는 청킹 전략 재검토"
            )
        
        if metrics.get('context_recall', 1) < 0.6:
            recommendations.append(
                "임베딩 모델 변경 또는 검색 개수(top-k) 증가 고려"
            )
        
        # 정확도 개선
        if metrics.get('answer_correctness', 1) < 0.5:
            recommendations.append(
                "LLM 파인튜닝 또는 더 강력한 모델로 변경 검토"
            )
        
        # 우선순위 지정
        if len(recommendations) > 1:
            recommendations.insert(0, f"우선순위: {self._get_priority_issue(metrics)}")
        
        return recommendations
    
    def _get_priority_issue(self, metrics: Dict[str, float]) -> str:
        """가장 우선적으로 개선해야 할 문제"""
        # 가장 낮은 점수의 메트릭 찾기
        min_metric = min(metrics.items(), key=lambda x: x[1])
        
        metric_names = {
            'faithfulness': '충실도',
            'answer_relevancy': '답변 관련성',
            'context_precision': '컨텍스트 정밀도',
            'context_recall': '컨텍스트 재현율',
            'answer_correctness': '답변 정확도'
        }
        
        return f"{metric_names.get(min_metric[0], min_metric[0])} 개선 ({min_metric[1]:.2f})"
    
    def _generate_interpretation(
        self,
        question_data: Dict[str, Any],
        metrics: Dict[str, float],
        issues: List[str],
        status: str
    ) -> str:
        """종합 해석 생성"""
        
        if status == 'good':
            base_text = "이 문항은 전반적으로 우수한 성능을 보입니다."
        elif status == 'warning':
            base_text = "이 문항은 일부 개선이 필요한 상태입니다."
        else:
            base_text = "이 문항은 전면적인 개선이 필요합니다."
        
        # 검색 vs 생성 분석
        retrieval_score = np.mean([
            metrics.get('context_precision', 0),
            metrics.get('context_recall', 0)
        ])
        generation_score = np.mean([
            metrics.get('faithfulness', 0),
            metrics.get('answer_relevancy', 0),
            metrics.get('answer_correctness', 0)
        ])
        
        if retrieval_score > generation_score + 0.2:
            analysis = "검색은 잘 되었으나 답변 생성에 문제가 있습니다."
        elif generation_score > retrieval_score + 0.2:
            analysis = "답변 생성 능력은 좋으나 관련 정보 검색이 부족합니다."
        else:
            analysis = "검색과 생성이 균형잡힌 성능을 보입니다."
        
        # 주요 문제점
        if issues:
            issues_text = f"주요 문제: {issues[0]}"
        else:
            issues_text = "특별한 문제점이 발견되지 않았습니다."
        
        return f"{base_text} {analysis} {issues_text}"
    
    def batch_analyze(
        self,
        questions_data: List[Dict[str, Any]],
        metrics_list: List[Dict[str, float]]
    ) -> pd.DataFrame:
        """여러 문항 일괄 분석"""
        
        analyses = []
        for q_data, metrics in zip(questions_data, metrics_list):
            analysis = self.analyze_question(q_data, metrics)
            analyses.append({
                'question': analysis.question_text[:50] + '...' if len(analysis.question_text) > 50 else analysis.question_text,
                'overall_score': analysis.overall_score,
                'status': analysis.status,
                'faithfulness': analysis.faithfulness,
                'answer_relevancy': analysis.answer_relevancy,
                'context_precision': analysis.context_precision,
                'context_recall': analysis.context_recall,
                'answer_correctness': analysis.answer_correctness,
                'main_issue': analysis.issues[0] if analysis.issues else 'None',
                'priority_action': analysis.recommendations[0] if analysis.recommendations else 'None'
            })
        
        df = pd.DataFrame(analyses)
        
        # 요약 통계 추가
        df['rank'] = df['overall_score'].rank(ascending=False, method='dense')
        
        return df
    
    def identify_patterns(self, analyses_df: pd.DataFrame) -> Dict[str, Any]:
        """문항들 간의 패턴 식별"""
        
        patterns = {
            'overall_stats': {
                'mean_score': analyses_df['overall_score'].mean(),
                'std_score': analyses_df['overall_score'].std(),
                'min_score': analyses_df['overall_score'].min(),
                'max_score': analyses_df['overall_score'].max()
            },
            'status_distribution': analyses_df['status'].value_counts().to_dict(),
            'common_issues': {},
            'metric_correlations': {}
        }
        
        # 공통 문제점 분석
        issue_counts = {}
        for issues_str in analyses_df['main_issue']:
            if issues_str != 'None':
                issue_counts[issues_str] = issue_counts.get(issues_str, 0) + 1
        
        patterns['common_issues'] = sorted(
            issue_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # 메트릭 간 상관관계
        metric_cols = ['faithfulness', 'answer_relevancy', 'context_precision', 
                      'context_recall', 'answer_correctness']
        
        for metric in metric_cols:
            if metric in analyses_df.columns:
                patterns['metric_correlations'][metric] = {
                    'vs_overall': analyses_df[metric].corr(analyses_df['overall_score'])
                }
        
        # 최악/최고 문항 식별
        patterns['worst_questions'] = analyses_df.nsmallest(3, 'overall_score')[
            ['question', 'overall_score', 'main_issue']
        ].to_dict('records')
        
        patterns['best_questions'] = analyses_df.nlargest(3, 'overall_score')[
            ['question', 'overall_score']
        ].to_dict('records')
        
        return patterns
    
    def generate_improvement_plan(self, patterns: Dict[str, Any]) -> List[str]:
        """패턴 기반 개선 계획 생성"""
        
        plan = []
        
        # 전체 성능 기반
        mean_score = patterns['overall_stats']['mean_score']
        if mean_score < 0.5:
            plan.append("🚨 긴급: 전체적인 시스템 재검토 필요")
        elif mean_score < 0.7:
            plan.append("⚠️ 주의: 단계적 개선 전략 수립 필요")
        else:
            plan.append("✅ 양호: 세부 최적화에 집중")
        
        # 공통 문제 기반
        if patterns['common_issues']:
            top_issue = patterns['common_issues'][0][0]
            count = patterns['common_issues'][0][1]
            plan.append(f"1. 최우선 개선: {top_issue} ({count}개 문항)")
        
        # 상관관계 기반
        correlations = patterns['metric_correlations']
        weak_correlation = min(
            correlations.items(), 
            key=lambda x: x[1]['vs_overall']
        )
        
        if weak_correlation[1]['vs_overall'] < 0.5:
            plan.append(f"2. {weak_correlation[0]} 메트릭 개선 집중")
        
        # 최악 문항 개선
        if patterns['worst_questions']:
            plan.append(f"3. 하위 {len(patterns['worst_questions'])}개 문항 집중 개선")
        
        return plan