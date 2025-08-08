# RAGTrace Statistical Analysis Guide
## 고급 통계 분석 기능 가이드

### 📊 Overview
RAGTrace v2.0는 RAG 시스템 평가를 위한 포괄적인 통계 분석 기능을 제공합니다.

## 🔬 Advanced Statistical Analyzer

### 자동 검정 선택 (Automatic Test Selection)
시스템이 데이터 특성을 자동으로 분석하여 적절한 통계 검정을 선택합니다:

```python
from ragtrace_lite.stats.advanced_analyzer import AdvancedStatisticalAnalyzer

analyzer = AdvancedStatisticalAnalyzer(alpha=0.05)
result = analyzer.analyze_comparison(group_a, group_b, test_type="auto")
```

**선택 로직:**
- 정규성 검정 (Shapiro-Wilk) → 정규분포 확인
- 등분산성 검정 (Levene) → 분산 동일성 확인
- 결과에 따라:
  - 정규분포 + 등분산 → **Independent t-test**
  - 정규분포 + 이분산 → **Welch's t-test**
  - 비정규분포 → **Mann-Whitney U test**

### 지원 통계 검정

#### 1. Independent t-test
- **사용 조건**: 정규분포, 등분산
- **효과 크기**: Cohen's d
- **해석 기준**:
  - |d| < 0.2: 무시할 수준
  - |d| < 0.5: 작은 효과
  - |d| < 0.8: 중간 효과
  - |d| ≥ 0.8: 큰 효과

#### 2. Welch's t-test
- **사용 조건**: 정규분포, 이분산
- **특징**: 등분산 가정 불필요
- **권장**: 샘플 크기가 다를 때

#### 3. Mann-Whitney U test
- **사용 조건**: 비정규분포
- **효과 크기**: Rank-biserial correlation
- **장점**: 이상치에 강건함

#### 4. One-way ANOVA
- **사용 조건**: 3개 이상 그룹 비교
- **효과 크기**: Eta-squared (η²)
- **사후 검정**: Tukey HSD

### 상관 분석
```python
corr_result = analyzer.perform_correlation_analysis(x, y)
```

**제공 지표:**
- Pearson correlation (선형 관계)
- Spearman correlation (순위 관계)
- Kendall's tau (순서 일치도)

### 이상치 탐지
```python
outliers = analyzer.detect_outliers(data, method="iqr")
```

**방법:**
- IQR method: Q1 - 1.5×IQR, Q3 + 1.5×IQR
- Z-score method: |z| > 3

## 📝 Individual Question Analyzer

### 문항별 성능 분석
```python
from ragtrace_lite.stats.question_analyzer import QuestionAnalyzer

analyzer = QuestionAnalyzer()
analysis = analyzer.analyze_question(question_data, metrics)
```

### 자동 문제 식별
시스템이 자동으로 문제점을 식별하고 개선 방안을 제시:

**식별 기준:**
- Faithfulness < 0.6 → "답변이 컨텍스트 벗어남"
- Answer Relevancy < 0.6 → "질문과 관련성 부족"
- Context Precision < 0.6 → "불필요한 정보 포함"
- Context Recall < 0.6 → "필요 정보 누락"
- Answer Correctness < 0.5 → "사실적 정확도 낮음"

### 패턴 분석
```python
patterns = analyzer.identify_patterns(analyses_df)
improvement_plan = analyzer.generate_improvement_plan(patterns)
```

**분석 내용:**
- 전체 통계 (평균, 표준편차, 최소/최대)
- 상태 분포 (good/warning/poor)
- 공통 문제점
- 메트릭 간 상관관계
- 최우수/최하위 문항

## 🌐 Dashboard Integration

### A/B Testing
대시보드에서 두 모델의 성능을 통계적으로 비교:

```javascript
// API 호출
fetch('/api/ab-test', {
    method: 'POST',
    body: JSON.stringify({
        run_id_a: 'run_001',
        run_id_b: 'run_002'
    })
})
```

