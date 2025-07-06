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