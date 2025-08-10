#!/usr/bin/env python
"""Test complete Excel upload workflow with mock evaluation"""

import json
import sqlite3
import numpy as np
from datetime import datetime
from pathlib import Path
import sys
import uuid
import os

# Add src to path
sys.path.insert(0, 'src')

from ragtrace_lite.core.excel_parser import ExcelParser
from ragtrace_lite.config.config_loader import get_config

# DB path will be determined by ConfigLoader

def test_upload_workflow():
    """Test the complete workflow with mock evaluation"""
    
    print("🧪 Testing Complete Excel Upload Workflow")
    print("="*60)
    
    # Get paths from config
    config = get_config()
    db_path = Path(config._get_default_config()['database']['path']).resolve()
    excel_path = db_path.parent / "sample_ragtrace_dataset.xlsx"
    
    print(f"Using DB path: {db_path}")
    print(f"Looking for Excel file: {excel_path}")
    
    if not excel_path.exists():
        print(f"❌ Excel file not found at {excel_path}")
        print("Available files:")
        if excel_path.parent.exists():
            for file in excel_path.parent.glob("*.xlsx"):
                print(f"  - {file}")
        return None
    
    # Parse Excel
    parser = ExcelParser(excel_path)
    dataset, environment, dataset_hash, dataset_items = parser.parse()
    
    print(f"✅ Excel parsed: {dataset_items} items")
    
    # Mock evaluation results
    results = {
        'metrics': {
            'faithfulness': 0.85,
            'answer_relevancy': 0.92,
            'context_precision': 0.78,
            'context_recall': 0.88,
            'answer_correctness': 0.81,
            'ragas_score': 0.848
        }
    }
    
    print(f"✅ Mock evaluation completed: {results['metrics']['ragas_score']:.3f}")
    
    # Store in database
    run_id = f"test_excel_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    dataset_name = "mock_test_dataset"
    
    store_evaluation_results(run_id, dataset_name, dataset, results, environment, excel_path)
    
    print(f"✅ Results stored with run_id: {run_id}")
    print(f"🌐 View in dashboard: http://localhost:8080")
    
    return run_id

def store_evaluation_results(run_id: str, dataset_name: str, dataset, results: dict, environment: dict, excel_path: str):
    """Store mock evaluation results"""
    
    # Get DB path from config  
    config = get_config()
    db_path = config._get_default_config()['database']['path']
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Store main evaluation record
    timestamp = datetime.now().isoformat()
    dataset_items = len(dataset)
    
    # Environment info
    env_info = environment.copy()
    env_info.update({
        'source_file': str(Path(excel_path).name),
        'file_path': str(excel_path),
        'processing_time': timestamp,
        'evaluator': 'RAGTrace-Lite-Mock',
        'columns_detected': dataset.column_names
    })
    
    # Main evaluation record
    cursor.execute("""
        INSERT INTO evaluations (
            run_id, timestamp, dataset_name, dataset_items,
            faithfulness, answer_relevancy, context_precision,
            context_recall, answer_correctness, ragas_score, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id, timestamp, dataset_name, dataset_items,
        results['metrics']['faithfulness'],
        results['metrics']['answer_relevancy'],
        results['metrics']['context_precision'],
        results['metrics']['context_recall'],
        results['metrics']['answer_correctness'],
        results['metrics']['ragas_score'],
        'completed'
    ))
    
    # Store environment data
    for key, value in env_info.items():
        cursor.execute("""
            INSERT INTO evaluation_env (run_id, key, value)
            VALUES (?, ?, ?)
        """, (run_id, key, str(value)))
    
    # Store individual question results with realistic variation
    for i in range(len(dataset)):
        # Generate realistic individual scores
        base_metrics = results['metrics']
        item_scores = {}
        
        for metric in ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall', 'answer_correctness']:
            base_value = base_metrics.get(metric, 0.5)
            variation = np.random.normal(0, 0.08)  # 8% standard deviation for more realistic variation
            item_scores[metric] = max(0.2, min(0.98, base_value + variation))
        
        # Get data from dataset
        question = dataset[i]['question']
        answer = dataset[i]['answer']
        contexts = dataset[i]['contexts']
        ground_truth = dataset[i].get('ground_truth', '') if 'ground_truth' in dataset.column_names else ''
        
        # Prepare contexts
        if isinstance(contexts, str):
            contexts = [contexts]
        contexts_json = json.dumps(contexts, ensure_ascii=False)
        
        # Store individual item
        cursor.execute("""
            INSERT INTO evaluation_items (
                run_id, item_index, question, answer, contexts, ground_truth,
                faithfulness, answer_relevancy, context_precision,
                context_recall, answer_correctness
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, i,
            question,
            answer,
            contexts_json,
            ground_truth,
            item_scores['faithfulness'],
            item_scores['answer_relevancy'],
            item_scores['context_precision'],
            item_scores['context_recall'],
            item_scores['answer_correctness']
        ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Stored {dataset_items} evaluation items in database")

if __name__ == "__main__":
    test_upload_workflow()