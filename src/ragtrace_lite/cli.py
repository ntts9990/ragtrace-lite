#!/usr/bin/env python3
"""
RAGTrace Lite CLI entry point

Original work Copyright 2024 RAGTrace Contributors
Modified work Copyright 2025 RAGTrace Lite Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

This file has been created as part of the RAGTrace Lite project.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

from .main import RAGTraceLite
from . import __version__

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for ragtrace-lite CLI"""
    parser = argparse.ArgumentParser(
        description='RAGTrace Lite - Lightweight RAG Evaluation Framework'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Evaluate command
    evaluate_parser = subparsers.add_parser('evaluate', help='Run RAG evaluation')
    evaluate_parser.add_argument(
        'data_file',
        type=str,
        help='Path to evaluation data file (JSON format)'
    )
    evaluate_parser.add_argument(
        '--llm',
        type=str,
        choices=['hcx', 'gemini'],
        default=None,
        help='LLM to use for evaluation (default: from config)'
    )
    evaluate_parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path for results'
    )
    evaluate_parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    
    # List datasets command
    list_parser = subparsers.add_parser('list-datasets', help='List available datasets')
    list_parser.add_argument(
        '--data-dir',
        type=str,
        default='./data',
        help='Directory containing datasets'
    )
    
    # Version command
    version_parser = subparsers.add_parser('version', help='Show version information')
    
    # Test HCX command
    test_parser = subparsers.add_parser('test-hcx', help='Test HCX-005 & BGE-M3 setup')
    test_parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick test with minimal data'
    )
    test_parser.add_argument(
        '--full',
        action='store_true',
        help='Full pipeline test including DB and report'
    )
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser('dashboard', help='Generate web dashboard')
    dashboard_parser.add_argument(
        '--open',
        action='store_true',
        help='Open dashboard in browser after generation'
    )
    
    args = parser.parse_args()
    
    if args.command == 'evaluate':
        run_evaluation(args)
    elif args.command == 'list-datasets':
        list_datasets(args)
    elif args.command == 'version':
        show_version()
    elif args.command == 'test-hcx':
        test_hcx(args)
    elif args.command == 'dashboard':
        run_dashboard(args)
    else:
        parser.print_help()
        sys.exit(1)


def run_evaluation(args):
    """Run RAG evaluation"""
    try:
        # Create RAGTrace Lite instance
        app = RAGTraceLite(args.config)
        
        # Run evaluation
        success = app.evaluate_dataset(
            data_path=args.data_file,
            output_dir=args.output,
            llm_provider=args.llm
        )
        
        app.cleanup()
        
        if not success:
            logger.error("Evaluation failed")
            sys.exit(1)
        else:
            sys.exit(0)
        
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        sys.exit(1)


def list_datasets(args):
    """List available datasets"""
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        sys.exit(1)
    
    json_files = list(data_dir.glob("*.json"))
    xlsx_files = list(data_dir.glob("*.xlsx"))
    all_files = sorted(json_files + xlsx_files)
    
    if not all_files:
        logger.info("No datasets found in data directory")
        return
    
    logger.info(f"Available datasets in {data_dir}:")
    for file in all_files:
        logger.info(f"  - {file.name}")


def show_version():
    """Show version information"""
    print(f"RAGTrace Lite v{__version__}")
    print("Licensed under Apache-2.0")
    print("For more information: https://github.com/ntts9990/ragtrace-lite")


