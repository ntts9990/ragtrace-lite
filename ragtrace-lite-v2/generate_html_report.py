#!/usr/bin/env python
"""Generate beautiful HTML report using unified generator"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, 'src')

from ragtrace_lite.report.unified_generator import UnifiedReportGenerator, ReportFormat, ReportLanguage

def main():
    print("="*60)
    print("Generating HTML Report for RAGTrace Evaluation")
    print("="*60)
    
    # Sample evaluation results
    results = {
        'metrics': {
            'faithfulness': 0.823,
            'answer_relevancy': 0.456,
            'context_precision': 0.692,
            'context_recall': 0.914,
            'answer_correctness': 0.381,
            'ragas_score': 0.653
        },
        'details': [
            {'question': f'Q{i}', 'score': 0.5 + i*0.1} 
            for i in range(10)
        ]
    }
    
    # Environment configuration
    environment = {
        'model': 'HCX-005',
        'temperature': 0.1,
        'dataset': 'customer_support_qa',
        'embeddings': 'BGE-M3 (local)',
        'batch_size': 5,
        'rate_limit': '5s',
        'evaluation_time': '2.3 minutes'
    }
    
    # AI interpretation (simulated)
    interpretation = """
    <div class="row">
        <div class="col-md-6">
            <div class="alert alert-success">
                <h5>✅ Strong Points</h5>
                <ul>
                    <li><strong>Context Recall (0.914):</strong> Excellent retrieval coverage</li>
                    <li><strong>Faithfulness (0.823):</strong> Answers well-grounded in context</li>
                </ul>
            </div>
        </div>
        <div class="col-md-6">
            <div class="alert alert-danger">
                <h5>⚠️ Needs Improvement</h5>
                <ul>
                    <li><strong>Answer Correctness (0.381):</strong> Critical - accuracy issues</li>
                    <li><strong>Answer Relevancy (0.456):</strong> Responses often off-topic</li>
                </ul>
            </div>
        </div>
    </div>
    
    <div class="alert alert-warning mt-3">
        <h5>🎯 Recommended Actions</h5>
        <ol>
            <li><strong>Immediate:</strong> Review answer generation prompts - focus on accuracy</li>
            <li><strong>Short-term:</strong> Fine-tune relevancy scoring mechanism</li>
            <li><strong>Long-term:</strong> Consider model retraining with corrected examples</li>
        </ol>
    </div>
    
    <div class="mt-3">
        <h5>📊 Statistical Insights</h5>
        <p>The system shows a <strong>significant performance gap</strong> between retrieval (high) and generation (low) capabilities. 
        This pattern suggests the retrieved context is good, but the LLM struggles to generate accurate answers from it.</p>
        <p><strong>Confidence:</strong> Based on evaluation of 10 samples with consistent patterns.</p>
    </div>
    """
    
    # Generate HTML report using unified generator
    generator = UnifiedReportGenerator()
    run_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Save HTML file
    output_path = Path('results') / f'{run_id}_report.html'
    output_path.parent.mkdir(exist_ok=True)
    
    # Generate report with unified generator
    html_content = generator.generate_report(
        run_id=run_id,
        results=results,
        environment=environment,
        format=ReportFormat.HTML,
        language=ReportLanguage.ENGLISH,
        output_path=output_path,
        dataset_name="Customer Support QA"
    )
    
    print(f"\n✅ HTML Report generated: {output_path}")
    print(f"\n📊 Report includes:")
    print("  - Interactive metrics visualization")
    print("  - Radar chart for performance overview")
    print("  - Color-coded score indicators")
    print("  - AI-powered analysis and recommendations")
    print("\nOpen the HTML file in your browser to view the report!")
    
    return output_path

if __name__ == "__main__":
    main()