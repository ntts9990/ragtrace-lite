"""Excel 파일 파서 - env_ 컬럼 자동 처리"""

import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
from datasets import Dataset
import logging

logger = logging.getLogger(__name__)


class ExcelParser:
    """환경 조건을 포함한 Excel 파일 파서"""
    
    REQUIRED_DATA_COLUMNS = ['question', 'answer', 'contexts']
    OPTIONAL_DATA_COLUMNS = ['ground_truth']
    ENV_PREFIX = 'env_'
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self.df = None
        self.data_df = None
        self.environment = {}
        self.dataset_hash = None
        self.dataset_items = 0
    
    def parse(self) -> Tuple[Dataset, Dict[str, Any], str, int]:
        """
        Excel 파일을 파싱하여 데이터셋과 환경 정보 추출
        
        Returns:
            (Dataset, environment_dict, dataset_hash, dataset_items)
        """
        # Windows 호환 읽기
        self._load_excel()
        
        # 데이터/환경 컬럼 분리
        self._separate_columns()
        
        # 데이터셋 해시 계산
        self._calculate_hash()
        
        # Dataset 객체 생성
        dataset = self._create_dataset()
        
        return dataset, self.environment, self.dataset_hash, self.dataset_items
    
    def _load_excel(self):
        """Excel 파일 로드 (Windows 호환)"""
        try:
            # openpyxl은 Windows에서 가장 안정적
            self.df = pd.read_excel(
                self.file_path,
                engine='openpyxl',
                dtype=str  # 모든 값을 문자열로 읽어서 나중에 변환
            )
            logger.info(f"Loaded {len(self.df)} rows from {self.file_path}")
        except Exception as e:
            logger.error(f"Failed to read Excel: {e}")
            raise
    
    def _separate_columns(self):
        """데이터 컬럼과 환경 컬럼 분리"""
        all_columns = set(self.df.columns)
        
        # 필수 데이터 컬럼 확인
        missing = [col for col in self.REQUIRED_DATA_COLUMNS if col not in all_columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # 데이터 컬럼 추출
        data_columns = self.REQUIRED_DATA_COLUMNS.copy()
        if 'ground_truth' in all_columns:
            data_columns.append('ground_truth')
        
        self.data_df = self.df[data_columns].copy()
        self.dataset_items = len(self.data_df)
        
        # 환경 컬럼 추출 (env_ 접두어)
        env_columns = [col for col in all_columns if col.startswith(self.ENV_PREFIX)]
        
        if env_columns:
            # 첫 번째 행의 값을 환경 조건으로 사용
            for col in env_columns:
                key = col[len(self.ENV_PREFIX):]  # env_ 제거
                value = self.df[col].iloc[0]
                if pd.notna(value):
                    self.environment[key] = self._normalize_value(value)
            
            logger.info(f"Extracted {len(self.environment)} environment conditions")
    
    def _normalize_value(self, value: str) -> Any:
        """값을 적절한 타입으로 변환"""
        if pd.isna(value):
            return None
        
        value = str(value).strip()
        
        # Boolean 변환
        if value.lower() in ['true', 'yes', '1']:
            return True
        elif value.lower() in ['false', 'no', '0']:
            return False
        
        # 숫자 변환
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            return value
    
    def _calculate_hash(self):
        """데이터셋 해시 계산 (파일 내용 기반)"""
        # 데이터 컬럼만으로 해시 생성
        data_str = self.data_df.to_json(orient='records')
        self.dataset_hash = hashlib.md5(data_str.encode('utf-8')).hexdigest()[:16]
    
    def _create_dataset(self) -> Dataset:
        """RAGAS 호환 Dataset 생성"""
        # contexts 처리 (문자열 → 리스트)
        if self.data_df['contexts'].dtype == object:
            self.data_df['contexts'] = self.data_df['contexts'].apply(
                lambda x: self._split_contexts(x) if pd.notna(x) else []
            )
        
        # ground_truths 추가 (RAGAS 형식)
        if 'ground_truth' in self.data_df.columns:
            self.data_df['ground_truths'] = self.data_df['ground_truth'].apply(
                lambda x: [str(x)] if pd.notna(x) else []
            )
        else:
            self.data_df['ground_truths'] = [[] for _ in range(len(self.data_df))]
        
        # Dataset 변환
        return Dataset.from_pandas(self.data_df)
    
    def _split_contexts(self, contexts: str) -> List[str]:
        """컨텍스트 문자열을 리스트로 분할"""
        if not contexts:
            return []
        
        # 구분자 우선순위: \n > ; > |
        if '\n' in contexts:
            return [c.strip() for c in contexts.split('\n') if c.strip()]
        elif ';' in contexts:
            return [c.strip() for c in contexts.split(';') if c.strip()]
        elif '|' in contexts:
            return [c.strip() for c in contexts.split('|') if c.strip()]
        else:
            return [contexts.strip()]
    
    @staticmethod
    def create_template(output_path: str):
        """환경 컬럼이 포함된 템플릿 생성"""
        template_data = {
            # 필수 데이터 컬럼
            'question': ['샘플 질문 1', '샘플 질문 2', '샘플 질문 3'],
            'answer': ['샘플 답변 1', '샘플 답변 2', '샘플 답변 3'],
            'contexts': ['컨텍스트1\n컨텍스트2', '컨텍스트3', '컨텍스트4;컨텍스트5'],
            'ground_truth': ['정답 1', '정답 2', '정답 3'],
            
            # 권장 환경 컬럼
            'env_sys_prompt_version': ['v2.0', '', ''],
            'env_es_nodes': [3, '', ''],
            'env_quantized': ['false', '', ''],
            'env_embedding_model': ['bge-m3', '', ''],
            'env_embedding_version': ['v1.0', '', ''],
            'env_intent_analysis': ['true', '', ''],
            'env_retriever_top_k': [5, '', ''],
            'env_retriever_chunk_size': [512, '', ''],
            'env_retriever_overlap': [50, '', ''],
            'env_notes': ['초기 테스트', '', ''],
            
            # 커스텀 환경 예시
            'env_custom_param1': ['value1', '', ''],
            'env_custom_param2': [100, '', '']
        }
        
        df = pd.DataFrame(template_data)
        
        # Windows 호환 저장
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
            
            # 메타데이터 시트 추가
            metadata = pd.DataFrame({
                'Info': ['Template Version', 'Created Date', 'Description'],
                'Value': ['2.0', pd.Timestamp.now().strftime('%Y-%m-%d'), 
                         'RAGTrace Lite evaluation template with environment columns']
            })
            metadata.to_excel(writer, index=False, sheet_name='Metadata')
        
        logger.info(f"Template created: {output_path}")
        return output_path