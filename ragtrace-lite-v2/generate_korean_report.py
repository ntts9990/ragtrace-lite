#!/usr/bin/env python
"""Generate Korean HTML report with detailed statistics"""

import sys
from pathlib import Path
from datetime import datetime
import random

sys.path.insert(0, 'src')

from ragtrace_lite.report.korean_html_generator import KoreanHTMLReportGenerator

def create_realistic_results():
    """실제와 유사한 평가 결과 생성"""
    
    # 실제 RAG 시스템의 일반적인 점수 패턴
    metrics = {
        'faithfulness': 0.823,      # 보통 높음
        'answer_relevancy': 0.456,  # 종종 낮음 - 관련 없는 답변
        'context_precision': 0.692, # 중간 정도
        'context_recall': 0.914,    # 검색은 잘 됨
        'answer_correctness': 0.381, # 정확도 문제 
        'ragas_score': 0.653        # 종합 점수
    }
    
    # 샘플별 상세 결과 (변동성 있게)
    details = []
    for i in range(20):  # 20개 샘플
        details.append({
            'question': f'질문 {i+1}',
            'faithfulness': random.gauss(0.82, 0.12),  # 평균 0.82, 표준편차 0.12
            'answer_relevancy': random.gauss(0.45, 0.18),  # 높은 변동성
            'context_precision': random.gauss(0.69, 0.08),
            'context_recall': random.gauss(0.91, 0.05),  # 안정적
            'answer_correctness': random.gauss(0.38, 0.15)  # 낮고 불안정
        })
    
    return {'metrics': metrics, 'details': details}

def create_good_results():
    """우수한 성능 결과"""
    metrics = {
        'faithfulness': 0.923,
        'answer_relevancy': 0.856,
        'context_precision': 0.892,
        'context_recall': 0.914,
        'answer_correctness': 0.881,
        'ragas_score': 0.893
    }
    
    details = []
    for i in range(15):
        details.append({
            'question': f'질문 {i+1}',
            'faithfulness': random.gauss(0.92, 0.05),
            'answer_relevancy': random.gauss(0.85, 0.06),
            'context_precision': random.gauss(0.89, 0.04),
            'context_recall': random.gauss(0.91, 0.03),
            'answer_correctness': random.gauss(0.88, 0.05)
        })
    
    return {'metrics': metrics, 'details': details}

def create_poor_results():
    """개선 필요 성능 결과"""
    metrics = {
        'faithfulness': 0.423,
        'answer_relevancy': 0.356,
        'context_precision': 0.492,
        'context_recall': 0.514,
        'answer_correctness': 0.281,
        'ragas_score': 0.413
    }
    
    details = []
    for i in range(10):
        details.append({
            'question': f'질문 {i+1}',
            'faithfulness': random.gauss(0.42, 0.08),
            'answer_relevancy': random.gauss(0.35, 0.10),
            'context_precision': random.gauss(0.49, 0.07),
            'context_recall': random.gauss(0.51, 0.09),
            'answer_correctness': random.gauss(0.28, 0.08)
        })
    
    return {'metrics': metrics, 'details': details}

def main():
    print("="*70)
    print("RAGTrace 한국어 보고서 생성 데모")
    print("="*70)
    
    generator = KoreanHTMLReportGenerator()
    
    # 세 가지 시나리오 테스트
    scenarios = [
        ("보통 성능", create_realistic_results(), "customer_qa_dataset"),
        ("우수 성능", create_good_results(), "premium_dataset"),
        ("개선 필요", create_poor_results(), "test_dataset")
    ]
    
    generated_reports = []
    
    for scenario_name, results, dataset_name in scenarios:
        print(f"\n📊 {scenario_name} 시나리오 보고서 생성 중...")
        
        environment = {
            'model': 'HCX-005',
            'temperature': 0.1,
            'dataset': dataset_name,
            'embeddings': 'BGE-M3 (로컬)',
            'batch_size': 5,
            'rate_limit': '5초',
            'evaluation_time': f'{random.uniform(1.5, 4.2):.1f}분'
        }
        
        run_id = f"kr_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{scenario_name.replace(' ', '_')}"
        
        html_content = generator.generate_evaluation_report(
            run_id=run_id,
            results=results,
            environment=environment,
            dataset_name=dataset_name
        )
        
        # 파일 저장
        output_path = Path('results') / f'{run_id}.html'
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        generated_reports.append((scenario_name, output_path))
        print(f"   ✅ 저장 완료: {output_path}")
    
    print("\n" + "="*70)
    print("📋 생성된 보고서 요약")
    print("="*70)
    
    for scenario, path in generated_reports:
        print(f"\n🔹 {scenario}:")
        print(f"   파일: {path}")
        print(f"   크기: {path.stat().st_size:,} bytes")
    
    print("\n" + "="*70)
    print("✨ 보고서 특징:")
    print("="*70)
    print("• 깔끔한 한국어 UI")
    print("• 상세한 통계 분석 (평균, 표준편차, 사분위수)")
    print("• 메트릭별 색상 코딩 (우수/양호/개선필요)")
    print("• 인터랙티브 차트 (Radar, Bar)")
    print("• 맞춤형 개선 권장사항")
    print("• 반응형 디자인 (모바일 지원)")
    print("\n브라우저에서 HTML 파일을 열어 확인하세요!")
    
    # 첫 번째 보고서 내용 일부 출력
    print("\n" + "="*70)
    print("📄 보고서 미리보기 (보통 성능):")
    print("="*70)
    
    with open(generated_reports[0][1], 'r', encoding='utf-8') as f:
        content = f.read()
        # 주요 섹션 추출
        if '전체 평가' in content:
            start = content.find('<h5>📊 전체 평가</h5>')
            end = content.find('</div>', start + 100)
            if start > 0 and end > 0:
                preview = content[start:end]
                # HTML 태그 제거 (간단한 방법)
                import re
                preview_text = re.sub('<[^<]+?>', '', preview)
                print(preview_text[:300])

if __name__ == "__main__":
    main()