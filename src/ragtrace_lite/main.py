#!/usr/bin/env python3
"""
RAGTrace Lite - Main Application Class

Original work Copyright 2024 RAGTrace Contributors
Modified work Copyright 2025 RAGTrace Lite Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

This file has been modified from the original version in the RAGTrace project.
"""

import sys
import time
import traceback
from pathlib import Path
from typing import Optional
from uuid import uuid4

# Use relative imports for package modules
from .config_loader import load_config, Config
from .llm_factory import create_llm, check_llm_connection
from .data_processor import DataProcessor
from .evaluator import RagasEvaluator
from .db_manager import DatabaseManager
from .report_generator import ReportGenerator


class RAGTraceLite:
    """RAGTrace Lite 메인 애플리케이션 클래스"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        RAGTrace Lite 초기화
        
        Args:
            config_path: 설정 파일 경로 (기본값: config.yaml)
        """
        self.config = load_config(config_path)
        self.run_id = f"ragtrace_{uuid4().hex[:8]}"
        
        # 컴포넌트 초기화
        self.llm = None
        self.data_processor = DataProcessor(self.config)
        self.evaluator = None
        self.db_manager = DatabaseManager(self.config)
        self.report_generator = ReportGenerator(self.config)
        
        from . import __version__
        print(f"🚀 RAGTrace Lite v{__version__} 시작")
        print(f"📊 실행 ID: {self.run_id}")
    
    def initialize_llm(self, provider: Optional[str] = None) -> bool:
        """
        LLM 초기화 및 연결 테스트
        
        Args:
            provider: LLM 제공자 ('gemini' 또는 'hcx')
            
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            # 설정 오버라이드
            if provider:
                import os
                self.config.llm.provider = provider
                
                # API 키도 함께 업데이트
                if provider.lower() == 'gemini':
                    self.config.llm.api_key = os.getenv('GEMINI_API_KEY', '')
                    self.config.llm.model_name = 'gemini-2.5-flash'
                elif provider.lower() == 'hcx':
                    self.config.llm.api_key = os.getenv('CLOVA_STUDIO_API_KEY', '')
                    self.config.llm.model_name = 'HCX-005'
            
            print(f"🔧 LLM 초기화 중: {self.config.llm.provider.upper()}")
            print(f"   모델: {self.config.llm.model_name}")
            print(f"   API 키: {'설정됨' if self.config.llm.api_key else '없음'}")
            
            # LLM 인스턴스 생성
            self.llm = create_llm(self.config)
            
            # 연결 테스트
            if not check_llm_connection(self.llm, self.config.llm.provider):
                return False
            
            # 평가기 초기화
            self.evaluator = RagasEvaluator(config=self.config, llm=self.llm)
            
            return True
            
        except Exception as e:
            print(f"❌ LLM 초기화 실패: {e}")
            return False
    
    def evaluate_dataset(self, 
                        data_path: str, 
                        output_dir: Optional[str] = None,
                        llm_provider: Optional[str] = None) -> bool:
        """
        데이터셋 평가 수행
        
        Args:
            data_path: 평가 데이터 파일 경로
            output_dir: 결과 출력 디렉토리
            llm_provider: LLM 제공자 오버라이드
            
        Returns:
            bool: 평가 성공 여부
        """
        try:
            start_time = time.time()
            
            # LLM 초기화
            if not self.initialize_llm(llm_provider):
                return False
            
            # 1. 데이터 로딩
            print(f"\n📁 데이터 로딩: {data_path}")
            dataset = self.data_processor.load_and_prepare_data(data_path)
            
            if not dataset:
                print("❌ 데이터셋이 비어있습니다")
                return False
            
            print(f"✅ 데이터 로딩 완료: {len(dataset)}개 항목")
            
            # 2. 데이터베이스에 평가 실행 기록
            print(f"\n💾 평가 실행 기록 생성...")
            self.db_manager.create_evaluation_run(
                run_id=self.run_id,
                llm_provider=self.config.llm.provider,
                llm_model=self.config.llm.model_name or "default",
                dataset_name=Path(data_path).name,
                total_items=len(dataset),
                metrics=self.config.evaluation.metrics,
                config_data=self.config.model_dump()
            )
            
            # 3. RAGAS 평가 수행
            print(f"\n🔍 RAGAS 평가 시작...")
            print(f"   - LLM: {self.config.llm.provider.upper()}")
            print(f"   - 메트릭: {', '.join(self.config.evaluation.metrics)}")
            print(f"   - 배치 크기: {self.config.evaluation.batch_size}")
            
            results_df = self.evaluator.evaluate(dataset)
            
            if results_df is None or results_df.empty:
                print("❌ 평가 결과가 없습니다")
                return False
            
            print(f"✅ 평가 완료: {len(results_df)}개 결과")
            
            # 4. 결과 저장
            print(f"\n💾 결과 저장 중...")
            self.db_manager.save_evaluation_results(
                run_id=self.run_id,
                results_df=results_df,
                dataset=dataset
            )
            self.db_manager.complete_evaluation_run(self.run_id)
            
            # 5. 요약 통계 계산
            print(f"\n📊 통계 계산 중...")
            summary_data = self.db_manager.get_evaluation_summary(self.run_id)
            
            # 6. 보고서 생성
            print(f"\n📄 보고서 생성 중...")
            report_content = self.report_generator.generate_evaluation_report(
                run_id=self.run_id,
                summary_data=summary_data,
                results_df=results_df,
                dataset=dataset
            )
            
            # 7. 파일 저장
            output_path = output_dir or "reports"
            report_file = self.report_generator.save_report(
                report_content=report_content,
                output_path=output_path,
                run_id=self.run_id
            )
            
            # 8. 결과 요약 출력
            elapsed_time = time.time() - start_time
            self._print_evaluation_summary(summary_data, report_file, elapsed_time)
            
            return True
            
        except Exception as e:
            print(f"❌ 평가 수행 실패: {e}")
            traceback.print_exc()
            return False
    
    def _print_evaluation_summary(self, summary_data: dict, report_file: str, elapsed_time: float):
        """평가 결과 요약을 콘솔에 출력"""
        print("\n" + "="*60)
        print("🎉 RAGTrace Lite 평가 완료!")
        print("="*60)
        
        # 기본 정보
        run_info = summary_data.get('run_info', {})
        print(f"📊 실행 ID: {self.run_id}")
        print(f"🤖 LLM: {run_info.get('llm_provider', 'Unknown').upper()}")
        print(f"📁 데이터셋: {run_info.get('dataset_name', 'Unknown')}")
        print(f"📋 평가 항목: {run_info.get('total_items', 0)}개")
        print(f"⏱️  소요 시간: {elapsed_time:.1f}초")
        
        # RAGAS 점수
        ragas_score = summary_data.get('ragas_score')
        if ragas_score is not None:
            print(f"\n🎯 전체 RAGAS 점수: {ragas_score:.4f}")
            
            # 점수 해석
            if ragas_score >= 0.8:
                print("   🟢 우수한 성능!")
            elif ragas_score >= 0.6:
                print("   🟡 양호한 성능")
            else:
                print("   🔴 개선이 필요합니다")
        
        # 메트릭별 점수
        metric_stats = summary_data.get('metric_statistics', {})
        if metric_stats:
            print(f"\n📈 메트릭별 점수:")
            for metric_name, stats in metric_stats.items():
                avg_score = stats.get('average', 0)
                print(f"   {metric_name}: {avg_score:.4f}")
        
        # 파일 경로
        print(f"\n📄 상세 보고서: {report_file}")
        print(f"💾 데이터베이스: {self.db_manager.db_path}")
        print("="*60)
    
    def list_evaluations(self, limit: int = 10):
        """최근 평가 기록 목록 출력"""
        evaluations = self.db_manager.list_evaluations(limit)
        
        if not evaluations:
            print("평가 기록이 없습니다.")
            return
        
        print(f"\n📋 최근 평가 기록 ({len(evaluations)}개):")
        print("-" * 80)
        print(f"{'Run ID':<12} {'날짜':<12} {'LLM':<8} {'데이터셋':<20} {'상태':<10}")
        print("-" * 80)
        
        for eval_record in evaluations:
            run_id = eval_record['run_id'][:10] + "..."
            timestamp = eval_record['timestamp'][:10]
            provider = eval_record['llm_provider'].upper()
            dataset = eval_record['dataset_name'][:18] + "..." if len(eval_record['dataset_name']) > 18 else eval_record['dataset_name']
            status = eval_record['status']
            
            print(f"{run_id:<12} {timestamp:<12} {provider:<8} {dataset:<20} {status:<10}")
    
    def show_evaluation_details(self, run_id: str):
        """특정 평가의 상세 정보 출력"""
        try:
            summary_data = self.db_manager.get_evaluation_summary(run_id)
            
            print(f"\n📊 평가 상세 정보: {run_id}")
            print("="*50)
            
            run_info = summary_data['run_info']
            print(f"날짜: {run_info['timestamp']}")
            print(f"LLM: {run_info['llm_provider']} - {run_info.get('llm_model', 'Unknown')}")
            print(f"데이터셋: {run_info['dataset_name']}")
            print(f"평가 항목: {run_info['total_items']}개")
            print(f"상태: {run_info['status']}")
            
            # RAGAS 점수
            ragas_score = summary_data.get('ragas_score')
            if ragas_score:
                print(f"\n🎯 전체 RAGAS 점수: {ragas_score:.4f}")
            
            # 메트릭별 통계
            metric_stats = summary_data.get('metric_statistics', {})
            if metric_stats:
                print(f"\n📈 메트릭별 통계:")
                for metric_name, stats in metric_stats.items():
                    print(f"  {metric_name}:")
                    print(f"    평균: {stats['average']:.4f}")
                    print(f"    범위: {stats['minimum']:.4f} ~ {stats['maximum']:.4f}")
                    print(f"    개수: {stats['count']}")
                    
        except Exception as e:
            print(f"❌ 평가 정보 조회 실패: {e}")
    
    def cleanup(self):
        """리소스 정리"""
        if self.db_manager:
            self.db_manager.close()