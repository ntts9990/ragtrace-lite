from pydantic import BaseModel, Field, HttpUrl, FilePath
from typing import Optional, Dict, List, Literal

class LLMProviderConfig(BaseModel):
    api_url: HttpUrl
    model_name: str
    temperature: float = 0.1
    max_tokens: int = 1024
    rate_limit_delay: float = 5.0
    rate_limit_increment: float = 5.0
    api_key: Optional[str] = None

class LLMConfig(BaseModel):
    provider: Literal["hcx", "gemini"] = "hcx"
    hcx: LLMProviderConfig
    gemini: LLMProviderConfig

class LocalEmbeddingsConfig(BaseModel):
    model_path: str = "./models/bge-m3"
    use_gpu: bool = False
    batch_size: int = 32

class APIEmbeddingsConfig(BaseModel):
    api_url: HttpUrl
    model_name: str = "bge-m3"
    api_key: Optional[str] = None
    timeout: int = 30
    max_batch_size: int = 100

class EmbeddingsConfig(BaseModel):
    provider: Literal["local", "api"] = "local"
    local: LocalEmbeddingsConfig
    api: APIEmbeddingsConfig

class EvaluationMetricsConfig(BaseModel):
    base: List[str] = ["faithfulness", "answer_relevancy", "context_precision"]
    conditional: List[str] = ["context_recall", "answer_correctness"]

class EvaluationConfig(BaseModel):
    batch_size: Dict[str, int] = Field(default_factory=lambda: {"initial": 5, "fallback_sizes": [3, 1]})
    retry: Dict[str, float] = Field(default_factory=lambda: {"max_attempts": 3, "backoff_factor": 2.0})
    metrics: EvaluationMetricsConfig = Field(default_factory=EvaluationMetricsConfig)

class DatabaseConfig(BaseModel):
    path: str = "ragtrace.db"
    wal_mode: bool = True

class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: Optional[str] = "ragtrace.log"
    console: bool = True
    timestamps: bool = True

class ReportsConfig(BaseModel):
    output_dir: str = "results"
    formats: List[str] = ["html", "json", "markdown"]
    include_details: bool = True
    include_plots: bool = True

class OfflineConfig(BaseModel):
    enabled: bool = False
    models_dir: str = "./models"
    wheels_dir: str = "./offline_wheels"
    python_version: str = "3.9"
    platforms: List[str] = ["win_amd64", "win32"]

class AppConfig(BaseModel):
    llm: LLMConfig
    embeddings: EmbeddingsConfig
    evaluation: EvaluationConfig
    database: DatabaseConfig
    logging: LoggingConfig
    reports: ReportsConfig
    offline: OfflineConfig
