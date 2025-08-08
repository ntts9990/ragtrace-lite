"""Dashboard service layer using DatabaseManager"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import numpy as np
from datetime import datetime, timedelta
import json
from scipy import stats
import pandas as pd

# Add src path for imports  
sys.path.insert(0, str(Path(__file__).parent.parent))

from ragtrace_lite.db.manager import DatabaseManager
from ragtrace_lite.config.config_loader import get_config

logger = logging.getLogger(__name__)

class DashboardService:
    """Dashboard service layer that uses DatabaseManager instead of direct SQL"""
    
    def __init__(self):
        """Initialize service with unified configuration"""
        config = get_config()
        db_config = config._get_default_config()['database']
        self.db_manager = DatabaseManager(str(db_config['path']))
        logger.info(f"DashboardService initialized with DB: {self.db_manager.db_path}")
    
    def get_all_reports(self) -> List[Dict[str, Any]]:
        """Get all evaluation reports using the DatabaseManager"""
        try:
            # Use the updated db_manager method
            raw_reports = self.db_manager.get_all_runs(limit=100)
            
            reports = []
            for row in raw_reports:
                report = dict(row)
                # Format and round values for display
                for key, value in report.items():
                    if isinstance(value, float):
                        report[key] = round(value, 3)
                reports.append(report)
            
            logger.info(f"Retrieved {len(reports)} evaluation reports via db_manager")
            return reports
            
        except Exception as e:
            logger.error(f"Failed to get reports via db_manager: {e}")
            return []
    
    def get_time_series_stats(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get time series statistics with forecasting"""
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

            # Fetch runs using the db_manager
            runs = self.db_manager.get_runs_by_window(start_date, end_date)
            if not runs:
                return self._get_empty_time_series_stats()

            # Process data using pandas for efficient aggregation
            df = pd.DataFrame(runs)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date

            # Group by date and aggregate
            daily_stats = df.groupby('date').agg(
                avg_score=('ragas_score', 'mean'),
                count=('run_id', 'size'),
                avg_faithfulness=('faithfulness', 'mean'),
                avg_answer_relevancy=('answer_relevancy', 'mean'),
                avg_context_precision=('context_precision', 'mean'),
                avg_context_recall=('context_recall', 'mean'),
                avg_answer_correctness=('answer_correctness', 'mean')
            ).reset_index()

            # Process data for the chart
            dates = daily_stats['date'].astype(str).tolist()
            scores = daily_stats['avg_score'].fillna(0).tolist()
            counts = daily_stats['count'].tolist()

            metrics = {
                'faithfulness': daily_stats['avg_faithfulness'].fillna(0).tolist(),
                'answer_relevancy': daily_stats['avg_answer_relevancy'].fillna(0).tolist(),
                'context_precision': daily_stats['avg_context_precision'].fillna(0).tolist(),
                'context_recall': daily_stats['avg_context_recall'].fillna(0).tolist(),
                'answer_correctness': daily_stats['avg_answer_correctness'].fillna(0).tolist()
            }

            # Forecasting logic
            forecast = self._calculate_forecast(scores)

            result = {
                'dates': dates,
                'scores': scores,
                'counts': counts,
                'metrics': metrics,
                'forecast': forecast,
                'summary': {
                    'total_evaluations': sum(counts),
                    'avg_score': round(np.mean(scores), 3) if scores else 0,
                    'trend_direction': forecast['trend_direction']
                }
            }

            logger.info(f"Generated time series stats for {len(dates)} data points")
            return result

        except Exception as e:
            logger.error(f"Failed to get time series stats: {e}")
            return self._get_empty_time_series_stats()

    def _get_empty_time_series_stats(self) -> Dict[str, Any]:
        """Return a default empty structure for time series stats."""
        return {
            'dates': [],
            'scores': [],
            'counts': [],
            'metrics': {
                'faithfulness': [], 'answer_relevancy': [], 'context_precision': [],
                'context_recall': [], 'answer_correctness': []
            },
            'forecast': {'trend': 0, 'next_score': 0, 'confidence': 0, 'trend_direction': 'stable'},
            'summary': {'total_evaluations': 0, 'avg_score': 0, 'trend_direction': 'stable'}
        }

    def _calculate_forecast(self, scores: List[float]) -> Dict[str, Any]:
        """Calculates trend and forecast from a list of scores."""
        if len(scores) >= 2:
            x = np.arange(len(scores))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, scores)
            next_score = slope * len(scores) + intercept
            confidence = abs(r_value) * 100
            trend_direction = 'improving' if slope > 0.01 else 'declining' if slope < -0.01 else 'stable'
        else:
            slope, next_score, confidence = 0, scores[0] if scores else 0, 0
            trend_direction = 'stable'

        return {
            'trend': round(slope, 4),
            'next_score': round(next_score, 3),
            'confidence': round(confidence, 1),
            'trend_direction': trend_direction
        }
    
    def perform_ab_test(self, group_a_ids: List[str], group_b_ids: List[str]) -> Dict[str, Any]:
        """Perform A/B statistical test between two groups"""
        try:
            # Fetch runs for both groups using the db_manager
            group_a_runs = [self.db_manager.load_evaluation_model(run_id) for run_id in group_a_ids]
            group_b_runs = [self.db_manager.load_evaluation_model(run_id) for run_id in group_b_ids]

            # Filter out None values if a run was not found
            group_a_runs = [run for run in group_a_runs if run]
            group_b_runs = [run for run in group_b_runs if run]

            if not group_a_runs or not group_b_runs:
                return {'error': 'Insufficient data for A/B testing. At least one run from each group must be valid.'}

            # Extract metric scores
            group_a_metrics = self._extract_metrics_from_runs(group_a_runs)
            group_b_metrics = self._extract_metrics_from_runs(group_b_runs)

            # Perform statistical tests
            results = {}
            for metric in group_a_metrics.keys():
                a_values = group_a_metrics[metric]
                b_values = group_b_metrics[metric]

                if not a_values or not b_values:
                    continue

                # t-test
                t_stat, p_value = stats.ttest_ind(a_values, b_values, equal_var=False)  # Welch's t-test

                # Effect size (Cohen's d)
                cohens_d = self._calculate_cohens_d(a_values, b_values)

                results[metric] = {
                    'group_a': {
                        'mean': round(np.mean(a_values), 3),
                        'std': round(np.std(a_values), 3),
                        'count': len(a_values)
                    },
                    'group_b': {
                        'mean': round(np.mean(b_values), 3),
                        'std': round(np.std(b_values), 3),
                        'count': len(b_values)
                    },
                    'statistics': {
                        't_statistic': round(t_stat, 3),
                        'p_value': round(p_value, 3),
                        'cohens_d': round(cohens_d, 3),
                        'significant': p_value < 0.05
                    }
                }
            
            logger.info(f"A/B test completed for {len(group_a_runs)} vs {len(group_b_runs)} runs")
            return results

        except Exception as e:
            logger.error(f"A/B test failed: {e}")
            return {'error': f'A/B test failed: {str(e)}'}

    def _extract_metrics_from_runs(self, runs: List[Any]) -> Dict[str, List[float]]:
        """Helper to extract all metric scores from a list of evaluation runs."""
        metrics_data = {
            'ragas_score': [], 'faithfulness': [], 'answer_relevancy': [],
            'context_precision': [], 'context_recall': [], 'answer_correctness': []
        }
        for run in runs:
            if run and run.overall_metrics:
                metrics_data['ragas_score'].append(run.ragas_score)
                for key in metrics_data.keys():
                    if key != 'ragas_score' and hasattr(run.overall_metrics, key):
                        metrics_data[key].append(getattr(run.overall_metrics, key))
        return metrics_data

    def _calculate_cohens_d(self, x: List[float], y: List[float]) -> float:
        """Calculate Cohen's d for independent samples."""
        nx, ny = len(x), len(y)
        dof = nx + ny - 2
        pooled_std = np.sqrt(((nx - 1) * np.std(x, ddof=1) ** 2 + (ny - 1) * np.std(y, ddof=1) ** 2) / dof)
        return (np.mean(y) - np.mean(x)) / pooled_std if pooled_std > 0 else 0
    
    def get_question_details(self, run_id: str) -> List[Dict[str, Any]]:
        """Get individual question analysis using DatabaseManager"""
        try:
            evaluation = self.db_manager.load_evaluation_model(run_id)
            if not evaluation or not evaluation.items:
                logger.warning(f"No evaluation items found for run {run_id}, cannot provide details.")
                return []

            questions = []
            for item in evaluation.items:
                scores = item.metrics.to_dict() if item.metrics else {}
                question_data = {
                    'index': item.item_index,
                    'question': item.question,
                    'answer': item.answer,
                    'contexts': item.contexts,
                    'ground_truth': item.ground_truth or 'N/A',
                    'scores': {k: round(v, 3) for k, v in scores.items()},
                    'analysis': self._analyze_question_scores(scores),
                    'data_source': 'real_evaluation'
                }
                questions.append(question_data)

            logger.info(f"Retrieved {len(questions)} real evaluation items for run {run_id}")
            return questions

        except Exception as e:
            logger.error(f"Failed to get question details for {run_id}: {e}")
            return []
    
    def _generate_synthetic_ab_data(self, base_score: float, count: int) -> List[Dict[str, float]]:
        """Generate synthetic data for A/B testing when real data is missing"""
        synthetic_data = []
        
        for _ in range(count):
            # Add some realistic variation
            variation = np.random.normal(0, 0.1)
            
            scores = {
                'ragas_score': max(0.1, min(0.95, base_score + variation)),
                'faithfulness': max(0.1, min(0.95, base_score + variation * 0.8)),
                'answer_relevancy': max(0.1, min(0.95, base_score + variation * 1.2)),
                'context_precision': max(0.1, min(0.95, base_score + variation * 0.9)),
                'context_recall': max(0.1, min(0.95, base_score + variation * 1.1)),
                'answer_correctness': max(0.1, min(0.95, base_score + variation * 0.7))
            }
            synthetic_data.append(scores)
        
        return synthetic_data
    
    def _generate_synthetic_questions(self, run_id: str, conn) -> List[Dict[str, Any]]:
        """Generate synthetic questions when real evaluation items are not available"""
        try:
            # Get evaluation metadata
            cursor = conn.cursor()
            cursor.execute("""
                SELECT dataset_name, dataset_items, faithfulness, answer_relevancy,
                       context_precision, context_recall, answer_correctness
                FROM evaluations WHERE run_id = ?
            """, (run_id,))
            
            eval_data = cursor.fetchone()
            if not eval_data:
                return []
            
            dataset_name = eval_data[0] or 'unknown'
            dataset_items = eval_data[1] or 5
            
            # Base metrics from evaluation
            base_metrics = {
                'faithfulness': float(eval_data[2] or 0.5),
                'answer_relevancy': float(eval_data[3] or 0.5),
                'context_precision': float(eval_data[4] or 0.5),
                'context_recall': float(eval_data[5] or 0.5),
                'answer_correctness': float(eval_data[6] or 0.5)
            }
            
            # Generate questions based on dataset type
            questions = self._get_question_templates(dataset_name)
            
            # Generate synthetic question data
            synthetic_questions = []
            for i in range(min(dataset_items, len(questions['questions']))):
                # Add realistic variation to base metrics
                scores = {}
                for metric, base_value in base_metrics.items():
                    variation = np.random.normal(0, 0.08)  # 8% standard deviation
                    scores[metric] = max(0.2, min(0.98, base_value + variation))
                
                question_data = {
                    'index': i,
                    'question': questions['questions'][i],
                    'answer': questions['answers'][i],
                    'contexts': [questions['contexts'][i]],
                    'ground_truth': questions['ground_truths'][i],
                    'scores': {k: round(v, 3) for k, v in scores.items()},
                    'analysis': self._analyze_question_scores(scores),
                    'data_source': 'synthetic'
                }
                synthetic_questions.append(question_data)
            
            return synthetic_questions
            
        except Exception as e:
            logger.error(f"Failed to generate synthetic questions: {e}")
            return []
    
    def _get_question_templates(self, dataset_name: str) -> Dict[str, List[str]]:
        """Get question templates based on dataset name"""
        if 'korean' in dataset_name.lower():
            return {
                'questions': [
                    "인공지능의 주요 학습 방법에는 어떤 것들이 있나요?",
                    "RAG 시스템의 구성 요소는 무엇인가요?",
                    "딥러닝과 머신러닝의 차이점은 무엇인가요?",
                    "Transformer 모델의 주요 특징은?",
                    "프롬프트 엔지니어링의 주요 기법들은?",
                    "벡터 데이터베이스의 장점은 무엇인가요?",
                    "LLM의 환각 문제를 어떻게 해결하나요?",
                    "Fine-tuning과 프롬프팅의 차이는?",
                    "GPT와 BERT의 주요 차이점은?",
                    "메모리 효율적인 LLM 추론 방법은?"
                ],
                'answers': [
                    "지도학습, 비지도학습, 강화학습이 주요 방법입니다.",
                    "Retriever, Generator, Orchestrator가 핵심 구성 요소입니다.",
                    "딥러닝은 심층 신경망을 사용하는 머신러닝의 하위 분야입니다.",
                    "Self-Attention, 병렬처리, Encoder-Decoder 구조가 주요 특징입니다.",
                    "Zero-shot, Few-shot, Chain-of-Thought 등이 주요 기법입니다.",
                    "의미적 검색과 빠른 유사도 계산이 주요 장점입니다.",
                    "RAG, Temperature 조절, 팩트 체킹으로 해결할 수 있습니다.",
                    "Fine-tuning은 모델 수정, 프롬프팅은 입력 조정 방식입니다.",
                    "GPT는 생성, BERT는 이해에 특화된 모델입니다.",
                    "양자화, 프루닝, 증류 등으로 메모리를 절약할 수 있습니다."
                ],
                'contexts': [
                    "머신러닝은 데이터로부터 패턴을 학습하는 AI 기술입니다.",
                    "RAG(Retrieval-Augmented Generation)는 검색과 생성을 결합한 시스템입니다.",
                    "딥러닝은 인공신경망을 여러 층으로 쌓아 복잡한 패턴을 학습합니다.",
                    "Transformer는 어텐션 메커니즘 기반의 신경망 아키텍처입니다.",
                    "프롬프트 엔지니어링은 AI 모델의 성능을 최적화하는 기법입니다.",
                    "벡터 데이터베이스는 고차원 벡터 데이터를 효율적으로 저장합니다.",
                    "LLM 환각은 잘못된 정보를 그럴듯하게 생성하는 문제입니다.",
                    "모델 학습 방법에는 여러 가지 접근법이 있습니다.",
                    "다양한 언어 모델들이 각기 다른 특성을 가지고 있습니다.",
                    "효율적인 추론을 위한 다양한 최적화 기법들이 존재합니다."
                ],
                'ground_truths': [
                    "지도학습, 비지도학습, 강화학습",
                    "검색기, 생성기, 제어기",
                    "딥러닝은 머신러닝의 하위 분야",
                    "어텐션 메커니즘, 병렬처리",
                    "Few-shot, Chain-of-Thought",
                    "빠른 유사도 검색",
                    "RAG, 팩트 체킹",
                    "모델 수정 vs 입력 조정",
                    "생성형 vs 이해형",
                    "양자화, 프루닝"
                ]
            }
        else:
            return {
                'questions': [
                    "What are the main components of a RAG system?",
                    "How does transformer attention mechanism work?",
                    "What is the difference between supervised and unsupervised learning?",
                    "How do you evaluate the performance of a language model?",
                    "What are the best practices for prompt engineering?"
                ],
                'answers': [
                    "A RAG system consists of a retriever, generator, and orchestrator.",
                    "Attention allows models to focus on relevant parts of the input.",
                    "Supervised learning uses labeled data, unsupervised doesn't.",
                    "Performance is measured using metrics like perplexity and BLEU.",
                    "Use clear instructions, examples, and iterative refinement."
                ],
                'contexts': [
                    "RAG systems combine retrieval and generation for better responses.",
                    "Attention mechanisms are key to modern neural networks.",
                    "Machine learning has different paradigms for different problems.",
                    "Evaluation metrics help assess model quality.",
                    "Prompt design significantly affects model performance."
                ],
                'ground_truths': [
                    "Retriever, generator, orchestrator",
                    "Focusing on relevant input parts",
                    "Labeled vs unlabeled data",
                    "Perplexity, BLEU, accuracy",
                    "Clear instructions and examples"
                ]
            }
    
    def _analyze_question_scores(self, scores: Dict[str, float]) -> Dict[str, Any]:
        """Analyze question scores and provide insights"""
        avg_score = np.mean(list(scores.values()))
        
        # Categorize performance
        if avg_score >= 0.8:
            status = "우수"
            status_class = "excellent"
        elif avg_score >= 0.6:
            status = "보통"
            status_class = "good"
        else:
            status = "개선필요"
            status_class = "poor"
        
        # Find strengths and weaknesses
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        strength = sorted_scores[0][0]
        weakness = sorted_scores[-1][0]
        
        # Generate recommendations
        recommendations = []
        if scores.get('faithfulness', 0) < 0.6:
            recommendations.append("답변의 신뢰성을 개선하세요")
        if scores.get('answer_relevancy', 0) < 0.6:
            recommendations.append("질문과의 관련성을 높이세요")
        if scores.get('context_precision', 0) < 0.6:
            recommendations.append("컨텍스트의 정확성을 개선하세요")
        if scores.get('context_recall', 0) < 0.6:
            recommendations.append("더 포괄적인 컨텍스트를 제공하세요")
        if scores.get('answer_correctness', 0) < 0.6:
            recommendations.append("답변의 정확도를 높이세요")
        
        if not recommendations:
            recommendations.append("전반적으로 우수한 성능입니다")
        
        return {
            'status': status,
            'status_class': status_class,
            'avg_score': round(avg_score, 3),
            'strength': strength,
            'weakness': weakness,
            'recommendations': recommendations
        }