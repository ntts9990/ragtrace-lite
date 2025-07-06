"""
RAGTrace Lite Data Processor

데이터 처리 기능:
- JSON/XLSX 파일 로딩
- 데이터 검증 및 변환
- RAGAS Dataset 형식으로 변환
- 다양한 contexts 형식 지원
"""

import json
import ast
import pandas as pd
from pathlib import Path
from typing import Union, List, Dict, Any, Optional
from datasets import Dataset

from .config_loader import Config


class DataProcessor:
    """RAGTrace Lite 데이터 처리 클래스"""
    
    REQUIRED_COLUMNS = ["question", "answer", "contexts", "ground_truth"]
    OPTIONAL_COLUMNS = ["ground_truths"]  # RAGAS 호환을 위한 복수형
    
    def __init__(self, config: Optional[Config] = None):
        """
        데이터 프로세서 초기화
        
        Args:
            config: RAGTrace Lite 설정 (선택사항)
        """
        self.config = config
        
    def load_and_prepare_data(self, file_path: Union[str, Path]) -> Dataset:
        """
        데이터 파일을 로드하여 RAGAS Dataset으로 변환합니다.
        
        Args:
            file_path: 입력 데이터 파일 경로 (JSON 또는 XLSX)
            
        Returns:
            Dataset: RAGAS 호환 Dataset 객체
            
        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
            ValueError: 지원하지 않는 파일 형식이거나 데이터가 잘못된 경우
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {file_path}")
        
        print(f"📁 데이터 파일 로딩: {file_path}")
        
        # 파일 형식에 따른 로딩
        if file_path.suffix.lower() == ".json":
            df = self._load_json_file(file_path)
        elif file_path.suffix.lower() in [".xlsx", ".xls"]:
            df = self._load_excel_file(file_path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {file_path.suffix}")
        
        print(f"✅ 데이터 로딩 완료: {len(df)}개 항목")
        
        # 데이터 검증 및 변환
        df = self._validate_and_transform_data(df)
        
        # RAGAS Dataset으로 변환
        dataset = self._convert_to_ragas_dataset(df)
        
        print(f"✅ RAGAS Dataset 변환 완료")
        return dataset
    
    def _load_json_file(self, file_path: Path) -> pd.DataFrame:
        """JSON 파일을 로딩합니다."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # JSON 구조 확인 및 DataFrame 변환
            if isinstance(data, dict):
                # 컬럼별 리스트 형태: {"question": [...], "answer": [...]}
                df = pd.DataFrame(data)
            elif isinstance(data, list):
                # 레코드 리스트 형태: [{"question": "...", "answer": "..."}]
                df = pd.DataFrame(data)
            else:
                raise ValueError("JSON 파일 형식이 올바르지 않습니다")
                
            return df
            
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파일 파싱 오류: {e}")
        except Exception as e:
            raise ValueError(f"JSON 파일 로딩 실패: {e}")
    
    def _load_excel_file(self, file_path: Path) -> pd.DataFrame:
        """Excel 파일을 로딩합니다."""
        try:
            # Excel 파일 읽기
            df = pd.read_excel(file_path)
            return df
            
        except Exception as e:
            raise ValueError(f"Excel 파일 로딩 실패: {e}")
    
    def _validate_and_transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 검증 및 변환을 수행합니다."""
        print("🔍 데이터 검증 및 변환 시작")
        
        # 필수 컬럼 검증
        missing_columns = []
        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            if 'ground_truth' in missing_columns and len(missing_columns) == 1:
                print("⚠️  'ground_truth' 컬럼이 없어 answer_correctness 평가가 제한될 수 있습니다")
                # ground_truth가 없으면 빈 값으로 채움
                df['ground_truth'] = ""
            else:
                raise ValueError(f"필수 컬럼이 누락되었습니다: {missing_columns}")
        
        # contexts 컬럼 변환
        df = self._transform_contexts_column(df)
        
        # ground_truth -> ground_truths 변환 (RAGAS 호환)
        if 'ground_truth' in df.columns and 'ground_truths' not in df.columns:
            df['ground_truths'] = df['ground_truth'].apply(
                lambda x: [x] if isinstance(x, str) and x.strip() else []
            )
        
        # reference 컬럼 추가 (context_precision용)
        if 'ground_truth' in df.columns and 'reference' not in df.columns:
            df['reference'] = df['ground_truth']
        
        # 빈 값 처리
        df = df.fillna("")
        
        print("✅ 데이터 검증 및 변환 완료")
        return df
    
    def _transform_contexts_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """contexts 컬럼을 리스트 형태로 변환합니다."""
        print("🔧 contexts 컬럼 변환 중...")
        
        if 'contexts' not in df.columns:
            raise ValueError("'contexts' 컬럼이 누락되었습니다")
        
        def parse_contexts(contexts_value) -> List[str]:
            """다양한 형태의 contexts를 리스트로 변환"""
            # None이나 NaN 처리
            try:
                if contexts_value is None:
                    return []
                if pd.isna(contexts_value):
                    return []
            except (TypeError, ValueError):
                # pandas.isna()가 실패하는 경우 (예: 배열)
                pass
            
            # 이미 리스트인 경우
            if isinstance(contexts_value, (list, tuple)):
                return [str(item) for item in contexts_value if item is not None]
            
            # numpy 배열인 경우
            try:
                import numpy as np
                if isinstance(contexts_value, np.ndarray):
                    return [str(item) for item in contexts_value.tolist() if item is not None]
            except ImportError:
                pass
            
            # 문자열 변환 시도
            try:
                contexts_str = str(contexts_value).strip()
                if not contexts_str or contexts_str == 'nan':
                    return []
            except:
                return []
            
            # JSON 배열 형태 시도
            if contexts_str.startswith('[') and contexts_str.endswith(']'):
                try:
                    parsed = ast.literal_eval(contexts_str)
                    if isinstance(parsed, list):
                        return [str(item) for item in parsed if item is not None]
                except (ValueError, SyntaxError):
                    pass
                    
                # JSON 파싱 시도
                try:
                    import json
                    parsed = json.loads(contexts_str)
                    if isinstance(parsed, list):
                        return [str(item) for item in parsed if item is not None]
                except json.JSONDecodeError:
                    pass
            
            # 구분자로 분리 시도
            for separator in [';', '|', '\n']:
                if separator in contexts_str:
                    parts = [part.strip() for part in contexts_str.split(separator)]
                    return [part for part in parts if part]
            
            # 단일 context로 처리
            return [contexts_str]
        
        # contexts 컬럼 변환
        try:
            df['contexts'] = df['contexts'].apply(parse_contexts)
        except Exception as e:
            print(f"⚠️  contexts 변환 중 오류 발생: {e}")
            # 대안: 직접 변환
            new_contexts = []
            for idx, contexts_value in df['contexts'].items():
                new_contexts.append(parse_contexts(contexts_value))
            df['contexts'] = new_contexts
        
        # 빈 contexts 확인
        empty_contexts = df['contexts'].apply(len) == 0
        empty_count = empty_contexts.sum()
        if empty_count > 0:
            print(f"⚠️  빈 contexts가 있는 항목: {empty_count}개")
        
        print(f"✅ contexts 변환 완료: 평균 {df['contexts'].apply(len).mean():.1f}개 컨텍스트/항목")
        return df
    
    def _convert_to_ragas_dataset(self, df: pd.DataFrame) -> Dataset:
        """pandas DataFrame을 RAGAS Dataset으로 변환합니다."""
        
        # RAGAS에 필요한 컬럼만 선택
        ragas_columns = ['question', 'answer', 'contexts', 'ground_truths', 'reference']
        
        # 존재하는 컬럼만 선택
        available_columns = [col for col in ragas_columns if col in df.columns]
        df_ragas = df[available_columns].copy()
        
        # Dataset 딕셔너리 생성
        dataset_dict = {}
        for col in available_columns:
            dataset_dict[col] = df_ragas[col].tolist()
        
        # RAGAS Dataset 생성
        try:
            dataset = Dataset.from_dict(dataset_dict)
            return dataset
        except Exception as e:
            raise ValueError(f"RAGAS Dataset 생성 실패: {e}")
    
    def get_data_summary(self, dataset: Dataset) -> Dict[str, Any]:
        """데이터셋 요약 정보를 반환합니다."""
        summary = {
            'total_items': len(dataset),
            'columns': list(dataset.column_names),
            'sample_data': {}
        }
        
        # 각 컬럼의 샘플 데이터
        for col in dataset.column_names:
            if len(dataset) > 0:
                sample_value = dataset[0][col]
                if isinstance(sample_value, list):
                    summary['sample_data'][col] = f"List[{len(sample_value)} items]"
                else:
                    summary['sample_data'][col] = str(sample_value)[:50] + "..."
        
        return summary
    
    def validate_dataset_for_ragas(self, dataset: Dataset) -> List[str]:
        """RAGAS 평가를 위한 데이터셋 검증"""
        issues = []
        
        # 필수 컬럼 확인
        required_for_ragas = ['question', 'answer', 'contexts']
        for col in required_for_ragas:
            if col not in dataset.column_names:
                issues.append(f"필수 컬럼 누락: {col}")
        
        if len(dataset) == 0:
            issues.append("데이터셋이 비어있습니다")
            return issues
        
        # 데이터 품질 확인
        for i, item in enumerate(dataset):
            if i >= 5:  # 첫 5개 항목만 검사
                break
                
            # question 검증
            if not item.get('question') or not str(item['question']).strip():
                issues.append(f"항목 {i}: 질문이 비어있습니다")
            
            # answer 검증
            if not item.get('answer') or not str(item['answer']).strip():
                issues.append(f"항목 {i}: 답변이 비어있습니다")
            
            # contexts 검증
            contexts = item.get('contexts', [])
            if not contexts or len(contexts) == 0:
                issues.append(f"항목 {i}: 컨텍스트가 비어있습니다")
            elif not all(str(ctx).strip() for ctx in contexts):
                issues.append(f"항목 {i}: 빈 컨텍스트가 포함되어 있습니다")
        
        return issues


def test_data_processor():
    """데이터 프로세서 테스트 함수"""
    print("🧪 DataProcessor 테스트 시작")
    
    # 샘플 데이터로 테스트
    sample_file = Path("data/input/sample.json")
    
    if not sample_file.exists():
        print(f"❌ 샘플 파일이 없습니다: {sample_file}")
        return False
    
    try:
        processor = DataProcessor()
        dataset = processor.load_and_prepare_data(sample_file)
        
        # 요약 정보 출력
        summary = processor.get_data_summary(dataset)
        print(f"📊 데이터셋 요약:")
        print(f"   - 총 항목 수: {summary['total_items']}")
        print(f"   - 컬럼: {summary['columns']}")
        
        # 검증
        issues = processor.validate_dataset_for_ragas(dataset)
        if issues:
            print("⚠️  데이터 검증 이슈:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ 데이터 검증 통과")
        
        return True
        
    except Exception as e:
        print(f"❌ DataProcessor 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_data_processor()