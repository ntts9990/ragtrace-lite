"""
CLI 진입점 - Windows 호환성 보장
"""

import sys
import os
from pathlib import Path

# Windows 콘솔 UTF-8 설정 (최상단)
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    # Python 3.7+ UTF-8 모드
    if sys.version_info >= (3, 7):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

import click
import logging
from datetime import datetime
import json

# 패키지 컨텍스트 보장
def ensure_package_context():
    """Windows에서 패키지 import 보장"""
    global __package__
    if __package__ is None:
        # 직접 실행된 경우
        file_path = Path(__file__).resolve()
        src_path = file_path.parent.parent
        
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        # 패키지명 설정
        __package__ = "ragtrace_lite"

ensure_package_context()

# 이제 절대 import 사용
from ragtrace_lite.core.excel_parser import ExcelParser
from ragtrace_lite.core.evaluator import Evaluator
from ragtrace_lite.core.adaptive_evaluator import AdaptiveEvaluator
from ragtrace_lite.db.manager import DatabaseManager
from ragtrace_lite.stats.window_compare import WindowComparator
from ragtrace_lite.report.generator import ReportGenerator, ReportFormat
from ragtrace_lite import __version__
from ragtrace_lite.config.logging_setup import setup_logging

logger = logging.getLogger(__name__)


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx, debug):
    """RAGTrace Lite v2.0 - Cross-platform RAG Evaluation Tool"""
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug
    
    setup_logging(debug) # 중앙 로깅 설정 호출
    
    if debug:
        logger.debug(f"Python: {sys.version}")
        logger.debug(f"Platform: {sys.platform}")
        logger.debug(f"CWD: {os.getcwd()}")
        logger.debug(f"Package: {__package__}")


@cli.command()
@click.option('--excel', '-e', required=True, 
              type=click.Path(exists=True, path_type=Path),
              help='Excel file with data and env_ columns')
@click.option('--name', '-n', default='', help='Evaluation name')
@click.option('--output', '-o', type=click.Path(path_type=Path), 
              default='results', help='Output directory')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompts')
@click.pass_context
def evaluate(ctx, excel, name, output, yes):
    """Run evaluation with Excel file"""
    
    try:
        # Path 객체로 변환 (Windows 호환)
        excel_path = Path(excel).resolve()
        
        if not excel_path.exists():
            raise FileNotFoundError(f"File not found: {excel_path}")
        
        # Windows에서 파일 열림 확인
        if sys.platform == 'win32':
            try:
                with open(excel_path, 'rb'):
                    pass
            except PermissionError:
                click.echo("❌ Excel file is open. Please close it first.", err=True)
                sys.exit(1)
        
        # Excel 파싱
        click.echo(f"📊 Loading: {excel_path}")
        parser = ExcelParser(str(excel_path))
        dataset, environment, dataset_hash, dataset_items = parser.parse()
        
        # 환경 정보 출력
        click.echo(f"\n📋 Dataset: {dataset_items} items (hash: {dataset_hash[:8]}...)")
        
        if environment:
            click.echo("\n⚙️  Environment Conditions:")
            for key, value in sorted(environment.items()):
                click.echo(f"    {key}: {value}")
        
        # 평가 실행 (--yes 플래그 처리)
        if yes or click.confirm("\n▶️  Proceed with evaluation?"):
            run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            click.echo(f"\n🚀 Starting: {run_id}")
            
            # Adaptive Evaluator 사용 (동적 배치 크기)
            evaluator = AdaptiveEvaluator()
            results = evaluator.evaluate(dataset, environment)
            
            # DB 저장 (Windows 안전 경로)
            db_path = Path("ragtrace.db").resolve()
            db = DatabaseManager(str(db_path))
            
            success = db.save_evaluation(
                run_id=run_id,
                dataset_name=excel_path.stem,
                dataset_hash=dataset_hash,
                dataset_items=dataset_items,
                environment=environment,
                metrics=results['metrics'],
                details=results['details']
            )
            
            if success:
                click.echo(f"\n✅ Completed!")
                for metric, score in results['metrics'].items():
                    click.echo(f"    {metric}: {score:.3f}")
                
                # 보고서 생성
                report_gen = ReportGenerator()
                report_path = report_gen.generate_report(
                    run_id=run_id,
                    results=results,
                    environment=environment,
                    output_path=output / f"{run_id}_report.html",
                    dataset_name=excel_path.stem
                )
                click.echo(f"\n📄 Report: {report_path}")
            else:
                click.echo("❌ Failed to save results", err=True)
                
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=ctx.obj.get('debug'))
        click.echo(f"❌ Error: {e}", err=True)
        
        if sys.platform == 'win32':
            click.echo("\n💡 Windows Troubleshooting:", err=True)
            click.echo("  1. Close Excel file if open", err=True)
            click.echo("  2. Check file path (use / or \\\\)", err=True)
            click.echo("  3. Run as Administrator if needed", err=True)
        
        sys.exit(1)


@cli.command()
@click.option('--a-start', required=True, help='Window A start date (YYYY-MM-DD)')
@click.option('--a-end', required=True, help='Window A end date')
@click.option('--b-start', required=True, help='Window B start date')
@click.option('--b-end', required=True, help='Window B end date')
@click.option('--metric', '-m', default='ragas_score', help='Metric to compare')
@click.option('--where', '-w', multiple=True, help='Environment filters (key=value)')
@click.option('--alpha', default=0.05, type=float, help='Significance level')
@click.option('--output', '-o', type=click.Path(path_type=Path), 
              default='results', help='Output directory')
