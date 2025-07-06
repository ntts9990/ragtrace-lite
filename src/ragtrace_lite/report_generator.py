"""
RAGTrace Lite Report Generator

Markdown 보고서 생성:
- 평가 결과 요약
- 텍스트 기반 시각화
- 통계 분석 및 인사이트
- 상세 결과 분석
"""

import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from .config_loader import Config


class ReportGenerator:
    """RAGTrace Lite Markdown 보고서 생성 클래스"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        보고서 생성기 초기화
        
        Args:
            config: RAGTrace Lite 설정
        """
        self.config = config
    
    def generate_evaluation_report(self,
                                 run_id: str,
                                 summary_data: Dict[str, Any],
                                 results_df: pd.DataFrame,
                                 dataset: List[Dict[str, Any]]) -> str:
        """
        완전한 평가 보고서를 생성합니다.
        
        Args:
            run_id: 실행 ID
            summary_data: 요약 통계 데이터
            results_df: 평가 결과 DataFrame
            dataset: 원본 데이터셋
            
        Returns:
            str: Markdown 형식의 보고서
        """
        report_sections = []
        
        # 헤더
        report_sections.append(self._generate_header(run_id, summary_data))
        
        # 요약 통계
        report_sections.append(self._generate_summary_statistics(summary_data))
        
        # 메트릭별 분석
        report_sections.append(self._generate_metric_analysis(summary_data, results_df))
        
        # 성능 분석
        report_sections.append(self._generate_performance_analysis(results_df, dataset))
        
        # 상세 결과
        report_sections.append(self._generate_detailed_results(results_df, dataset))
        
        # 인사이트 및 권장사항
        report_sections.append(self._generate_insights_and_recommendations(summary_data, results_df))
        
        # 푸터
        report_sections.append(self._generate_footer())
        
        return "\n\n".join(report_sections)
    
    def _generate_header(self, run_id: str, summary_data: Dict[str, Any]) -> str:
        """보고서 헤더 생성"""
        run_info = summary_data.get('run_info', {})
        
        header = [
            f"# RAGTrace Lite 평가 보고서",
            f"",
            f"**실행 ID**: `{run_id}`  ",
            f"**생성 일시**: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}  ",
            f"**LLM 모델**: {run_info.get('llm_provider', 'Unknown')} - {run_info.get('llm_model', 'Unknown')}  ",
            f"**데이터셋**: {run_info.get('dataset_name', 'Unknown')}  ",
            f"**총 항목 수**: {run_info.get('total_items', 0)}개  ",
            f"**평가 상태**: {run_info.get('status', 'Unknown')}  ",
            f"",
            "---"
        ]
        
        return "\n".join(header)
    
    def _generate_summary_statistics(self, summary_data: Dict[str, Any]) -> str:
        """요약 통계 섹션 생성"""
        metric_stats = summary_data.get('metric_statistics', {})
        ragas_score = summary_data.get('ragas_score')
        
        section = [
            "## 📊 종합 결과",
            ""
        ]
        
        # RAGAS 전체 점수
        if ragas_score is not None:
            ragas_score = float(ragas_score)  # 명시적 float 변환
            score_bar = self._create_score_bar(ragas_score)
            section.extend([
                f"### 🎯 전체 RAGAS 점수",
                f"",
                f"**{ragas_score:.4f}** {score_bar}",
                f"",
                self._interpret_score(ragas_score),
                ""
            ])
        
        # 메트릭별 점수 테이블
        if metric_stats:
            section.extend([
                "### 📈 메트릭별 성능",
                "",
                "| 메트릭 | 평균 점수 | 시각화 | 최소값 | 최대값 | 평가 수 |",
                "|--------|-----------|--------|--------|--------|---------|"
            ])
            
            for metric_name, stats in metric_stats.items():
                avg_score = float(stats.get('average', 0) or 0)
                min_score = float(stats.get('minimum', 0) or 0)
                max_score = float(stats.get('maximum', 0) or 0)
                count = int(stats.get('count', 0) or 0)
                
                score_viz = self._create_score_bar(avg_score, length=15)
                
                section.append(
                    f"| {metric_name} | {avg_score:.4f} | `{score_viz}` | {min_score:.4f} | {max_score:.4f} | {count} |"
                )
        
        return "\n".join(section)
    
    def _generate_metric_analysis(self, summary_data: Dict[str, Any], results_df: pd.DataFrame) -> str:
        """메트릭별 상세 분석 생성"""
        metric_stats = summary_data.get('metric_statistics', {})
        
        section = [
            "## 🔍 메트릭별 상세 분석",
            ""
        ]
        
        metric_descriptions = {
            'faithfulness': '**충실도** - 답변이 제공된 컨텍스트에 얼마나 충실한지 측정',
            'answer_relevancy': '**답변 관련성** - 답변이 질문과 얼마나 관련이 있는지 측정',
            'context_precision': '**컨텍스트 정확도** - 검색된 컨텍스트의 정확도 측정',
            'context_recall': '**컨텍스트 회상률** - 필요한 정보가 컨텍스트에 포함된 정도 측정',
            'answer_correctness': '**답변 정확성** - 답변이 정답과 얼마나 일치하는지 측정'
        }
        
        for metric_name, stats in metric_stats.items():
            description = metric_descriptions.get(metric_name, f'**{metric_name}** - 평가 메트릭')
            # 더 강력한 None 처리 - float 변환 추가
            avg_score = float(stats.get('average', 0) or 0)  # None 값 처리
            min_score = float(stats.get('minimum', 0) or 0)
            max_score = float(stats.get('maximum', 0) or 0)
            count = int(stats.get('count', 0) or 0)
            
            section.extend([
                f"### {metric_name}",
                f"",
                description,
                f"",
                f"- **평균 점수**: {avg_score:.4f}",
                f"- **점수 범위**: {min_score:.4f} ~ {max_score:.4f}",
                f"- **평가 완료**: {count}개 항목",
                ""
            ])
            
            # 성능 해석
            interpretation = self._interpret_metric_performance(metric_name, avg_score)
            section.extend([
                f"**성능 해석**: {interpretation}",
                ""
            ])
        
        return "\n".join(section)
    
    def _generate_performance_analysis(self, results_df: pd.DataFrame, dataset: List[Dict[str, Any]]) -> str:
        """성능 분석 섹션 생성"""
        section = [
            "## 📈 성능 분석",
            ""
        ]
        
        # 상위/하위 성능 항목 분석
        if not results_df.empty:
            # 전체 점수 계산 (메트릭 평균)
            metric_columns = [col for col in results_df.columns 
                            if col not in ['question', 'answer', 'contexts', 'ground_truths', 'reference']]
            
            if metric_columns:
                results_df_copy = results_df.copy()
                # 수치형 컬럼만 선택하고 평균 계산
                numeric_columns = []
                for col in metric_columns:
                    if col in results_df_copy.columns:
                        # 수치형 데이터로 변환 가능한 컬럼만 선택
                        try:
                            pd.to_numeric(results_df_copy[col], errors='coerce')
                            numeric_columns.append(col)
                        except:
                            continue
                
                if numeric_columns:
                    numeric_data = results_df_copy[numeric_columns].apply(pd.to_numeric, errors='coerce')
                    results_df_copy['overall_score'] = numeric_data.mean(axis=1, skipna=True)
                else:
                    results_df_copy['overall_score'] = 0
                
                # 상위 3개
                top_3 = results_df_copy.nlargest(3, 'overall_score')
                section.extend([
                    "### 🏆 최고 성능 항목 (상위 3개)",
                    ""
                ])
                
                for i, (idx, row) in enumerate(top_3.iterrows(), 1):
                    question = dataset[idx]['question'] if idx < len(dataset) else "Unknown"
                    question_short = (question[:50] + "...") if len(question) > 50 else question
                    overall_score = float(row['overall_score']) if pd.notna(row['overall_score']) else 0.0
                    section.extend([
                        f"{i}. **점수: {overall_score:.4f}**",
                        f"   - 질문: {question_short}",
                        ""
                    ])
                
                # 하위 3개
                bottom_3 = results_df_copy.nsmallest(3, 'overall_score')
                section.extend([
                    "### ⚠️ 개선 필요 항목 (하위 3개)",
                    ""
                ])
                
                for i, (idx, row) in enumerate(bottom_3.iterrows(), 1):
                    question = dataset[idx]['question'] if idx < len(dataset) else "Unknown"
                    question_short = (question[:50] + "...") if len(question) > 50 else question
                    overall_score = float(row['overall_score']) if pd.notna(row['overall_score']) else 0.0
                    section.extend([
                        f"{i}. **점수: {overall_score:.4f}**",
                        f"   - 질문: {question_short}",
                        ""
                    ])
        
        # 점수 분포 분석
        section.extend(self._generate_score_distribution_analysis(results_df))
        
        return "\n".join(section)
    
    def _generate_detailed_results(self, results_df: pd.DataFrame, dataset: List[Dict[str, Any]]) -> str:
        """상세 결과 섹션 생성"""
        section = [
            "## 📋 상세 평가 결과",
            "",
            "각 질문별 상세 점수 및 분석 결과입니다.",
            ""
        ]
        
        # 메트릭 컬럼 식별
        metric_columns = [col for col in results_df.columns 
                        if col not in ['question', 'answer', 'contexts', 'ground_truths', 'reference']]
        
        if not metric_columns:
            section.append("평가 결과가 없습니다.")
            return "\n".join(section)
        
        # 테이블 헤더
        header_row = "| 번호 | 질문 | " + " | ".join(metric_columns) + " |"
        separator_row = "|------|------|" + "|".join(["--------" for _ in metric_columns]) + "|"
        
        section.extend([header_row, separator_row])
        
        # 각 항목별 결과
        for i, (idx, row) in enumerate(results_df.iterrows()):
            question = dataset[idx]['question'] if idx < len(dataset) else "Unknown"
            question_short = (question[:30] + "...") if len(question) > 30 else question
            
            # 메트릭 점수들
            metric_scores = []
            for metric in metric_columns:
                score = row[metric]
                if pd.isna(score) or score is None:
                    metric_scores.append("N/A")
                else:
                    try:
                        # 수치형으로 변환 시도
                        numeric_score = float(score)
                        metric_scores.append(f"{numeric_score:.3f}")
                    except (ValueError, TypeError):
                        # 변환 실패 시 문자열 그대로 표시
                        metric_scores.append(str(score))
            
            table_row = f"| {i+1} | {question_short} | " + " | ".join(metric_scores) + " |"
            section.append(table_row)
        
        return "\n".join(section)
    
    def _generate_insights_and_recommendations(self, summary_data: Dict[str, Any], results_df: pd.DataFrame) -> str:
        """인사이트 및 권장사항 생성"""
        ragas_score = summary_data.get('ragas_score', 0)
        metric_stats = summary_data.get('metric_statistics', {})
        
        section = [
            "## 💡 인사이트 및 권장사항",
            ""
        ]
        
        # 전체 성능 평가
        if ragas_score >= 0.8:
            section.extend([
                "### 🎉 전체 평가",
                "전반적으로 우수한 성능을 보이고 있습니다. 현재 시스템이 효과적으로 작동하고 있습니다.",
                ""
            ])
        elif ragas_score >= 0.6:
            section.extend([
                "### 📈 전체 평가", 
                "양호한 성능을 보이나 일부 개선의 여지가 있습니다.",
                ""
            ])
        else:
            section.extend([
                "### ⚠️ 전체 평가",
                "성능 개선이 필요합니다. 시스템 최적화를 권장합니다.",
                ""
            ])
        
        # 메트릭별 권장사항
        section.append("### 🔧 메트릭별 개선 권장사항")
        section.append("")
        
        for metric_name, stats in metric_stats.items():
            avg_score = stats.get('average', 0)
            recommendation = self._get_improvement_recommendation(metric_name, avg_score)
            section.extend([
                f"**{metric_name}**:",
                f"- {recommendation}",
                ""
            ])
        
        # 일반적인 개선 방안
        section.extend([
            "### 🚀 일반적인 개선 방안",
            "",
            "1. **데이터 품질**: 고품질의 컨텍스트와 정답 데이터 확보",
            "2. **프롬프트 최적화**: LLM 프롬프트 엔지니어링을 통한 성능 개선",
            "3. **모델 튜닝**: 하이퍼파라미터 조정 및 모델 선택 최적화",
            "4. **컨텍스트 개선**: 검색 시스템의 정확도 및 관련성 향상",
            "5. **평가 기준**: 도메인 특화 평가 기준 개발",
            ""
        ])
        
        return "\n".join(section)
    
    def _generate_score_distribution_analysis(self, results_df: pd.DataFrame) -> List[str]:
        """점수 분포 분석 생성"""
        section = [
            "### 📊 점수 분포 분석",
            ""
        ]
        
        metric_columns = [col for col in results_df.columns 
                        if col not in ['question', 'answer', 'contexts', 'ground_truths', 'reference']]
        
        for metric in metric_columns:
            scores = results_df[metric].dropna()
            if len(scores) == 0:
                continue
            
            # 수치형으로 변환 가능한 데이터만 처리
            try:
                numeric_scores = pd.to_numeric(scores, errors='coerce').dropna()
                if len(numeric_scores) == 0:
                    continue
                    
                # 점수 구간별 분포
                excellent = (numeric_scores >= 0.8).sum()
                good = ((numeric_scores >= 0.6) & (numeric_scores < 0.8)).sum()
                fair = ((numeric_scores >= 0.4) & (numeric_scores < 0.6)).sum()
                poor = (numeric_scores < 0.4).sum()
                scores = numeric_scores  # 수치형 데이터로 교체
            except:
                continue
            
            section.extend([
                f"**{metric} 분포**:",
                f"- 우수 (≥0.8): {excellent}개 ({excellent/len(scores)*100:.1f}%)",
                f"- 양호 (0.6-0.8): {good}개 ({good/len(scores)*100:.1f}%)",
                f"- 보통 (0.4-0.6): {fair}개 ({fair/len(scores)*100:.1f}%)",
                f"- 미흡 (<0.4): {poor}개 ({poor/len(scores)*100:.1f}%)",
                ""
            ])
        
        return section
    
    def _generate_footer(self) -> str:
        """보고서 푸터 생성"""
        footer = [
            "---",
            "",
            "## 📝 보고서 정보",
            "",
            f"- **생성 도구**: RAGTrace Lite v0.1.0",
            f"- **생성 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **평가 프레임워크**: RAGAS",
            "",
            "이 보고서는 RAGTrace Lite에 의해 자동 생성되었습니다.",
            ""
        ]
        
        return "\n".join(footer)
    
    def _create_score_bar(self, score: float, max_score: float = 1.0, length: int = 20) -> str:
        """점수를 텍스트 막대그래프로 변환"""
        if score is None or pd.isna(score):
            return "░" * length
        
        filled_length = int((score / max_score) * length)
        filled_length = max(0, min(length, filled_length))
        
        bar = "█" * filled_length + "░" * (length - filled_length)
        return bar
    
    def _interpret_score(self, score: float) -> str:
        """점수 해석"""
        if score >= 0.9:
            return "🟢 **매우 우수** - 탁월한 성능"
        elif score >= 0.8:
            return "🟢 **우수** - 높은 품질의 결과"
        elif score >= 0.7:
            return "🟡 **양호** - 만족스러운 성능"
        elif score >= 0.6:
            return "🟡 **보통** - 개선 여지 있음"
        else:
            return "🔴 **미흡** - 상당한 개선 필요"
    
    def _interpret_metric_performance(self, metric_name: str, score: float) -> str:
        """메트릭별 성능 해석"""
        # None 값 처리
        if score is None:
            score = 0.0
        base_interpretation = self._interpret_score(score)
        
        specific_advice = {
            'faithfulness': "답변이 컨텍스트를 얼마나 충실히 반영하는지 나타냅니다.",
            'answer_relevancy': "답변이 질문과 얼마나 관련성이 높은지 보여줍니다.",
            'context_precision': "검색된 컨텍스트의 정확도를 측정합니다.",
            'context_recall': "필요한 정보가 컨텍스트에 포함된 정도를 나타냅니다.",
            'answer_correctness': "답변의 정확성과 완전성을 종합적으로 평가합니다."
        }
        
        advice = specific_advice.get(metric_name, "메트릭 성능을 나타냅니다.")
        return f"{base_interpretation} {advice}"
    
    def _get_improvement_recommendation(self, metric_name: str, score: float) -> str:
        """메트릭별 개선 권장사항"""
        if score >= 0.8:
            return "현재 성능이 우수합니다. 지속적인 모니터링을 권장합니다."
        
        recommendations = {
            'faithfulness': "답변 생성 시 컨텍스트에 더 충실하도록 프롬프트를 개선하세요.",
            'answer_relevancy': "질문-답변 매칭을 개선하고 불필요한 정보를 제거하세요.",
            'context_precision': "검색 시스템의 정확도를 높이고 노이즈를 줄이세요.",
            'context_recall': "더 포괄적인 정보 검색을 위해 검색 범위를 확대하세요.",
            'answer_correctness': "정답 데이터의 품질을 개선하고 답변 생성 로직을 최적화하세요."
        }
        
        return recommendations.get(metric_name, "시스템 성능 최적화를 권장합니다.")
    
    def save_report(self, report_content: str, output_path: str, run_id: str) -> str:
        """보고서를 파일로 저장"""
        output_file = Path(output_path) / f"{run_id}_report.md"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 보고서 저장 완료: {output_file}")
        return str(output_file)


