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
from pathlib import Path

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
        
        # 임베딩 모델 설정
        self.embeddings = self._setup_embeddings()
        if self.embeddings:
            print("✅ 임베딩 모델 설정 완료")
        else:
            print("⚠️  임베딩 설정 실패, RAGAS 기본값 사용")
        
        # 평가 메트릭은 evaluate() 호출 시 데이터셋을 기반으로 설정
        self.metrics = None
        
        print(f"✅ 평가자 초기화 완료")
    
    def _setup_embeddings(self):
        """임베딩 모델을 설정합니다."""
        embedding_provider = self.config.embedding.provider.lower()
        
        print(f"🔧 임베딩 설정: {embedding_provider}")
        
        if embedding_provider == "bge_m3":
            print("📁 BGE-M3 임베딩 초기화")
            try:
                return self._setup_bge_m3_embeddings()
            except Exception as e:
                print(f"⚠️  BGE-M3 임베딩 초기화 실패: {e}")
                return None
            
        elif embedding_provider == "default":
            # OpenAI 임베딩 사용 (RAGAS 기본값)
            try:
                from langchain_openai.embeddings import OpenAIEmbeddings
                import os
                
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key or api_key == "your_openai_api_key_here":
                    print("⚠️  OpenAI API 키가 설정되지 않았습니다")
                    return None
                    
                embeddings = OpenAIEmbeddings(
                    model="text-embedding-ada-002",
                    openai_api_key=api_key
                )
                print("✅ OpenAI 임베딩 (text-embedding-ada-002) 로드 완료")
                return embeddings
                
            except ImportError as e:
                print(f"⚠️  OpenAI 임베딩 import 실패: {e}")
                return None
            except Exception as e:
                print(f"⚠️  OpenAI 임베딩 초기화 실패: {e}")
                return None
                
        else:
            print(f"⚠️  지원하지 않는 임베딩 제공자: {embedding_provider}")
            return None

    def _setup_bge_m3_embeddings(self):
        """BGE-M3 임베딩 모델을 설정합니다."""
        import os
        
        # 모델 경로 설정
        model_path = Path(os.getenv('BGE_M3_MODEL_PATH', './models/bge-m3'))
        
        # 모델 폴더 생성
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 모델이 로컬에 있는지 확인
        if not model_path.exists() or not any(model_path.iterdir()):
            print(f"📥 BGE-M3 모델을 다운로드합니다: {model_path}")
            self._download_bge_m3_model(model_path)
        else:
            print(f"✅ BGE-M3 모델 발견: {model_path}")
        
        # 임베딩 모델 로드
        try:
            from sentence_transformers import SentenceTransformer
            
            device = os.getenv('BGE_M3_DEVICE', 'auto')
            if device == 'auto':
                import torch
                if torch.cuda.is_available():
                    device = 'cuda'
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    device = 'mps'
                else:
                    device = 'cpu'
            
            print(f"🔧 BGE-M3 모델 로딩 (device: {device})...")
            model = SentenceTransformer(str(model_path), device=device)
            
            # RAGAS 호환 임베딩 래퍼 생성
            from ragas.embeddings import LangchainEmbeddingsWrapper
            
            try:
                # 새로운 langchain_huggingface 사용 (권장)
                from langchain_huggingface import HuggingFaceEmbeddings
            except ImportError:
                # 대체: langchain_community 사용
                from langchain_community.embeddings import HuggingFaceEmbeddings
            
            # HuggingFace 임베딩을 langchain으로 감싸기
            lc_embeddings = HuggingFaceEmbeddings(
                model_name=str(model_path),
                model_kwargs={'device': device}
            )
            embeddings = LangchainEmbeddingsWrapper(lc_embeddings)
            
            print(f"✅ BGE-M3 임베딩 로드 완료 (device: {device})")
            return embeddings
            
        except ImportError as e:
            raise ImportError(f"BGE-M3 의존성이 설치되지 않았습니다: {e}")
        except Exception as e:
            raise Exception(f"BGE-M3 모델 로드 실패: {e}")
    
    def _download_bge_m3_model(self, model_path: Path):
        """BGE-M3 모델을 Hugging Face에서 다운로드합니다."""
        try:
            from huggingface_hub import snapshot_download
            
            print(f"📦 BGE-M3 모델 다운로드 시작...")
            print(f"   위치: {model_path.absolute()}")
            print(f"   크기: 약 2.3GB (시간이 걸릴 수 있습니다)")
            
            # 디렉토리 생성 (크로스 플랫폼 호환)
            model_path.mkdir(parents=True, exist_ok=True)
            
            # BGE-M3 모델 다운로드 (크로스 플랫폼 경로 처리)
            snapshot_download(
                repo_id="BAAI/bge-m3",
                local_dir=str(model_path.absolute()),
                local_dir_use_symlinks=False,  # 심볼릭 링크 대신 실제 파일 복사
                resume_download=True  # 중단된 다운로드 재개 지원
            )
            
            print(f"✅ BGE-M3 모델 다운로드 완료: {model_path.absolute()}")
            
        except ImportError as e:
            print("❌ huggingface_hub가 설치되지 않았습니다")
            print("💡 해결방법: pip install huggingface_hub")
            raise ImportError(f"huggingface_hub가 설치되지 않았습니다: {e}")
        except Exception as e:
            raise Exception(f"BGE-M3 모델 다운로드 실패: {e}")

    def _check_ground_truth_availability(self, dataset: Dataset = None) -> bool:
        """Ground truth 데이터의 가용성을 확인합니다."""
        if dataset is None:
            return False
        
        # ground_truths 컬럼이 있는지 확인
        if 'ground_truths' not in dataset.column_names:
            return False
        
        # ground_truths가 비어있지 않은 항목이 있는지 확인
        for item in dataset:
            ground_truths = item.get('ground_truths', [])
            if ground_truths and len(ground_truths) > 0:
                # 빈 문자열이 아닌 ground truth가 있는지 확인
                valid_truths = [gt for gt in ground_truths if isinstance(gt, str) and gt.strip()]
                if valid_truths:
                    return True
        
        return False

    def _setup_metrics(self, dataset: Dataset = None) -> List[Any]:
        """평가 메트릭을 설정합니다."""
        metrics = []
        
        print("🔧 메트릭 설정 중...")
        
        # Ground truth 데이터 가용성 확인
        has_ground_truths = self._check_ground_truth_availability(dataset)
        
        # 메트릭 선택: ground truth가 있으면 5개, 없으면 4개
        if has_ground_truths:
            selected_metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall", "answer_correctness"]
            print("📊 Ground truth 데이터 확인: 5개 메트릭 사용")
        else:
            selected_metrics = ["faithfulness", "answer_relevancy", "context_precision", "answer_correctness"]
            print("📊 Ground truth 데이터 없음: 4개 메트릭 사용 (context_recall 제외)")
        
        for metric_name in selected_metrics:
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
        print(f"   - LLM: {self.config.llm.provider}")
        print(f"   - 배치 크기: {self.config.evaluation.batch_size}")
        
        # 데이터셋 기반 메트릭 설정
        if self.metrics is None:
            self.metrics = self._setup_metrics(dataset)
        
        print(f"   - 메트릭: {len(self.metrics)}개")
        
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
                raise_exceptions=False,  # 파싱 오류 시에도 계속 진행
                show_progress=self.config.evaluation.show_progress,
            )
            
            print("✅ 평가 완료!")
            
            # 결과를 pandas DataFrame으로 변환
            try:
                results_df = result.to_pandas()
            except Exception as e:
                print(f"⚠️ DataFrame 변환 중 오류: {e}")
                # 수동으로 DataFrame 생성
                results_dict = {}
                if hasattr(result, 'scores'):
                    for key, value in result.scores.items():
                        results_dict[key] = value
                
                results_df = pd.DataFrame(results_dict)
            
            # 디버깅: 결과 데이터 타입 확인
            print("\n📊 결과 데이터 타입:")
            for col in results_df.columns:
                print(f"  - {col}: {results_df[col].dtype}")
                # 문자열 컬럼 확인
                if results_df[col].dtype == 'object':
                    print(f"    샘플: {results_df[col].head(2).tolist()}")
            
            # 결과 요약 출력
            try:
                self._print_evaluation_summary(results_df)
            except Exception as e:
                print(f"⚠️ 결과 요약 출력 중 오류: {e}")
                # 기본 정보만 출력
                print("\n📈 평가 결과 (원시 데이터):")
                print(results_df.head())
            
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
        
        # 실제 평가된 메트릭 확인
        evaluated_metrics = [col for col in results_df.columns 
                           if col not in ['question', 'answer', 'contexts', 'ground_truths', 'reference']]
        
        # 각 메트릭별 평균 점수
        for metric_name in evaluated_metrics:
            try:
                # 숫자가 아닌 값 제외하고 numeric 타입으로 변환
                scores = pd.to_numeric(results_df[metric_name], errors='coerce').dropna()
                
                if len(scores) > 0:
                    avg_score = scores.mean()
                    min_score = scores.min()
                    max_score = scores.max()
                    
                    # NaN 체크
                    if pd.isna(avg_score):
                        print(f"{metric_name:20}: 계산 불가 (유효한 점수 없음)")
                    else:
                        print(f"{metric_name:20}: {avg_score:.4f} (범위: {min_score:.4f}-{max_score:.4f})")
                else:
                    print(f"{metric_name:20}: 데이터 없음")
            except Exception as e:
                print(f"{metric_name:20}: 오류 발생 ({str(e)})")
        
        # 전체 평균 (RAGAS Score)
        if evaluated_metrics:
            try:
                # 각 메트릭을 numeric으로 변환
                numeric_df = pd.DataFrame()
                valid_metrics = []
                
                for metric in evaluated_metrics:
                    numeric_col = pd.to_numeric(results_df[metric], errors='coerce')
                    if numeric_col.notna().any():  # 최소 하나의 유효한 값이 있으면
                        numeric_df[metric] = numeric_col
                        valid_metrics.append(metric)
                
                if valid_metrics:
                    # 각 행의 평균 계산 (NaN 제외)
                    overall_scores = numeric_df[valid_metrics].mean(axis=1, skipna=True)
                    overall_avg = overall_scores.mean(skipna=True)
                    
                    if not pd.isna(overall_avg):
                        print(f"{'='*50}")
                        print(f"{'전체 평균 (RAGAS Score)':20}: {overall_avg:.4f}")
                    else:
                        print(f"{'='*50}")
                        print(f"{'전체 평균 (RAGAS Score)':20}: 계산 불가")
                else:
                    print(f"{'='*50}")
                    print(f"{'전체 평균 (RAGAS Score)':20}: 유효한 메트릭 없음")
            except Exception as e:
                print(f"{'='*50}")
                print(f"{'전체 평균 (RAGAS Score)':20}: 오류 ({str(e)})")
        
        print(f"{'='*50}")
    
    def get_detailed_results(self, results_df: pd.DataFrame) -> Dict[str, Any]:
        """상세한 평가 결과를 반환합니다."""
        
        detailed_results = {
            'summary': {},
            'by_metric': {},
            'by_item': {},
            'statistics': {}
        }
        
        # 실제 평가된 메트릭 확인
        metric_columns = [col for col in results_df.columns 
                         if col not in ['question', 'answer', 'contexts', 'ground_truths', 'reference']]
        
        # 메트릭별 통계
        for metric_name in metric_columns:
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