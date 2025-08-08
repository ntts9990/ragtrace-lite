# RAGTrace Lite v2.0 개발 가이드

## 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [아키텍처](#아키텍처)
3. [설치 가이드](#설치-가이드)
4. [개발 환경 설정](#개발-환경-설정)
5. [핵심 기능 구현](#핵심-기능-구현)
6. [테스트 전략](#테스트-전략)
7. [Windows 호환성](#windows-호환성)
8. [문제 해결](#문제-해결)

## 프로젝트 개요

### 목적
RAGTrace Lite는 HCX-005 모델 기반 RAG 시스템의 성능을 평가하고 추적하는 경량 도구입니다.

### 핵심 특징
- **단일 Excel 파일**: 데이터와 환경 조건 통합 관리
- **EAV 패턴**: 동적 스키마로 무한 확장 가능
- **통계적 비교**: Welch's t-test 기반 A/B 테스트
- **크로스 플랫폼**: Windows/macOS/Linux 완벽 호환

### 기술 스택
```yaml
Language: Python 3.9+
Database: SQLite 3.35+
Statistics: SciPy, NumPy
LLM Framework: RAGAS, LangChain
CLI: Click
Excel: openpyxl
```

## 아키텍처

### 계층 구조
```
┌─────────────────────────────┐
│   Presentation (CLI)        │
├─────────────────────────────┤
│   Application Logic         │
│  (Evaluator, Comparator)    │
├─────────────────────────────┤
│   Data Access Layer         │
│  (DatabaseManager, EAV)     │
├─────────────────────────────┤
│   External Services         │
│  (HCX API, Gemini API)      │
└─────────────────────────────┘
```

### 데이터 플로우
```
Excel File (data + env_)
    ↓
ExcelParser (parse & validate)
    ↓
Dataset + Environment Dict
    ↓
Evaluator (RAGAS execution)
    ↓
DatabaseManager (EAV storage)
    ↓
WindowComparator (statistics)
    ↓
ReportGenerator (output)
```

### EAV (Entity-Attribute-Value) 패턴

```sql
-- 전통적 방식 (스키마 고정)
CREATE TABLE evaluations (
    run_id TEXT,
    sys_prompt_version TEXT,
    es_nodes INTEGER,
    -- 새 조건 추가시 ALTER TABLE 필요
);

-- EAV 방식 (스키마 유연)
CREATE TABLE evaluation_env (
    run_id TEXT,
    key TEXT,      -- 'sys_prompt_version'
    value TEXT,    -- 'v2.0'
    PRIMARY KEY (run_id, key)
);
-- 새 조건 추가시 INSERT만 하면 됨
```

## 설치 가이드

### 빠른 설치

#### Windows
```batch
:: 자동 설치
install.bat

:: 또는 수동 설치
python -m venv venv
venv\Scripts\activate
pip install -r requirements-windows.txt
pip install -e .
```

#### macOS/Linux
```bash
# 자동 설치
./install.sh

# 또는 수동 설치
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### 개발 모드 설치
```bash
# 개발 의존성 포함
pip install -e .[dev]

# Windows에서
pip install -e .[windows,dev]
```

## 개발 환경 설정

### IDE 설정 (VS Code)

`.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "files.encoding": "utf8",
    "files.eol": "\n",
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }
}
```

### 환경 변수 설정

`.env` 파일:
```bash
# 필수
CLOVA_STUDIO_API_KEY=your_hcx_key
GEMINI_API_KEY=your_gemini_key  # 선택적

# 선택적
LLM_PROVIDER=hcx
DB_PATH=ragtrace.db
LOG_LEVEL=INFO
RATE_LIMIT_DELAY=2.0
```

### Pre-commit Hooks 설정

```bash
pip install pre-commit
pre-commit install
```

`.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.9
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100']
```

## 핵심 기능 구현

### 1. Excel 파싱 (env_ 컬럼)

#### 동작 원리
```python
# Excel 구조
# | question | answer | contexts | env_sys_prompt | env_es_nodes |
# |----------|--------|----------|----------------|--------------|
# | Q1       | A1     | C1       | v2.0           | 3            |

# 파싱 결과
dataset = Dataset({
    'question': ['Q1'],
    'answer': ['A1'],
    'contexts': [['C1']],
    'ground_truths': [[]]
})

environment = {
    'sys_prompt': 'v2.0',
    'es_nodes': 3
}
```

#### 구현 코드
```python
class ExcelParser:
    def parse(self) -> Tuple[Dataset, Dict, str, int]:
        # 1. Excel 로드
        df = pd.read_excel(self.file_path, engine='openpyxl')
        
        # 2. 환경 컬럼 추출
        env_cols = [col for col in df.columns 
                   if col.startswith('env_')]
        
        # 3. 첫 번째 행에서 환경 값 추출
        environment = {}
        for col in env_cols:
            key = col[4:]  # 'env_' 제거
            value = df[col].iloc[0]
            environment[key] = self._normalize_value(value)
        
        # 4. 데이터셋 생성
        data_cols = ['question', 'answer', 'contexts', 'ground_truth']
        data_df = df[data_cols]
        dataset = Dataset.from_pandas(data_df)
        
        return dataset, environment, hash, len(data_df)
```

### 2. EAV 패턴 DB 저장

#### 스키마 설계
```sql
-- 메인 테이블
CREATE TABLE evaluations (
    run_id TEXT PRIMARY KEY,
    timestamp DATETIME,
    dataset_hash TEXT,
    environment_json TEXT,  -- 전체 환경 백업
    ragas_score REAL
);

-- EAV 테이블 (확장 가능)
CREATE TABLE evaluation_env (
    run_id TEXT,
    key TEXT,
    value TEXT,
    PRIMARY KEY (run_id, key)
);

-- 인덱스 (성능 최적화)
CREATE INDEX idx_env_key_value ON evaluation_env(key, value);
```

#### 저장 로직
```python
def save_evaluation(self, run_id, environment, metrics, details):
    with self.get_connection() as conn:
        # 1. 메인 테이블
        conn.execute("""
            INSERT INTO evaluations (...) VALUES (...)
        """, (...))
        
        # 2. EAV 저장 (동적 확장)
        for key, value in environment.items():
            conn.execute("""
                INSERT INTO evaluation_env (run_id, key, value)
                VALUES (?, ?, ?)
            """, (run_id, key, str(value)))
        
        # 3. 메트릭 요약
        # 4. 상세 결과
```

### 3. 통계 비교 (Welch's t-test)

#### 이론적 배경
```python
# Welch's t-test: 분산이 다른 두 그룹 비교
# H0: μ_A = μ_B (두 그룹 평균이 같다)
# H1: μ_A ≠ μ_B (두 그룹 평균이 다르다)

t = (mean_A - mean_B) / sqrt(var_A/n_A + var_B/n_B)
df = (var_A/n_A + var_B/n_B)² / ...  # Welch-Satterthwaite

# Cohen's d: 효과 크기
d = (mean_B - mean_A) / pooled_std
# |d| < 0.2: negligible
# 0.2 ≤ |d| < 0.5: small
# 0.5 ≤ |d| < 0.8: medium
# |d| ≥ 0.8: large
```

#### 구현
```python
def compare_windows(self, window_a, window_b, metric='ragas_score'):
    # 1. 데이터 추출
    values_a = self._get_run_means(runs_a, metric)
    values_b = self._get_run_means(runs_b, metric)
    
    # 2. Welch's t-test
    statistic, p_value = stats.ttest_ind(
        values_a, values_b, equal_var=False
    )
    
    # 3. Cohen's d
    pooled_std = np.sqrt((np.var(values_a) + np.var(values_b)) / 2)
    cohens_d = (np.mean(values_b) - np.mean(values_a)) / pooled_std
    
    # 4. Bootstrap CI (95%)
    ci_a = self._bootstrap_ci(values_a, n_bootstrap=10000)
    ci_b = self._bootstrap_ci(values_b, n_bootstrap=10000)
    
    return ComparisonResult(...)
```

### 4. LLM 어댑터 (HCX/Gemini)

#### 통합 어댑터 패턴
```python
class LLMAdapter(LLM):
    provider: str  # "hcx" or "gemini"
    
    def _call(self, prompt: str) -> str:
        # RAGAS 프롬프트 강화
        enhanced = self._enhance_prompt(prompt)
        
        if self.provider == "hcx":
            return self._call_hcx(enhanced)
        elif self.provider == "gemini":
            return self._call_gemini(enhanced)
    
    def _enhance_prompt(self, prompt: str) -> str:
        # RAGAS 메트릭별 JSON 형식 지정
        if "faithfulness" in prompt.lower():
            prompt += "\nReturn JSON: {\"statements\": [...]}"
        return prompt
```

## 테스트 전략

### 단위 테스트

```python
# tests/test_excel_parser.py
def test_env_column_extraction():
    """env_ 컬럼 추출 테스트"""
    parser = ExcelParser("test_data.xlsx")
    dataset, env, hash, items = parser.parse()
    
    assert 'sys_prompt_version' in env
    assert env['quantized'] is False  # 타입 변환 확인
    assert items == 100

def test_value_normalization():
    """값 정규화 테스트"""
    parser = ExcelParser("dummy.xlsx")
    
    assert parser._normalize_value("true") is True
    assert parser._normalize_value("false") is False
    assert parser._normalize_value("123") == 123
    assert parser._normalize_value("1.23") == 1.23
    assert parser._normalize_value("text") == "text"
```

### 통합 테스트

```python
# tests/test_integration.py
def test_full_evaluation_flow():
    """전체 평가 플로우 테스트"""
    # 1. Excel 로드
    parser = ExcelParser("sample.xlsx")
    dataset, env, hash, items = parser.parse()
    
    # 2. 평가 실행
    evaluator = Evaluator()
    results = evaluator.evaluate(dataset, env)
    
    # 3. DB 저장
    db = DatabaseManager(":memory:")  # In-memory DB
    success = db.save_evaluation(...)
    
    assert success
    assert results['metrics']['faithfulness'] > 0
```

### 성능 테스트

```python
# tests/test_performance.py
import time

def test_large_dataset_performance():
    """대용량 데이터셋 성능 테스트"""
    # 10,000 rows Excel
    start = time.time()
    
    parser = ExcelParser("large_data.xlsx")
    dataset, _, _, items = parser.parse()
    
    elapsed = time.time() - start
    assert elapsed < 10  # 10초 이내
    assert items == 10000
```

## Windows 호환성

### 핵심 규칙

#### 1. 경로 처리
```python
# ❌ Bad
file_path = "data\\test.xlsx"
file_path = os.path.join("data", "test.xlsx")

# ✅ Good
from pathlib import Path
file_path = Path("data") / "test.xlsx"
file_path = Path("data/test.xlsx")  # Forward slash OK
```

#### 2. 인코딩
```python
# ❌ Bad
with open(file_path) as f:
    content = f.read()

# ✅ Good
with open(file_path, encoding='utf-8') as f:
    content = f.read()
```

#### 3. Import 처리
```python
# ❌ Bad
from . import module  # 직접 실행시 실패

# ✅ Good
# 패키지 컨텍스트 보장
if __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    __package__ = "ragtrace_lite"

from ragtrace_lite import module
```

#### 4. 콘솔 출력
```python
# Windows 콘솔 UTF-8 설정
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8')
```

### Windows 특별 고려사항

#### Excel 파일 잠금
```python
def is_excel_locked(file_path):
    """Excel 파일이 열려있는지 확인"""
    try:
        with open(file_path, 'rb'):
            return False
    except PermissionError:
        return True

if is_excel_locked(excel_path):
    print("Please close Excel file first!")
    sys.exit(1)
```

#### SQLite 동시성
```python
# Windows에서 SQLite 잠금 방지
conn = sqlite3.connect(
    db_path,
    timeout=30.0,  # 충분한 타임아웃
    isolation_level='DEFERRED'
)
conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
```

## 문제 해결

### 일반적인 문제

#### ImportError
```python
# 문제
ImportError: attempted relative import with no known parent package

# 해결
python -m ragtrace_lite.cli  # -m 플래그 사용
# 또는
pip install -e .  # 개발 모드 설치
```

#### Excel 읽기 오류
```python
# 문제
PermissionError: [Errno 13] Permission denied

# 해결
# 1. Excel 파일 닫기
# 2. 다른 엔진 시도
df = pd.read_excel(file, engine='xlrd')  # 대체 엔진
```

#### 한글 경로 문제
```python
# 문제
UnicodeDecodeError on Windows

# 해결
file_path = Path(korean_path).resolve()
with open(file_path, encoding='utf-8') as f:
    ...
```

### Windows 특화 문제

#### 콘솔 한글 깨짐
```batch
:: 해결
chcp 65001
set PYTHONIOENCODING=utf-8
```

#### 멀티프로세싱 오류
```python
# 문제: Windows spawn 이슈
# 해결: 스레드 사용
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=4)
```

### 성능 최적화

#### DB 인덱스
```sql
-- 자주 사용하는 쿼리 최적화
CREATE INDEX idx_env_composite 
ON evaluation_env(key, value, run_id);
```

#### 배치 처리
```python
# 대량 INSERT
conn.executemany(
    "INSERT INTO evaluation_env VALUES (?, ?, ?)",
    [(run_id, k, v) for k, v in environment.items()]
)
```

#### 캐싱
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_metric_values(run_id, metric):
    # DB 조회 캐싱
    ...
```

## 배포

### PyPI 배포

```bash
# 빌드
python -m build

# 테스트 PyPI
twine upload --repository testpypi dist/*

# 프로덕션
twine upload dist/*
```

### Docker 배포

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -e .

ENTRYPOINT ["ragtrace"]
```

### 독립 실행 파일

```bash
# PyInstaller
pip install pyinstaller
pyinstaller --onefile --name ragtrace src/ragtrace_lite/cli.py

# 결과
dist/ragtrace.exe  # Windows
dist/ragtrace      # Linux/macOS
```

## CI/CD

### GitHub Actions

`.github/workflows/test.yml`:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python: ['3.9', '3.10', '3.11']
    
    runs-on: ${{ matrix.os }}
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python }}
      
      - name: Install dependencies
        run: |
          pip install -e .[dev]
      
      - name: Run tests
        run: |
          pytest tests/ --cov=ragtrace_lite
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 보안 고려사항

### API 키 관리
```python
# 환경 변수 우선
api_key = os.getenv("CLOVA_STUDIO_API_KEY")

# .env 파일 (개발용)
from dotenv import load_dotenv
load_dotenv()

# 절대 하드코딩 금지!
# api_key = "sk-abc123..."  # ❌
```

### SQL Injection 방지
```python
# ❌ Bad
query = f"SELECT * FROM table WHERE id = {user_input}"

# ✅ Good
query = "SELECT * FROM table WHERE id = ?"
conn.execute(query, (user_input,))
```

## 기여 가이드

### 브랜치 전략
```
main (stable)
  ├── develop (integration)
  │   ├── feature/new-llm-provider
  │   ├── feature/export-formats
  │   └── bugfix/windows-path-issue
  └── release/v2.1.0
```

### 커밋 메시지
```
feat: Add Ollama LLM provider support
fix: Resolve Windows path encoding issue
docs: Update installation guide
test: Add integration tests for EAV pattern
refactor: Simplify response parsing logic
```

### PR 체크리스트
- [ ] 코드가 black/isort로 포맷됨
- [ ] 테스트 작성 및 통과
- [ ] Windows/macOS/Linux에서 테스트
- [ ] 문서 업데이트
- [ ] CHANGELOG 업데이트

## 로드맵

### v2.1.0 (예정)
- [ ] Ollama 로컬 LLM 지원
- [ ] 시계열 분석 기능
- [ ] Web UI (Streamlit)
- [ ] 다국어 지원

### v3.0.0 (장기)
- [ ] 분산 평가 (Ray)
- [ ] 실시간 모니터링
- [ ] 클라우드 배포 (AWS/Azure)
- [ ] REST API

## 참고 자료

- [RAGAS Documentation](https://docs.ragas.io)
- [SQLite EAV Pattern](https://www.sqlite.org/eav.html)
- [Statistical Testing Guide](https://scipy.org/doc/scipy/reference/stats.html)
- [Python Packaging Guide](https://packaging.python.org)

---

문의: ragtrace@example.com