def test_report_generator():
    """보고서 생성기 테스트"""
    print("🧪 ReportGenerator 테스트 시작")
    
    try:
        generator = ReportGenerator()
        
        # 테스트 데이터
        run_id = "test_report_001"
        
        summary_data = {
            'run_info': {
                'llm_provider': 'hcx',
                'llm_model': 'HCX-005',
                'dataset_name': 'sample.json',
                'total_items': 3,
                'status': 'completed'
            },
            'metric_statistics': {
                'faithfulness': {'average': 0.85, 'minimum': 0.78, 'maximum': 0.92, 'count': 3},
                'answer_relevancy': {'average': 0.87, 'minimum': 0.83, 'maximum': 0.90, 'count': 3}
            },
            'ragas_score': 0.86,
            'total_metrics': 2
        }
        
        results_df = pd.DataFrame({
            'faithfulness': [0.85, 0.92, 0.78],
            'answer_relevancy': [0.90, 0.88, 0.83]
        })
        
        dataset = [
            {'question': '테스트 질문 1', 'answer': '테스트 답변 1'},
            {'question': '테스트 질문 2', 'answer': '테스트 답변 2'},
            {'question': '테스트 질문 3', 'answer': '테스트 답변 3'}
        ]
        
        # 보고서 생성
        report = generator.generate_evaluation_report(run_id, summary_data, results_df, dataset)
        
        print("✅ 보고서 생성 성공")
        print(f"보고서 길이: {len(report)} 문자")
        
        # 파일로 저장 테스트
        report_file = generator.save_report(report, "test_reports", run_id)
        
        # 테스트 파일 정리
        Path(report_file).unlink(missing_ok=True)
        Path("test_reports").rmdir()
        
        print("✅ ReportGenerator 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ ReportGenerator 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_report_generator()