def test_hcx(args):
    """Test HCX-005 & BGE-M3 setup"""
    import os
    from datetime import datetime
    from .config_loader import load_config
    from .llm_factory import create_llm, check_llm_connection
    from .data_processor import DataProcessor
    from .evaluator import RagasEvaluator
    
    print("=" * 70)
    print("🧪 HCX-005 & BGE-M3 테스트")
    print("=" * 70)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. 환경 확인
    print("1️⃣ 환경 설정 확인")
    print("-" * 50)
    
    # API 키 확인
    hcx_key = os.getenv('CLOVA_STUDIO_API_KEY', '').strip()
    if hcx_key and hcx_key.startswith('nv-'):
        print(f"✅ HCX API 키: 설정됨 ({hcx_key[:10]}...)")
    else:
        print("❌ HCX API 키가 설정되지 않음")
        print("   export CLOVA_STUDIO_API_KEY='your-key' 실행 필요")
        sys.exit(1)
    
    # 설정 로드
    try:
        config = load_config()
        print(f"✅ 설정 파일 로드: config.yaml")
        print(f"   - LLM: {config.llm.provider} ({config.llm.model_name})")
        print(f"   - Embedding: {config.embedding.provider}")
    except Exception as e:
        print(f"❌ 설정 로드 실패: {e}")
        sys.exit(1)
    
    # 2. LLM 연결 테스트
    print("\n2️⃣ HCX-005 연결 테스트")
    print("-" * 50)
    
    try:
        llm = create_llm(config)
        print(f"✅ LLM 인스턴스 생성: {type(llm).__name__}")
        
        if check_llm_connection(llm, config.llm.provider):
            print("✅ HCX-005 API 연결 성공")
        else:
            print("❌ HCX-005 API 연결 실패")
            sys.exit(1)
    except Exception as e:
        print(f"❌ LLM 생성 실패: {e}")
        sys.exit(1)
    
    # 3. BGE-M3 임베딩 테스트
    print("\n3️⃣ BGE-M3 임베딩 테스트")
    print("-" * 50)
    
    if config.embedding.provider == 'bge_m3':
        print("✅ BGE-M3 설정 확인")
        model_path = Path('./models/bge-m3')
        if model_path.exists():
            print(f"✅ BGE-M3 모델 존재: {model_path}")
        else:
            print("⚠️  BGE-M3 모델이 없음 (첫 실행 시 자동 다운로드)")
    else:
        print(f"⚠️  다른 임베딩 사용 중: {config.embedding.provider}")
    
    if args.quick:
        # 빠른 테스트
        print("\n4️⃣ 빠른 기능 테스트")
        print("-" * 50)
        
        # 간단한 데이터로 테스트
        test_data = {
            'question': ['테스트 질문입니다'],
            'answer': ['테스트 답변입니다'],
            'contexts': [['테스트 컨텍스트입니다']],
            'ground_truths': [['테스트 정답입니다']]
        }
        
        try:
            from datasets import Dataset
            dataset = Dataset.from_dict(test_data)
            print("✅ 테스트 데이터셋 생성")
            
            # 평가자 생성
            evaluator = RagasEvaluator(config, llm=llm)
            print("✅ 평가자 초기화 성공")
            
            print("\n✅ 모든 구성 요소가 정상 작동합니다!")
            
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            sys.exit(1)
    
    elif args.full:
        # 전체 파이프라인 테스트
        print("\n4️⃣ 전체 파이프라인 테스트 실행")
        print("-" * 50)
        print("📌 파이프라인: 데이터 생성 → 평가 → DB 저장 → 보고서 생성")
        
        # test_full_pipeline.py의 함수 재사용
        import subprocess
        import os
        
        # API 키 환경변수 설정
        env = os.environ.copy()
        env['CLOVA_STUDIO_API_KEY'] = os.getenv('CLOVA_STUDIO_API_KEY', '')
        
        # 전체 파이프라인 스크립트 실행
        try:
            result = subprocess.run(
                [sys.executable, 'test_full_pipeline.py'],
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("\n✅ 전체 파이프라인 테스트 성공!")
            else:
                print(f"\n❌ 파이프라인 테스트 실패: {result.stderr}")
                
        except Exception as e:
            print(f"\n❌ 테스트 실행 오류: {e}")
    
    else:
        # 기본 테스트
        print("\n✅ HCX-005 & BGE-M3 설정이 올바르게 되어 있습니다.")
        print("\n사용 가능한 옵션:")
        print("  --quick : 빠른 기능 테스트")
        print("  --full  : 전체 파이프라인 테스트")
    
    print("\n" + "=" * 70)
    print(f"완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def run_dashboard(args):
    """Generate web dashboard"""
    try:
        from .web_dashboard import generate_web_dashboard
        
        dashboard_path = generate_web_dashboard()
        print(f"✅ 웹 대시보드 생성 완료: {dashboard_path}")
        
        if args.open:
            import webbrowser
            import os
            dashboard_url = f"file://{os.path.abspath(dashboard_path)}"
            webbrowser.open(dashboard_url)
            print(f"🌐 브라우저에서 대시보드 열기: {dashboard_url}")
        else:
            import os
            dashboard_url = f"file://{os.path.abspath(dashboard_path)}"
            print(f"🌐 대시보드 URL: {dashboard_url}")
            
    except Exception as e:
        logger.error(f"Dashboard generation failed: {e}")
        sys.exit(1)


def main_enhanced():
    """Entry point for enhanced CLI (ragtrace-lite-enhanced)"""
    from .main_enhanced import RAGTraceLiteEnhanced
    
    parser = argparse.ArgumentParser(
        description='RAGTrace Lite Enhanced - Advanced RAG Evaluation'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Evaluate command
    evaluate_parser = subparsers.add_parser('evaluate', help='Run RAG evaluation')
    evaluate_parser.add_argument(
        'data_file',
        type=str,
        help='Path to evaluation data file (JSON or XLSX format)'
    )
    evaluate_parser.add_argument(
        '--llm',
        type=str,
        choices=['hcx', 'gemini'],
        default=None,
        help='LLM to use for evaluation'
    )
    evaluate_parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output directory for results'
    )
    evaluate_parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    
    # List evaluations
    list_parser = subparsers.add_parser('list', help='List recent evaluations')
    list_parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Number of evaluations to show'
    )
    
    # Show details
    show_parser = subparsers.add_parser('show', help='Show evaluation details')
    show_parser.add_argument(
        'run_id',
        type=str,
        help='Run ID to show details for'
    )
    
    # Export logs
    export_parser = subparsers.add_parser('export-logs', help='Export logs for Elasticsearch')
    export_parser.add_argument(
        'output_path',
        type=str,
        help='Output file path (.ndjson)'
    )
    
    # Version
    version_parser = subparsers.add_parser('version', help='Show version information')
    
    args = parser.parse_args()
    
    if args.command == 'version':
        show_version()
        return
    
    # Create enhanced app instance
    app = RAGTraceLiteEnhanced(getattr(args, 'config', None))
    
    try:
        if args.command == 'evaluate':
            success = app.evaluate_dataset(
                args.data_file,
                output_dir=args.output,
                llm_override=args.llm
            )
            sys.exit(0 if success else 1)
        elif args.command == 'list':
            app.list_evaluations(args.limit)
        elif args.command == 'show':
            app.show_evaluation_details(args.run_id)
        elif args.command == 'export-logs':
            app.export_logs(args.output_path)
        else:
            parser.print_help()
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()