"""
RAGTrace Lite Database Manager

SQLite 데이터베이스 관리:
- 평가 결과 저장
- 기존 RAGTrace 스키마 호환
- 통계 계산 및 조회
- 데이터베이스 초기화
"""

import sqlite3
import pandas as pd
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from uuid import uuid4

from .config_loader import Config


class DatabaseManager:
    """RAGTrace Lite SQLite 데이터베이스 관리 클래스"""
    
    def __init__(self, config: Optional[Config] = None, db_path: Optional[str] = None):
        """
        데이터베이스 매니저 초기화
        
        Args:
            config: RAGTrace Lite 설정
            db_path: 데이터베이스 파일 경로 (config보다 우선)
        """
        if db_path:
            self.db_path = Path(db_path)
        elif config:
            self.db_path = Path(config.database.path)
        else:
            self.db_path = Path("db/ragtrace_lite.db")
        
        # 디렉토리 생성
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 데이터베이스 연결
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # 딕셔너리 스타일 접근
        
        # 테이블 초기화
        self._create_tables()
        
        print(f"📀 데이터베이스 초기화 완료: {self.db_path}")
    
    def _create_tables(self):
        """필요한 테이블들을 생성합니다."""
        cursor = self.conn.cursor()
        
        # 평가 메타데이터 테이블
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT UNIQUE NOT NULL,
            timestamp DATETIME NOT NULL,
            llm_provider TEXT NOT NULL,
            llm_model TEXT,
            dataset_name TEXT,
            total_items INTEGER,
            metrics TEXT,  -- JSON 배열
            config_data TEXT,  -- JSON 설정
            status TEXT DEFAULT 'running',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME
        )
        """)
        
        # 개별 결과 테이블 (기존 RAGTrace 호환)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluation_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            item_index INTEGER NOT NULL,
            question TEXT,
            answer TEXT,
            contexts TEXT,  -- JSON 배열
            ground_truth TEXT,
            metric_name TEXT NOT NULL,
            metric_score REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES evaluations (run_id)
        )
        """)
        
        # 인덱스 생성
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_run_id ON evaluation_results (run_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metric ON evaluation_results (metric_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON evaluations (timestamp)")
        
        self.conn.commit()
        print("✅ 데이터베이스 테이블 생성 완료")
    
    def create_evaluation_run(self, 
                            run_id: str,
                            llm_provider: str,
                            llm_model: str,
                            dataset_name: str,
                            total_items: int,
                            metrics: List[str],
                            config_data: Dict[str, Any]) -> str:
        """
        새로운 평가 실행을 생성합니다.
        
        Args:
            run_id: 실행 ID
            llm_provider: LLM 제공자
            llm_model: LLM 모델명
            dataset_name: 데이터셋 이름
            total_items: 총 아이템 수
            metrics: 평가 메트릭 목록
            config_data: 설정 데이터
            
        Returns:
            str: 생성된 run_id
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
        INSERT INTO evaluations 
        (run_id, timestamp, llm_provider, llm_model, dataset_name, total_items, metrics, config_data, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'running')
        """, (
            run_id,
            datetime.now(),
            llm_provider,
            llm_model,
            dataset_name,
            total_items,
            json.dumps(metrics),
            json.dumps(config_data),
        ))
        
        self.conn.commit()
        print(f"📊 평가 실행 생성: {run_id}")
        return run_id
    
    def save_evaluation_results(self, 
                              run_id: str, 
                              results_df: pd.DataFrame,
                              dataset) -> None:
        """
        평가 결과를 데이터베이스에 저장합니다.
        
        Args:
            run_id: 실행 ID
            results_df: 평가 결과 DataFrame
            dataset: 원본 데이터셋 (질문, 답변 등)
        """
        cursor = self.conn.cursor()
        
        print(f"💾 평가 결과 저장 중: {run_id}")
        
        # 원본 데이터와 결과를 결합
        for i, result_row in results_df.iterrows():
            # 원본 데이터 가져오기
            original_data = dataset[i]
            
            question = original_data.get('question', '')
            answer = original_data.get('answer', '')
            contexts = json.dumps(original_data.get('contexts', []), ensure_ascii=False)
            ground_truth = original_data.get('ground_truth', '') or original_data.get('reference', '')
            
            # 각 메트릭별로 결과 저장
            # 메트릭 컬럼만 처리 (메타데이터 제외)
            metric_columns = ['faithfulness', 'answer_relevancy', 'context_precision', 
                            'context_recall', 'answer_correctness']
            
            for metric_name in metric_columns:
                if metric_name not in results_df.columns:
                    continue  # 해당 메트릭이 없으면 스킵
                
                metric_score = result_row[metric_name]
                
                # NaN 값 처리 - 배열인 경우 첫 번째 값 사용
                if isinstance(metric_score, (list, np.ndarray)):
                    metric_score = float(metric_score[0]) if len(metric_score) > 0 else None
                elif pd.isna(metric_score):
                    metric_score = None
                else:
                    metric_score = float(metric_score)
                
                cursor.execute("""
                INSERT INTO evaluation_results 
                (run_id, item_index, question, answer, contexts, ground_truth, metric_name, metric_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_id,
                    i,
                    question,
                    answer,
                    contexts,
                    ground_truth,
                    metric_name,
                    metric_score
                ))
        
        self.conn.commit()
        print(f"✅ 평가 결과 저장 완료: {len(results_df)} 항목")
    
    def complete_evaluation_run(self, run_id: str) -> None:
        """평가 실행을 완료 상태로 업데이트합니다."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
        UPDATE evaluations 
        SET status = 'completed', completed_at = ?
        WHERE run_id = ?
        """, (datetime.now(), run_id))
        
        self.conn.commit()
        print(f"🎉 평가 실행 완료: {run_id}")
    
    def get_evaluation_summary(self, run_id: str) -> Dict[str, Any]:
        """특정 실행에 대한 요약 통계를 반환합니다."""
        cursor = self.conn.cursor()
        
        # 기본 정보
        cursor.execute("""
        SELECT * FROM evaluations WHERE run_id = ?
        """, (run_id,))
        
        eval_info = dict(cursor.fetchone() or {})
        
        if not eval_info:
            raise ValueError(f"평가 실행을 찾을 수 없습니다: {run_id}")
        
        # 메트릭별 통계
        cursor.execute("""
        SELECT 
            metric_name,
            COUNT(*) as count,
            AVG(metric_score) as average,
            MIN(metric_score) as minimum,
            MAX(metric_score) as maximum,
            SUM(CASE WHEN metric_score IS NULL THEN 1 ELSE 0 END) as null_count
        FROM evaluation_results 
        WHERE run_id = ? AND metric_score IS NOT NULL
        GROUP BY metric_name
        ORDER BY metric_name
        """, (run_id,))
        
        metric_stats = {}
        for row in cursor.fetchall():
            metric_stats[row['metric_name']] = {
                'count': row['count'],
                'average': round(row['average'], 4) if row['average'] else None,
                'minimum': round(row['minimum'], 4) if row['minimum'] else None,
                'maximum': round(row['maximum'], 4) if row['maximum'] else None,
                'null_count': row['null_count']
            }
        
        # 전체 RAGAS 점수 계산
        if metric_stats:
            valid_averages = [stats['average'] for stats in metric_stats.values() 
                            if stats['average'] is not None]
            ragas_score = sum(valid_averages) / len(valid_averages) if valid_averages else None
        else:
            ragas_score = None
        
        return {
            'run_info': eval_info,
            'metric_statistics': metric_stats,
            'ragas_score': round(ragas_score, 4) if ragas_score else None,
            'total_metrics': len(metric_stats),
            'successful_evaluations': sum(stats['count'] for stats in metric_stats.values())
        }
    
    def get_evaluation_details(self, run_id: str) -> pd.DataFrame:
        """특정 실행의 상세 결과를 DataFrame으로 반환합니다."""
        query = """
        SELECT 
            item_index,
            question,
            answer,
            contexts,
            ground_truth,
            metric_name,
            metric_score
        FROM evaluation_results 
        WHERE run_id = ?
        ORDER BY item_index, metric_name
        """
        
        return pd.read_sql_query(query, self.conn, params=(run_id,))
    
    def list_evaluations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 평가 실행 목록을 반환합니다."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
        SELECT 
            run_id,
            timestamp,
            llm_provider,
            llm_model,
            dataset_name,
            total_items,
            status,
            completed_at
        FROM evaluations 
        ORDER BY timestamp DESC 
        LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_performance_trends(self, metric_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """특정 메트릭의 성능 트렌드를 반환합니다."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
        SELECT 
            e.run_id,
            e.timestamp,
            e.llm_provider,
            AVG(er.metric_score) as average_score
        FROM evaluations e
        JOIN evaluation_results er ON e.run_id = er.run_id
        WHERE er.metric_name = ? AND er.metric_score IS NOT NULL
        GROUP BY e.run_id, e.timestamp, e.llm_provider
        ORDER BY e.timestamp DESC
        LIMIT ?
        """, (metric_name, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_evaluations(self, keep_days: int = 30) -> int:
        """오래된 평가 결과를 정리합니다."""
        cursor = self.conn.cursor()
        
        cutoff_date = datetime.now().replace(day=datetime.now().day - keep_days)
        
        # 결과 삭제
        cursor.execute("""
        DELETE FROM evaluation_results 
        WHERE run_id IN (
            SELECT run_id FROM evaluations 
            WHERE timestamp < ?
        )
        """, (cutoff_date,))
        
        results_deleted = cursor.rowcount
        
        # 평가 메타데이터 삭제
        cursor.execute("""
        DELETE FROM evaluations 
        WHERE timestamp < ?
        """, (cutoff_date,))
        
        evaluations_deleted = cursor.rowcount
        
        self.conn.commit()
        
        print(f"🧹 정리 완료: {evaluations_deleted}개 평가, {results_deleted}개 결과")
        return evaluations_deleted
    
    def export_evaluation_data(self, run_id: str, output_path: str) -> None:
        """평가 데이터를 CSV로 내보냅니다."""
        details_df = self.get_evaluation_details(run_id)
        
        # 피벗하여 메트릭을 컬럼으로 변환
        pivot_df = details_df.pivot_table(
            index=['item_index', 'question', 'answer', 'contexts', 'ground_truth'],
            columns='metric_name',
            values='metric_score',
            aggfunc='first'
        ).reset_index()
        
        # 컬럼명 정리
        pivot_df.columns.name = None
        
        # CSV 저장
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        pivot_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"📄 평가 데이터 내보내기 완료: {output_file}")
    
    def close(self):
        """데이터베이스 연결을 닫습니다."""
        if self.conn:
            self.conn.close()
            print("📀 데이터베이스 연결 종료")


def test_database_manager():
    """데이터베이스 매니저 테스트 함수"""
    print("🧪 DatabaseManager 테스트 시작")
    
    try:
        # 테스트용 DB
        db_manager = DatabaseManager(db_path="test_ragtrace_lite.db")
        
        # 테스트 평가 실행 생성
        run_id = f"test_{uuid4().hex[:8]}"
        db_manager.create_evaluation_run(
            run_id=run_id,
            llm_provider="hcx",
            llm_model="HCX-005",
            dataset_name="sample.json",
            total_items=3,
            metrics=["faithfulness", "answer_relevancy"],
            config_data={"temperature": 0.5, "max_tokens": 1000}
        )
        
        # 테스트 결과 데이터 생성
        test_results = pd.DataFrame({
            'faithfulness': [0.85, 0.92, 0.78],
            'answer_relevancy': [0.90, 0.88, 0.83]
        })
        
        test_dataset = [
            {'question': '테스트 질문 1', 'answer': '테스트 답변 1', 'contexts': ['컨텍스트 1'], 'ground_truth': '정답 1'},
            {'question': '테스트 질문 2', 'answer': '테스트 답변 2', 'contexts': ['컨텍스트 2'], 'ground_truth': '정답 2'},
            {'question': '테스트 질문 3', 'answer': '테스트 답변 3', 'contexts': ['컨텍스트 3'], 'ground_truth': '정답 3'}
        ]
        
        # 결과 저장
        db_manager.save_evaluation_results(run_id, test_results, test_dataset)
        db_manager.complete_evaluation_run(run_id)
        
        # 요약 통계 확인
        summary = db_manager.get_evaluation_summary(run_id)
        print(f"✅ 요약 통계:")
        print(f"   - RAGAS Score: {summary['ragas_score']}")
        print(f"   - 총 메트릭: {summary['total_metrics']}개")
        
        # 평가 목록 확인
        evaluations = db_manager.list_evaluations(limit=5)
        print(f"✅ 최근 평가: {len(evaluations)}개")
        
        # 정리
        db_manager.close()
        
        # 테스트 DB 파일 삭제
        Path("test_ragtrace_lite.db").unlink(missing_ok=True)
        
        print("✅ DatabaseManager 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ DatabaseManager 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_database_manager()