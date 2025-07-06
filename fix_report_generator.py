#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAGTrace Lite Report Generator 버그 수정 패치
Windows에서 None 값 처리 오류 수정
"""

import os
import sys
from pathlib import Path

def find_report_generator():
    """report_generator.py 파일 찾기"""
    # 가능한 위치들
    possible_paths = [
        Path("ragtrace_env/Lib/site-packages/ragtrace_lite/report_generator.py"),
        Path("venv/Lib/site-packages/ragtrace_lite/report_generator.py"),
        Path(sys.prefix) / "Lib/site-packages/ragtrace_lite/report_generator.py",
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # pip show로 찾기
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "-f", "ragtrace-lite"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Location:'):
                    location = line.split(':', 1)[1].strip()
                    path = Path(location) / "ragtrace_lite" / "report_generator.py"
                    if path.exists():
                        return path
    except:
        pass
    
    return None

def patch_report_generator(file_path):
    """report_generator.py 파일 패치"""
    print(f"📁 파일 읽기: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 백업 생성
    backup_path = file_path.with_suffix('.py.bak')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 백업 생성: {backup_path}")
    
    # 패치 1: None 값 처리
    old_code1 = """        for metric_name, stats in metric_stats.items():
            description = metric_descriptions.get(metric_name, f'**{metric_name}** - 평가 메트릭')
            avg_score = stats.get('average', 0)
            
            section.extend([
                f"### {metric_name}",
                f"",
                description,
                f"",
                f"- **평균 점수**: {avg_score:.4f}",
                f"- **점수 범위**: {(stats.get('minimum', 0) or 0):.4f} ~ {(stats.get('maximum', 0) or 0):.4f}",
                f"- **평가 완료**: {stats.get('count', 0)}개 항목",
                ""
            ])"""
    
    new_code1 = """        for metric_name, stats in metric_stats.items():
            description = metric_descriptions.get(metric_name, f'**{metric_name}** - 평가 메트릭')
            avg_score = stats.get('average', 0) or 0  # None 값 처리
            min_score = stats.get('minimum', 0) or 0
            max_score = stats.get('maximum', 0) or 0
            count = stats.get('count', 0) or 0
            
            section.extend([
                f"### {metric_name}",
                f"",
                description,
                f"",
                f"- **평균 점수**: {avg_score:.4f}",
                f"- **점수 범위**: {min_score:.4f} ~ {max_score:.4f}",
                f"- **평가 완료**: {count}개 항목",
                ""
            ])"""
    
    if old_code1 in content:
        content = content.replace(old_code1, new_code1)
        print("✅ 패치 1 적용: None 값 처리")
    else:
        print("⚠️  패치 1: 이미 적용되었거나 코드를 찾을 수 없음")
    
    # 패치 2: _interpret_metric_performance 메서드
    old_code2 = """    def _interpret_metric_performance(self, metric_name: str, score: float) -> str:
        \"\"\"메트릭별 성능 해석\"\"\"
        base_interpretation = self._interpret_score(score)"""
    
    new_code2 = """    def _interpret_metric_performance(self, metric_name: str, score: float) -> str:
        \"\"\"메트릭별 성능 해석\"\"\"
        # None 값 처리
        if score is None:
            score = 0.0
        base_interpretation = self._interpret_score(score)"""
    
    if old_code2 in content:
        content = content.replace(old_code2, new_code2)
        print("✅ 패치 2 적용: _interpret_metric_performance None 처리")
    else:
        print("⚠️  패치 2: 이미 적용되었거나 코드를 찾을 수 없음")
    
    # 파일 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ 패치 완료!")

def main():
    print("=" * 60)
    print("RAGTrace Lite Report Generator 버그 수정")
    print("=" * 60)
    print()
    
    # report_generator.py 찾기
    file_path = find_report_generator()
    
    if not file_path:
        print("❌ report_generator.py 파일을 찾을 수 없습니다.")
        print("   RAGTrace Lite가 제대로 설치되었는지 확인하세요.")
        sys.exit(1)
    
    print(f"✅ 파일 발견: {file_path}")
    print()
    
    try:
        patch_report_generator(file_path)
        print("\n패치가 성공적으로 적용되었습니다!")
        print("이제 다시 실행해보세요:")
        print("  run_ragtrace.bat evaluate data\\sample.json")
    except Exception as e:
        print(f"\n❌ 패치 실패: {e}")
        print("수동으로 파일을 수정해야 할 수 있습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main()