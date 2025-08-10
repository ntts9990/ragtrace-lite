"""Report generation and synthetic data service for dashboard"""

import logging
import random
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ReportService:
    """Generate synthetic data and templated content for reports"""
    
    def __init__(self):
        """Initialize report service"""
        self.question_templates = self._get_question_templates()
    
    def generate_synthetic_ab_data(
        self, 
        num_runs: int = 10, 
        improvement: float = 0.1
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Generate synthetic A/B test data for demo purposes
        
        Args:
            num_runs: Number of runs per group
            improvement: Performance improvement for group B
            
        Returns:
            Tuple of (group_a_data, group_b_data)
        """
        base_metrics = {
            'faithfulness': 0.75,
            'answer_relevancy': 0.70,
            'context_precision': 0.72
        }
        
        group_a = []
        group_b = []
        
        for i in range(num_runs):
            # Group A (baseline)
            run_a = {
                'run_id': f'synthetic_a_{i}',
                'timestamp': (datetime.now() - timedelta(hours=i)).isoformat()
            }
            for metric, base_value in base_metrics.items():
                # Add random variation
                run_a[f'metric_{metric}'] = base_value + random.uniform(-0.1, 0.1)
            group_a.append(run_a)
            
            # Group B (improved)
            run_b = {
                'run_id': f'synthetic_b_{i}',
                'timestamp': (datetime.now() - timedelta(hours=i)).isoformat()
            }
            for metric, base_value in base_metrics.items():
                # Add improvement plus random variation
                run_b[f'metric_{metric}'] = base_value + improvement + random.uniform(-0.05, 0.05)
            group_b.append(run_b)
        
        return group_a, group_b
    
    def generate_synthetic_questions(
        self, 
        num_questions: int = 20,
        language: str = 'ko'
    ) -> List[Dict[str, Any]]:
        """
        Generate synthetic question-answer pairs for testing
        
        Args:
            num_questions: Number of questions to generate
            language: Language for questions ('ko' or 'en')
            
        Returns:
            List of synthetic Q&A items
        """
        templates = self.question_templates.get(language, self.question_templates['en'])
        questions = []
        
        for i in range(num_questions):
            template = random.choice(templates)
            
            # Generate scores
            base_score = random.uniform(0.5, 0.95)
            metrics = {
                'faithfulness': base_score + random.uniform(-0.1, 0.1),
                'answer_relevancy': base_score + random.uniform(-0.1, 0.1),
                'context_precision': base_score + random.uniform(-0.1, 0.1)
            }
            
            # Ensure scores are in valid range
            for key in metrics:
                metrics[key] = max(0.0, min(1.0, metrics[key]))
            
            questions.append({
                'question': template['question'],
                'answer': template['answer'],
                'contexts': template.get('contexts', []),
                'metrics': metrics,
                'ground_truth': template.get('ground_truth', template['answer'])
            })
        
        return questions
    
    def _get_question_templates(self) -> Dict[str, List[Dict]]:
        """Get question templates for different languages"""
        return {
            'ko': [
                {
                    'question': 'RAG란 무엇인가요?',
                    'answer': 'RAG(Retrieval-Augmented Generation)는 검색과 생성을 결합한 AI 기술입니다.',
                    'contexts': ['RAG는 외부 지식을 활용하여 더 정확한 답변을 생성합니다.'],
                    'ground_truth': 'RAG는 검색 증강 생성 기술입니다.'
                },
                {
                    'question': 'LLM의 한계점은 무엇인가요?',
                    'answer': 'LLM은 학습 데이터의 시점 한계와 환각 현상이 주요 문제입니다.',
                    'contexts': ['대규모 언어 모델은 최신 정보를 반영하지 못하는 한계가 있습니다.'],
                    'ground_truth': '최신 정보 부족과 환각이 주요 한계입니다.'
                },
                {
                    'question': '벡터 데이터베이스의 역할은?',
                    'answer': '벡터 데이터베이스는 임베딩된 문서를 저장하고 유사도 검색을 수행합니다.',
                    'contexts': ['벡터 DB는 고차원 벡터를 효율적으로 저장하고 검색합니다.'],
                    'ground_truth': '임베딩 저장과 유사도 검색을 담당합니다.'
                },
                {
                    'question': '프롬프트 엔지니어링이란?',
                    'answer': '프롬프트 엔지니어링은 AI 모델에게 효과적인 지시문을 작성하는 기술입니다.',
                    'contexts': ['좋은 프롬프트는 AI의 성능을 크게 향상시킬 수 있습니다.'],
                    'ground_truth': 'AI 모델을 위한 효과적인 지시문 작성 기술입니다.'
                },
                {
                    'question': '파인튜닝과 RAG의 차이점은?',
                    'answer': '파인튜닝은 모델 자체를 수정하지만, RAG는 외부 지식을 활용합니다.',
                    'contexts': ['파인튜닝은 모델 가중치를 조정하는 반면, RAG는 검색을 통해 정보를 보강합니다.'],
                    'ground_truth': '모델 수정 vs 외부 지식 활용의 차이입니다.'
                }
            ],
            'en': [
                {
                    'question': 'What is RAG?',
                    'answer': 'RAG (Retrieval-Augmented Generation) is an AI technique combining retrieval and generation.',
                    'contexts': ['RAG uses external knowledge to generate more accurate responses.'],
                    'ground_truth': 'RAG is a retrieval-augmented generation technique.'
                },
                {
                    'question': 'What are the limitations of LLM?',
                    'answer': 'LLMs suffer from knowledge cutoff dates and hallucination issues.',
                    'contexts': ['Large language models cannot reflect the latest information.'],
                    'ground_truth': 'Knowledge cutoff and hallucination are major limitations.'
                },
                {
                    'question': 'What is the role of vector database?',
                    'answer': 'Vector databases store embedded documents and perform similarity searches.',
                    'contexts': ['Vector DBs efficiently store and search high-dimensional vectors.'],
                    'ground_truth': 'It handles embedding storage and similarity search.'
                },
                {
                    'question': 'What is prompt engineering?',
                    'answer': 'Prompt engineering is the technique of crafting effective instructions for AI models.',
                    'contexts': ['Good prompts can significantly improve AI performance.'],
                    'ground_truth': 'It is the technique of writing effective instructions for AI.'
                },
                {
                    'question': 'What is the difference between fine-tuning and RAG?',
                    'answer': 'Fine-tuning modifies the model itself, while RAG uses external knowledge.',
                    'contexts': ['Fine-tuning adjusts model weights, while RAG augments with retrieval.'],
                    'ground_truth': 'Model modification vs external knowledge utilization.'
                }
            ]
        }
    
    def generate_demo_report(self, language: str = 'ko') -> Dict[str, Any]:
        """
        Generate a complete demo report for testing
        
        Args:
            language: Report language
            
        Returns:
            Complete demo report data
        """
        questions = self.generate_synthetic_questions(10, language)
        
        # Calculate overall metrics
        metrics = {}
        for metric_name in ['faithfulness', 'answer_relevancy', 'context_precision']:
            values = [q['metrics'][metric_name] for q in questions]
            metrics[metric_name] = sum(values) / len(values)
        
        return {
            'run_id': f'demo_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'timestamp': datetime.now().isoformat(),
            'dataset_name': 'Demo Dataset' if language == 'en' else '데모 데이터셋',
            'dataset_items': len(questions),
            'metrics': metrics,
            'items': questions,
            'status': 'completed',
            'environment': {
                'model_name': 'demo-model',
                'temperature': 0.1,
                'llm_provider': 'demo',
                'embedding_model': 'demo-embeddings'
            }
        }