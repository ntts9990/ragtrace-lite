"""데이터베이스 관리자 - EAV 패턴 구현"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
from contextlib import contextmanager
import numpy as np

from .schema import SCHEMAS, INDEXES, SCHEMA_VERSION
from .migrations import migrate_database

# Import Pydantic models
try:
    from ..models.evaluation import (
        EvaluationResult, EvaluationMetrics, EvaluationItem, 
        EvaluationConfig, EvaluationEnvironment, EvaluationStatus
    )
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    logger.warning("Pydantic models not available, using legacy dict-based approach")

logger = logging.getLogger(__name__)


class DatabaseManager:
    """EAV 패턴을 사용한 확장 가능한 DB 관리자"""
    
    def __init__(self, db_path: str = "ragtrace.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """컨텍스트 관리자로 DB 연결 관리"""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,  # Windows에서 충분한 타임아웃
            isolation_level='DEFERRED'
        )
        conn.row_factory = sqlite3.Row  # dict-like 접근 가능
        
        # 성능 최적화
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """데이터베이스 스키마 초기화 및 마이그레이션"""
        # 마이그레이션 먼저 실행 (기존 테이블 업데이트)
        migrate_database(self.db_path)
        
        with self.get_connection() as conn:
            # 테이블 생성 (IF NOT EXISTS이므로 안전)
            for table_name, schema_sql in SCHEMAS.items():
                try:
                    conn.execute(schema_sql)
                except sqlite3.OperationalError as e:
                    logger.warning(f"Table {table_name} creation issue (likely already exists): {e}")
            
            # 인덱스 생성 (IF NOT EXISTS이므로 안전)
            for index_sql in INDEXES:
                try:
                    conn.execute(index_sql)
                except sqlite3.OperationalError as e:
                    # 컬럼이 없는 경우 인덱스 생성을 건너뜁니다
                    if "no such column" in str(e):
                        logger.warning(f"Skipping index creation due to missing column: {e}")
                    else:
                        logger.warning(f"Index creation issue: {e}")
        
        logger.info(f"Database initialized at {self.db_path}")
    
    def save_evaluation(
        self,
        run_id: str,
        dataset_name: str,
        dataset_hash: str,
        dataset_items: int,
        environment: Dict[str, Any],
        metrics: Dict[str, float],
        details: List[Dict],
        llm: str = "hcx-005",
        config: Optional[Dict] = None
    ) -> bool:
        """평가 결과 저장"""
        try:
            with self.get_connection() as conn:
                # 1. evaluations 테이블 저장
                ragas_score = sum(metrics.values()) / len(metrics) if metrics else 0.0
                
                conn.execute("""
                    INSERT INTO evaluations (
                        run_id, timestamp, llm, dataset_name, dataset_hash,
                        dataset_items, total_items, metrics, config_data,
                        environment_json, ragas_score, faithfulness, 
                        answer_relevancy, context_precision, context_recall, 
                        answer_correctness, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_id,
                    datetime.now().isoformat(),
                    llm,
                    dataset_name,
                    dataset_hash,
                    dataset_items,
                    len(details),
                    json.dumps(metrics, ensure_ascii=False),
                    json.dumps(config or {}, ensure_ascii=False),
                    json.dumps(environment, ensure_ascii=False),
                    ragas_score,
                    metrics.get('faithfulness'),
                    metrics.get('answer_relevancy'),
                    metrics.get('context_precision'),
                    metrics.get('context_recall'),
                    metrics.get('answer_correctness'),
                    'completed'
                ))
                
                # 2. 환경 키-값 저장 (EAV)
                if environment:
                    env_data = [
                        (run_id, key, str(value))
                        for key, value in environment.items()
                    ]
                    conn.executemany(
                        "INSERT INTO evaluation_env (run_id, key, value) VALUES (?, ?, ?)",
                        env_data
                    )
                
                # 3. 메트릭 요약 저장
                if metrics and details:
                    self._save_metric_summary(conn, run_id, details, metrics)
                
                # 4. 상세 결과 저장
                if details:
                    self._save_evaluation_items(conn, run_id, details)
                
                logger.info(f"Saved evaluation: {run_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save evaluation: {e}")
            return False
    
    def _save_metric_summary(
        self,
        conn: sqlite3.Connection,
        run_id: str,
        details: List[Dict],
        metrics: Dict[str, float]
    ):
        """메트릭 요약 통계 저장"""
        for metric_name in metrics.keys():
            # 상세 결과에서 메트릭 값 추출
            values = []
            for item in details:
                if metric_name in item and item[metric_name] is not None:
                    values.append(float(item[metric_name]))
            
            if values:
                arr = np.array(values)
                conn.execute("""
                    INSERT INTO evaluation_metric_summary (
                        run_id, metric_name, avg_score, min_score, max_score, std_score, count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_id,
                    metric_name,
                    float(np.mean(arr)),
                    float(np.min(arr)),
                    float(np.max(arr)),
                    float(np.std(arr)) if len(values) > 1 else 0.0,
                    len(values)
                ))
    
    def _save_evaluation_items(
        self,
        conn: sqlite3.Connection,
        run_id: str,
        details: List[Dict]
    ):
        """평가 항목별 상세 결과 저장"""
        items_data = []
        
        for idx, item in enumerate(details):
            # contexts가 리스트인 경우 JSON으로 변환
            contexts = item.get('contexts', [])
            if isinstance(contexts, list):
                contexts = json.dumps(contexts, ensure_ascii=False)
            
            items_data.append((
                run_id,
                idx,
                item.get('question', ''),
                item.get('answer', ''),
                contexts,
                item.get('ground_truth', ''),
                item.get('faithfulness'),
                item.get('answer_relevancy'),
                item.get('context_precision'),
                item.get('context_recall'),
                item.get('answer_correctness')
            ))
        
        conn.executemany("""
            INSERT INTO evaluation_items (
                run_id, item_index, question, answer, contexts, ground_truth,
                faithfulness, answer_relevancy, context_precision,
                context_recall, answer_correctness
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, items_data)
    
    def get_runs_by_window(
        self,
        start_date: str,
        end_date: str,
        env_filters: Optional[Dict[str, str]] = None
    ) -> List[Dict]:
        """시간 윈도우와 환경 필터로 실행 조회"""
        with self.get_connection() as conn:
            query = """
                SELECT DISTINCT e.*
                FROM evaluations e
                WHERE e.timestamp BETWEEN ? AND ?
                  AND e.status = 'completed'
            """
            params = [start_date, end_date]
            
            # 환경 필터 추가
            if env_filters:
                for key, value in env_filters.items():
                    query += """
                        AND EXISTS (
                            SELECT 1 FROM evaluation_env env
                            WHERE env.run_id = e.run_id
                              AND env.key = ?
                              AND env.value = ?
                        )
                    """
                    params.extend([key, value])
            
            query += " ORDER BY e.timestamp"
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_metric_values_for_runs(
        self,
        run_ids: List[str],
        metric_name: str
    ) -> List[float]:
        """특정 런들의 메트릭 평균값 조회"""
        if not run_ids:
            return []
        
        with self.get_connection() as conn:
            placeholders = ','.join(['?' for _ in run_ids])
            query = f"""
                SELECT avg_score
                FROM evaluation_metric_summary
                WHERE run_id IN ({placeholders})
                  AND metric_name = ?
                ORDER BY run_id
            """
            
            cursor = conn.execute(query, run_ids + [metric_name])
            return [row[0] for row in cursor.fetchall() if row[0] is not None]
    
    def get_environment_stats(self) -> Dict[str, List[Dict]]:
        """환경 키별 사용 통계"""
        with self.get_connection() as conn:
            query = """
                SELECT 
                    key,
                    value,
                    COUNT(*) as count,
                    MIN(e.timestamp) as first_used,
                    MAX(e.timestamp) as last_used
                FROM evaluation_env env
                JOIN evaluations e ON env.run_id = e.run_id
                GROUP BY key, value
                ORDER BY key, count DESC
            """
            
            cursor = conn.execute(query)
            
            stats = {}
            for row in cursor.fetchall():
                key = row[0]
                if key not in stats:
                    stats[key] = []
                
                stats[key].append({
                    'value': row[1],
                    'count': row[2],
                    'first_used': row[3],
                    'last_used': row[4]
                })
            
            return stats
    
    def get_all_runs(self, limit: int = 100) -> List[Dict]:
        """모든 실행 이력 조회"""
        with self.get_connection() as conn:
            query = """
                SELECT run_id, timestamp, dataset_name, dataset_items, 
                       ragas_score, status, faithfulness, answer_relevancy,
                       context_precision, context_recall, answer_correctness
                FROM evaluations
                ORDER BY timestamp DESC
                LIMIT ?
            """
            
            cursor = conn.execute(query, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ============ Pydantic Model Support Methods ============
    
    def save_evaluation_model(self, evaluation: 'EvaluationResult') -> bool:
        """Save evaluation using Pydantic model (type-safe)"""
        if not PYDANTIC_AVAILABLE:
            logger.warning("Pydantic not available, falling back to legacy save_evaluation")
            return self.save_evaluation(
                run_id=evaluation.run_id,
                dataset_name=evaluation.dataset_name,
                dataset_hash=evaluation.dataset_hash,
                dataset_items=evaluation.dataset_items,
                environment=evaluation.environment.to_dict(),
                metrics=evaluation.overall_metrics.to_dict(),
                details=[self._evaluation_item_to_dict(item) for item in evaluation.items],
                llm=evaluation.llm,
                config=evaluation.config.to_dict()
            )
        
        try:
            with self.get_connection() as conn:
                # Insert evaluation record
                db_dict = evaluation.to_database_dict()
                
                conn.execute("""
                    INSERT INTO evaluations (
                        run_id, timestamp, llm, dataset_name, dataset_hash,
                        dataset_items, total_items, metrics, config_data,
                        environment_json, ragas_score, faithfulness, 
                        answer_relevancy, context_precision, context_recall, 
                        answer_correctness, status, error_message, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    db_dict['run_id'], db_dict['timestamp'], db_dict['llm'],
                    db_dict['dataset_name'], db_dict['dataset_hash'],
                    db_dict['dataset_items'], db_dict['total_items'],
                    db_dict['metrics'], db_dict['config_data'],
                    db_dict['environment_json'], db_dict['ragas_score'],
                    db_dict['faithfulness'], db_dict['answer_relevancy'],
                    db_dict['context_precision'], db_dict['context_recall'],
                    db_dict['answer_correctness'], db_dict['status'],
                    db_dict['error_message'], db_dict['created_at']
                ))
                
                # Insert environment EAV data
                env_data = evaluation.environment.to_dict()
                if env_data:
                    env_records = [
                        (evaluation.run_id, key, str(value))
                        for key, value in env_data.items() if value is not None
                    ]
                    if env_records:
                        conn.executemany("""
                            INSERT INTO evaluation_env (run_id, key, value)
                            VALUES (?, ?, ?)
                        """, env_records)
                
                # Insert evaluation items
                if evaluation.items:
                    self._save_evaluation_items_model(conn, evaluation.run_id, evaluation.items)
                
                logger.info(f"Saved evaluation model: {evaluation.run_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save evaluation model {evaluation.run_id}: {e}")
            return False
    
    def load_evaluation_model(self, run_id: str) -> Optional['EvaluationResult']:
        """Load evaluation as Pydantic model (type-safe)"""
        if not PYDANTIC_AVAILABLE:
            logger.warning("Pydantic not available, cannot load evaluation model")
            return None
        
        try:
            with self.get_connection() as conn:
                # Load main evaluation record
                cursor = conn.execute("""
                    SELECT * FROM evaluations WHERE run_id = ?
                """, (run_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Convert row to dict
                columns = [desc[0] for desc in cursor.description]
                eval_dict = dict(zip(columns, row))
                
                # Create evaluation model
                evaluation = EvaluationResult.from_database_dict(eval_dict)
                
                # Load items
                items_cursor = conn.execute("""
                    SELECT * FROM evaluation_items 
                    WHERE run_id = ? ORDER BY item_index
                """, (run_id,))
                
                items = []
                for item_row in items_cursor.fetchall():
                    item_columns = [desc[0] for desc in items_cursor.description]
                    item_dict = dict(zip(item_columns, item_row))
                    
                    # Parse contexts
                    contexts = item_dict.get('contexts', '[]')
                    if isinstance(contexts, str):
                        try:
                            contexts = json.loads(contexts)
                        except json.JSONDecodeError:
                            contexts = [contexts] if contexts else []
                    
                    item = EvaluationItem(
                        item_index=item_dict['item_index'],
                        question=item_dict['question'] or '',
                        answer=item_dict['answer'] or '',
                        contexts=contexts,
                        ground_truth=item_dict.get('ground_truth'),
                        metrics=EvaluationMetrics(
                            faithfulness=item_dict.get('faithfulness', 0.0),
                            answer_relevancy=item_dict.get('answer_relevancy', 0.0),
                            context_precision=item_dict.get('context_precision', 0.0),
                            context_recall=item_dict.get('context_recall', 0.0),
                            answer_correctness=item_dict.get('answer_correctness', 0.0)
                        )
                    )
                    items.append(item)
                
                evaluation.items = items
                evaluation.total_items = len(items)
                
                return evaluation
                
        except Exception as e:
            logger.error(f"Failed to load evaluation model {run_id}: {e}")
            return None
    
    def _save_evaluation_items_model(self, conn, run_id: str, items: List['EvaluationItem']):
        """Save evaluation items from Pydantic models"""
        items_data = []
        for item in items:
            contexts_json = json.dumps(item.contexts, ensure_ascii=False)
            
            items_data.append((
                run_id,
                item.item_index,
                item.question,
                item.answer,
                contexts_json,
                item.ground_truth or '',
                item.metrics.faithfulness,
                item.metrics.answer_relevancy,
                item.metrics.context_precision,
                item.metrics.context_recall,
                item.metrics.answer_correctness
            ))
        
        conn.executemany("""
            INSERT INTO evaluation_items (
                run_id, item_index, question, answer, contexts, ground_truth,
                faithfulness, answer_relevancy, context_precision,
                context_recall, answer_correctness
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, items_data)
    
    def _evaluation_item_to_dict(self, item: 'EvaluationItem') -> Dict[str, Any]:
        """Convert EvaluationItem to dictionary for backward compatibility"""
        return {
            'question': item.question,
            'answer': item.answer,
            'contexts': item.contexts,
            'ground_truth': item.ground_truth,
            'faithfulness': item.metrics.faithfulness,
            'answer_relevancy': item.metrics.answer_relevancy,
            'context_precision': item.metrics.context_precision,
            'context_recall': item.metrics.context_recall,
            'answer_correctness': item.metrics.answer_correctness
        }
    
    def update_evaluation_status(self, run_id: str, status: Union[str, 'EvaluationStatus'], error_message: Optional[str] = None) -> bool:
        """Update evaluation status (supports both string and Pydantic enum)"""
        try:
            status_str = status.value if PYDANTIC_AVAILABLE and hasattr(status, 'value') else str(status)
            
            with self.get_connection() as conn:
                if error_message:
                    conn.execute("""
                        UPDATE evaluations 
                        SET status = ?, error_message = ? 
                        WHERE run_id = ?
                    """, (status_str, error_message, run_id))
                else:
                    conn.execute("""
                        UPDATE evaluations 
                        SET status = ?
                        WHERE run_id = ?
                    """, (status_str, run_id))
                
                return conn.total_changes > 0
                
        except Exception as e:
            logger.error(f"Failed to update evaluation status for {run_id}: {e}")
            return False