#!/usr/bin/env python
"""Debug question detail functionality"""

import sqlite3
import json
from pathlib import Path

# Connect to database
db_path = Path("ragtrace.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get a sample run_id
cursor.execute("SELECT run_id FROM evaluations LIMIT 1")
run_id = cursor.fetchone()[0]
print(f"Testing with run_id: {run_id}")

# Get evaluation items for this run
cursor.execute("""
    SELECT * FROM evaluation_items 
    WHERE run_id = ?
    LIMIT 3
""", (run_id,))

items = cursor.fetchall()
print(f"\nFound {len(items)} items")

for item in items:
    print(f"\n--- Item {item['item_index']} ---")
    print(f"Question: {item['question'][:50]}...")
    print(f"Answer: {item['answer'][:50]}...")
    print(f"Contexts: {item['contexts'][:50]}...")
    print(f"Ground Truth: {item['ground_truth'] or 'N/A'}")
    print(f"Metrics:")
    print(f"  - Faithfulness: {item['faithfulness']:.3f}")
    print(f"  - Answer Relevancy: {item['answer_relevancy']:.3f}")
    print(f"  - Context Precision: {item['context_precision']:.3f}")
    print(f"  - Context Recall: {item['context_recall']:.3f}")
    print(f"  - Answer Correctness: {item['answer_correctness']:.3f}")

# Test the question analyzer
print("\n" + "="*50)
print("Testing Question Analyzer")
print("="*50)

from src.ragtrace_lite.stats.question_analyzer import QuestionAnalyzer

analyzer = QuestionAnalyzer()

# Prepare data for analysis
question_data = dict(items[0])
metrics = {
    'faithfulness': question_data['faithfulness'],
    'answer_relevancy': question_data['answer_relevancy'],
    'context_precision': question_data['context_precision'],
    'context_recall': question_data['context_recall'],
    'answer_correctness': question_data['answer_correctness']
}

# Analyze the question
analysis = analyzer.analyze_question(question_data, metrics)

print(f"\nAnalysis Result:")
print(f"Overall Score: {analysis.overall_score:.3f}")
print(f"Status: {analysis.status}")
print(f"Issues: {analysis.issues}")
print(f"Recommendations: {analysis.recommendations}")
print(f"Interpretation: {analysis.interpretation}")

conn.close()