**결과 해석:**
- **p-value < 0.05**: 통계적으로 유의미한 차이
- **Effect size**: 실질적 차이의 크기
- **Confidence Interval**: 차이의 신뢰구간

### 시각화 옵션

#### 1. 메트릭 비교 차트
- Radar chart로 5개 메트릭 동시 비교
- Bar chart로 개별 메트릭 비교

#### 2. 분포 시각화
- Box plot으로 분포 비교
- Violin plot으로 밀도 추정

#### 3. 트렌드 분석
- 시계열 그래프로 성능 변화 추적
- 이동 평균으로 트렌드 파악

## 💡 Best Practices

### 1. 샘플 크기 고려
```python
required_n = analyzer.calculate_sample_size(
    effect_size=0.5,  # 중간 효과
    power=0.8,         # 80% 검정력
    alpha=0.05         # 5% 유의수준
)
```

### 2. 다중 비교 보정
여러 메트릭을 동시에 비교할 때 Bonferroni 보정 고려:
```python
adjusted_alpha = 0.05 / n_comparisons
```

### 3. 실질적 유의성 vs 통계적 유의성
- p-value가 작아도 effect size가 작으면 실질적 차이 없음
- Effect size와 함께 해석 필요

## 📈 Use Cases

### 1. 모델 업그레이드 검증
```python
# 이전 모델과 새 모델 비교
old_scores = [0.75, 0.78, 0.72, ...]
new_scores = [0.82, 0.85, 0.79, ...]

result = analyzer.analyze_comparison(old_scores, new_scores)
if result.significant and result.effect_size > 0.5:
    print("새 모델이 의미있는 개선을 보임")
```

### 2. 데이터셋별 성능 분석
```python
# 여러 데이터셋에서의 성능 비교
datasets = [dataset_a, dataset_b, dataset_c]
anova_result = analyzer.perform_anova(*datasets)

if anova_result['significant']:
    # 사후 검정으로 어느 데이터셋이 다른지 확인
    post_hoc = anova_result['post_hoc']
```

### 3. 취약 문항 식별
```python
# 배치 분석으로 문제 문항 찾기
df = analyzer.batch_analyze(questions, metrics_list)
worst_questions = df.nsmallest(5, 'overall_score')

for _, q in worst_questions.iterrows():
    print(f"문항: {q['question']}")
    print(f"주요 문제: {q['main_issue']}")
    print(f"권장 조치: {q['priority_action']}")
```

## 🎯 Interpretation Guidelines

### P-value 해석
- **p < 0.001**: 매우 강한 증거
- **p < 0.01**: 강한 증거
- **p < 0.05**: 충분한 증거
- **p ≥ 0.05**: 증거 불충분

### Effect Size 해석
- **작은 효과**: 실무적 의미 제한적
- **중간 효과**: 주목할 만한 차이
- **큰 효과**: 중요한 개선/악화

### 신뢰구간 해석
- 0을 포함하지 않음 → 유의미한 차이
- 구간 폭이 좁음 → 높은 정밀도
- 구간 폭이 넓음 → 불확실성 높음

## 🔧 Configuration

### 환경 변수 설정
```bash
# 통계 분석 설정
export RAGTRACE_ALPHA_LEVEL=0.05  # 유의수준
export RAGTRACE_POWER_LEVEL=0.8   # 검정력
```

### 커스터마이징
```python
# 커스텀 임계값 설정
analyzer = QuestionAnalyzer()
analyzer.thresholds = {
    'good': 0.85,    # 더 엄격한 기준
    'warning': 0.70,
    'poor': 0.0
}
```

## 📚 References
- [Cohen's d Effect Size](https://en.wikipedia.org/wiki/Effect_size#Cohen's_d)
- [Mann-Whitney U Test](https://en.wikipedia.org/wiki/Mann%E2%80%93Whitney_U_test)
- [ANOVA](https://en.wikipedia.org/wiki/Analysis_of_variance)
- [Multiple Comparisons Problem](https://en.wikipedia.org/wiki/Multiple_comparisons_problem)