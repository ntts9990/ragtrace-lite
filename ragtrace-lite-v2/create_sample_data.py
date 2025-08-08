#!/usr/bin/env python
"""Create sample data for dashboard testing"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random
import json

sys.path.insert(0, 'src')

from ragtrace_lite.db.manager import DatabaseManager

def create_sample_evaluations():
    """Create sample evaluation data"""
    
    db = DatabaseManager("ragtrace.db")
    
    # Sample datasets
    datasets = [
        "customer_support_qa",
        "product_documentation",
        "technical_manual",
        "faq_dataset",
        "knowledge_base"
    ]
    
    # Create 20 sample evaluations over the past 30 days
    for i in range(20):
        # Random date in last 30 days
        days_ago = random.randint(0, 30)
        timestamp = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
        
        # Random performance pattern
        if i % 3 == 0:  # Good performance
            base_score = 0.8
            variance = 0.1
        elif i % 3 == 1:  # Medium performance
            base_score = 0.65
            variance = 0.15
        else:  # Poor performance
            base_score = 0.45
            variance = 0.1
        
        # Generate metrics
        metrics = {
            'faithfulness': max(0, min(1, random.gauss(base_score + 0.05, variance))),
            'answer_relevancy': max(0, min(1, random.gauss(base_score - 0.1, variance))),
            'context_precision': max(0, min(1, random.gauss(base_score, variance))),
            'context_recall': max(0, min(1, random.gauss(base_score + 0.1, variance))),
            'answer_correctness': max(0, min(1, random.gauss(base_score - 0.05, variance)))
        }
        
        # Calculate RAGAS score
        metrics['ragas_score'] = sum(metrics.values()) / len(metrics)
        
        # Environment
        environment = {
            'model': random.choice(['HCX-005', 'HCX-003', 'Gemini-2.5']),
            'temperature': round(random.uniform(0.1, 0.3), 1),
            'batch_size': random.choice([5, 10, 20]),
            'embeddings': random.choice(['BGE-M3 (local)', 'OpenAI', 'Cohere']),
            'dataset': random.choice(datasets)
        }
        
        # Sample details
        num_samples = random.randint(10, 50)
        details = []
        for j in range(min(10, num_samples)):  # Store max 10 details
            details.append({
                'question': f'Sample question {j+1}',
                'answer': f'Sample answer {j+1}',
                'contexts': [f'Context {j+1}'],
                'ground_truths': f'Ground truth {j+1}',
                **{k: max(0, min(1, v + random.gauss(0, 0.05))) for k, v in metrics.items() if k != 'ragas_score'}
            })
        
        # Save to database
        run_id = f"sample_run_{timestamp.strftime('%Y%m%d_%H%M%S')}_{i}"
        
        success = db.save_evaluation(
            run_id=run_id,
            dataset_name=random.choice(datasets),
            dataset_hash=f"hash_{i:04d}",
            dataset_items=num_samples,
            environment=environment,
            metrics=metrics,
            details=details
        )
        
        if success:
            print(f"✅ Created: {run_id} (Score: {metrics['ragas_score']:.3f})")
        else:
            print(f"❌ Failed: {run_id}")
    
    print("\n✨ Sample data creation complete!")
    print(f"📊 Total evaluations in database: {db.get_evaluation_count()}")

def get_evaluation_count():
    """Get count of evaluations in database"""
    try:
        conn = sqlite3.connect("ragtrace.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM evaluations")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

if __name__ == "__main__":
    print("="*50)
    print("Creating Sample Data for Dashboard")
    print("="*50)
    
    existing_count = get_evaluation_count()
    print(f"\n📊 Existing evaluations: {existing_count}")
    
    if existing_count > 0:
        response = input("\n⚠️  Database already has data. Add more? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)
    
    create_sample_evaluations()
    
    print("\n🎯 Dashboard is ready!")
    print("Run: python run_dashboard.py")
    print("Then open: http://localhost:5000")