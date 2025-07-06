"""
Original work Copyright 2024 RAGTrace Contributors
Modified work Copyright 2025 RAGTrace Lite Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

This file has been modified from the original version in the RAGTrace project.

RAGTrace Lite Configuration Loader

Pydantic 기반 설정 관리:
- YAML 파일 파싱
- 환경변수 오버라이드
- 설정 검증 및 기본값 처리
"""

import os
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class LLMConfig(BaseModel):
    """LLM 설정"""
    provider: str = Field(..., description="LLM 제공자 (gemini, hcx)")
    api_key: Optional[str] = Field(None, description="API 키")
    model_name: Optional[str] = Field(None, description="모델 이름")
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed = ['gemini', 'hcx']
        if v.lower() not in allowed:
            raise ValueError(f"지원하지 않는 LLM 제공자: {v}. 허용: {allowed}")
        return v.lower()


class EmbeddingConfig(BaseModel):
    """임베딩 설정"""
    provider: str = Field("default", description="임베딩 제공자 (default, bge_m3)")
    device: str = Field("auto", description="디바이스 (auto, cpu, cuda, mps)")
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed = ['default', 'bge_m3']
        if v.lower() not in allowed:
            raise ValueError(f"지원하지 않는 임베딩 제공자: {v}. 허용: {allowed}")
        return v.lower()


class DataConfig(BaseModel):
    """데이터 설정"""
    input_path: str = Field("data/input", description="입력 데이터 경로")
    supported_formats: List[str] = Field(["json", "xlsx"], description="지원 형식")


class DatabaseConfig(BaseModel):
    """데이터베이스 설정"""
    path: str = Field("db/ragtrace_lite.db", description="데이터베이스 경로")


class ResultsConfig(BaseModel):
    """결과 설정"""
    output_path: str = Field("results", description="결과 출력 경로")


class EvaluationConfig(BaseModel):
    """평가 설정"""
    batch_size: int = Field(10, description="배치 크기")
    show_progress: bool = Field(True, description="진행률 표시")
    raise_exceptions: bool = Field(False, description="예외 발생 시 중단")
    metrics: List[str] = Field(
        ["faithfulness", "answer_relevancy", "context_precision", "context_recall", "answer_correctness"],
        description="평가 메트릭"
    )
    
    @validator('batch_size')
    def validate_batch_size(cls, v):
        if v < 1 or v > 100:
            raise ValueError("배치 크기는 1-100 사이여야 합니다")
        return v
    
    @validator('metrics')
    def validate_metrics(cls, v):
        allowed = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall', 'answer_correctness']
        for metric in v:
            if metric not in allowed:
                raise ValueError(f"지원하지 않는 메트릭: {metric}. 허용: {allowed}")
        return v


class Config(BaseSettings):
    """RAGTrace Lite 설정"""
    llm: LLMConfig
    embedding: EmbeddingConfig = EmbeddingConfig()
    data: DataConfig = DataConfig()
    database: DatabaseConfig = DatabaseConfig()
    results: ResultsConfig = ResultsConfig()
    evaluation: EvaluationConfig = EvaluationConfig()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def load_config(config_path: Optional[str] = None) -> Config:
    """
    YAML 설정 파일을 로드하고 환경변수와 병합합니다.
    
    Args:
        config_path: 설정 파일 경로
        
    Returns:
        Config: 검증된 설정 객체
        
    Raises:
        FileNotFoundError: 설정 파일이 없는 경우
        ValueError: 설정 값이 잘못된 경우
    """
    if config_path is None:
        config_path = "config.yaml"
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        print(f"⚠️ 설정 파일이 없습니다: {config_path}")
        print("환경변수 기반 기본 설정을 사용합니다.")
        
        # 환경변수만으로 설정 생성
        provider = os.getenv('DEFAULT_LLM', 'hcx').lower()
        
        if provider == 'gemini':
            api_key = os.getenv('GEMINI_API_KEY', '')
            model_name = os.getenv('LLM_MODEL_NAME', 'gemini-2.5-flash')
        elif provider == 'hcx':
            api_key = os.getenv('CLOVA_STUDIO_API_KEY', '')
            model_name = os.getenv('LLM_MODEL_NAME', 'HCX-005')
        else:
            api_key = ''
            model_name = 'default'
        
        return Config(
            llm=LLMConfig(
                provider=provider,
                api_key=api_key,
                model_name=model_name
            ),
            evaluation=EvaluationConfig(),
            database=DatabaseConfig()
        )
    
    # YAML 파일 로드
    with open(config_file, 'r', encoding='utf-8') as f:
        yaml_config = yaml.safe_load(f)
    
    # 환경변수 병합
    yaml_config = _merge_environment_variables(yaml_config)
    
    # Pydantic 설정 객체 생성
    try:
        config = Config(**yaml_config)
    except Exception as e:
        raise ValueError(f"설정 파일 검증 실패: {e}")
    
    # API 키 검증
    _validate_api_keys(config)
    
    return config


def _merge_environment_variables(yaml_config: Dict[str, Any]) -> Dict[str, Any]:
    """환경변수를 YAML 설정에 병합합니다."""
    
    # LLM API 키 환경변수 확인
    if 'llm' in yaml_config:
        llm_config = yaml_config['llm']
        provider = llm_config.get('provider', '').lower()
        
        if provider == 'gemini':
            env_key = os.getenv('GEMINI_API_KEY')
            if env_key:
                llm_config['api_key'] = env_key
        elif provider == 'hcx':
            env_key = os.getenv('CLOVA_STUDIO_API_KEY')
            if env_key:
                llm_config['api_key'] = env_key
    
    return yaml_config


def _validate_api_keys(config: Config) -> None:
    """API 키 존재 여부를 검증합니다."""
    
    provider = config.llm.provider
    
    if provider == 'gemini':
        if not config.llm.api_key:
            raise ValueError(
                "Gemini API 키가 설정되지 않았습니다. "
                "config.yaml의 llm.api_key 또는 GEMINI_API_KEY 환경변수를 설정하세요."
            )
    elif provider == 'hcx':
        if not config.llm.api_key:
            raise ValueError(
                "HCX API 키가 설정되지 않았습니다. "
                "config.yaml의 llm.api_key 또는 CLOVA_STUDIO_API_KEY 환경변수를 설정하세요."
            )


def get_default_config() -> Dict[str, Any]:
    """기본 설정을 반환합니다."""
    return {
        'llm': {
            'provider': 'gemini',
            'api_key': None,
            'model_name': 'gemini-2.5-flash'
        },
        'embedding': {
            'provider': 'default',
            'device': 'auto'
        },
        'data': {
            'input_path': 'data/input',
            'supported_formats': ['json', 'xlsx']
        },
        'database': {
            'path': 'db/ragtrace_lite.db'
        },
        'results': {
            'output_path': 'results'
        },
        'evaluation': {
            'batch_size': 10,
            'show_progress': True,
            'raise_exceptions': False,
            'metrics': ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall', 'answer_correctness']
        }
    }


if __name__ == "__main__":
    # 테스트 코드
    try:
        config = load_config()
        print("✅ 설정 로드 성공")
        print(f"LLM 제공자: {config.llm.provider}")
        print(f"배치 크기: {config.evaluation.batch_size}")
        print(f"메트릭: {config.evaluation.metrics}")
    except Exception as e:
        print(f"❌ 설정 로드 실패: {e}")