def compare_windows(a_start, a_end, b_start, b_end, metric, where, alpha, output):
    """Compare two time windows statistically"""
    
    try:
        # 환경 필터 파싱
        env_filters = {}
        if where:
            for condition in where:
                if '=' in condition:
                    key, value = condition.split('=', 1)
                    env_filters[key.strip()] = value.strip()
        
        # 비교 정보 출력
        click.echo("📊 Window Comparison:")
        click.echo(f"  Window A: {a_start} to {a_end}")
        click.echo(f"  Window B: {b_start} to {b_end}")
        click.echo(f"  Metric: {metric}")
        if env_filters:
            click.echo(f"  Filters: {env_filters}")
        
        # 통계 비교 실행
        db = DatabaseManager()
        comparator = WindowComparator(db)
        
        result = comparator.compare_windows(
            window_a=(a_start, a_end),
            window_b=(b_start, b_end),
            metric=metric,
            env_filters=env_filters,
            mode='run_mean',  # 단순화: run_mean만 지원
            alpha=alpha
        )
        
        # 경고 출력
        if result.warnings:
            click.echo("\n⚠️  Warnings:")
            for warning in result.warnings:
                click.echo(f"  - {warning}")
        
        # 결과 출력
        click.echo(f"\n📈 Results for {result.metric_name}:")
        click.echo(f"\nWindow A ({result.window_a['runs']} runs):")
        click.echo(f"  Mean: {result.stats_a['mean']:.4f} ± {result.stats_a['std']:.4f}")
        click.echo(f"  95% CI: [{result.confidence_interval_a[0]:.4f}, "
                  f"{result.confidence_interval_a[1]:.4f}]")
        
        click.echo(f"\nWindow B ({result.window_b['runs']} runs):")
        click.echo(f"  Mean: {result.stats_b['mean']:.4f} ± {result.stats_b['std']:.4f}")
        click.echo(f"  95% CI: [{result.confidence_interval_b[0]:.4f}, "
                  f"{result.confidence_interval_b[1]:.4f}]")
        
        # 변화량
        if result.improvement > 0:
            click.echo(f"\n📊 Change: ↑ {result.improvement:.4f} "
                      f"({result.improvement_pct:+.1f}%)")
        elif result.improvement < 0:
            click.echo(f"\n📊 Change: ↓ {abs(result.improvement):.4f} "
                      f"({result.improvement_pct:.1f}%)")
        else:
            click.echo("\n📊 Change: → No change")
        
        # 통계적 유의성
        click.echo(f"\n🔬 Statistical Test: {result.test_type}")
        if result.p_value is not None:
            if result.significant:
                click.echo(f"  ✅ Significant (p = {result.p_value:.4f} < {alpha})")
            else:
                click.echo(f"  ❌ Not significant (p = {result.p_value:.4f} ≥ {alpha})")
            
            if result.cohens_d:
                click.echo(f"  Effect size: {result.effect_size} (d = {result.cohens_d:.3f})")
        
        # CI 중첩
        if result.ci_overlap:
            click.echo("  ⚠️  Confidence intervals overlap")
        
        # 보고서 생성
        report_gen = ReportGenerator()
        report_path = report_gen.generate_comparison_report(result, output)
        click.echo(f"\n📄 Report saved: {report_path}")
            
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def create_template():
    """Create Excel template with env_ columns"""
    
    try:
        output_path = f"template_{datetime.now().strftime('%Y%m%d')}.xlsx"
        ExcelParser.create_template(output_path)
        
        click.echo(f"✅ Template created: {output_path}")
        click.echo("\n📝 Usage:")
        click.echo("  1. Fill in your test data (question, answer, contexts, ground_truth)")
        click.echo("  2. Set environment values in env_ columns (first row)")
        click.echo("  3. Add custom env_ columns as needed")
        click.echo(f"  4. Run: ragtrace evaluate --excel {output_path}")
        
    except Exception as e:
        logger.error(f"Template creation failed: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def list_env():
    """List all environment keys and their usage"""
    
    try:
        db = DatabaseManager()
        stats = db.get_environment_stats()
        
        if not stats:
            click.echo("No environment data found.")
            return
        
        click.echo("📋 Environment Keys Usage:")
        click.echo("-" * 60)
        
        for key, values in stats.items():
            click.echo(f"\n🔑 {key}")
            for val_info in values[:5]:  # Top 5 values
                click.echo(f"  '{val_info['value']}': {val_info['count']} times")
                click.echo(f"    First: {val_info['first_used'][:10]}")
                click.echo(f"    Last: {val_info['last_used'][:10]}")
            
            if len(values) > 5:
                click.echo(f"  ... and {len(values) - 5} more values")
                
    except Exception as e:
        logger.error(f"Failed to list environment keys: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--limit', '-l', default=20, type=int, help='Number of runs to show')
def history(limit):
    """Show evaluation history"""
    
    try:
        db = DatabaseManager()
        runs = db.get_all_runs(limit)
        
        if not runs:
            click.echo("No evaluation runs found.")
            return
        
        click.echo("📚 Evaluation History:")
        click.echo("-" * 80)
        
        for run in runs:
            click.echo(f"\n🔹 {run['run_id']}")
            click.echo(f"   Date: {run['timestamp'][:19]}")
            click.echo(f"   Dataset: {run['dataset_name']}")
            click.echo(f"   Items: {run['dataset_items']}")
            click.echo(f"   Score: {run['ragas_score']:.3f}" if run['ragas_score'] else "   Score: N/A")
            click.echo(f"   Status: {run['status']}")
            
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


def main():
    """Entry point for console script"""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"\n❌ Fatal error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()