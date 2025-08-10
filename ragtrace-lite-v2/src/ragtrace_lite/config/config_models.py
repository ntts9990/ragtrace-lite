from pydantic import BaseModel, Field, HttpUrl, FilePath
from typing import Optional, Dict, List, Literal, Union

class LLMProviderConfig(BaseModel):
    api_url: Union[HttpUrl, str]
    model_name: str
    temperature: float = 0.1
    max_tokens: int = 1024
    rate_limit_delay: float = 5.0
    rate_limit_increment: float = 5.0
    api_key: Optional[str] = None

class LLMConfig(BaseModel):
    provider: Literal["hcx", "gemini"] = "hcx"
    hcx: Optional[LLMProviderConfig] = None
    gemini: Optional[LLMProviderConfig] = None
    
    def model_post_init(self, __context) -> None:
        """Create default providers if not set"""
        if self.hcx is None:
            self.hcx = LLMProviderConfig(
                api_url="https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/HCX-005",
                model_name="HCX-005",
                api_key="${CLOVA_STUDIO_API_KEY}"
            )
        if self.gemini is None:
            self.gemini = LLMProviderConfig(
                api_url="https://generativelanguage.googleapis.com/v1beta/models",
                model_name="gemini-2.5-flash-lite",
                api_key="${GEMINI_API_KEY}"
            )

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
    local: Optional[LocalEmbeddingsConfig] = Field(default_factory=LocalEmbeddingsConfig)
    api: Optional[APIEmbeddingsConfig] = None

class EvaluationMetricsConfig(BaseModel):
    base: List[str] = ["faithfulness", "answer_relevancy", "context_precision"]
    conditional: List[str] = ["context_recall", "answer_correctness"]

class EvaluationBatchConfig(BaseModel):
    initial: int = 5
    fallback_sizes: List[int] = [3, 1]

class EvaluationRetryConfig(BaseModel):
    max_attempts: int = 3
    backoff_factor: float = 2.0

class EvaluationConfig(BaseModel):
    batch_size: EvaluationBatchConfig = Field(default_factory=EvaluationBatchConfig)
    retry: EvaluationRetryConfig = Field(default_factory=EvaluationRetryConfig)
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
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    reports: ReportsConfig = Field(default_factory=ReportsConfig)
    offline: OfflineConfig = Field(default_factory=OfflineConfig)
