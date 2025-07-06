#!/usr/bin/env python3
"""
Basic usage example for RAGTrace Lite

This example demonstrates how to use RAGTrace Lite programmatically.
"""

import os
from pathlib import Path
from ragtrace_lite import RAGTraceLite

# Set up environment variables (or use .env file)
os.environ['GEMINI_API_KEY'] = 'your-gemini-api-key'
os.environ['CLOVA_STUDIO_API_KEY'] = 'your-clova-api-key'


def main():
    """Run basic evaluation example"""
    
    # Initialize RAGTrace Lite
    app = RAGTraceLite()
    
    # Prepare evaluation data
    evaluation_data = [
        {
            "question": "What is RAGTrace Lite?",
            "contexts": [
                "RAGTrace Lite is a lightweight RAG evaluation framework.",
                "It supports multiple LLMs including HCX-005 and Gemini."
            ],
            "answer": "RAGTrace Lite is a lightweight framework for evaluating RAG systems.",
            "ground_truth": "RAGTrace Lite is a lightweight RAG evaluation framework."
        },
        {
            "question": "Which LLMs are supported?",
            "contexts": [
                "RAGTrace Lite supports HCX-005 from Naver and Gemini from Google.",
                "Both LLMs can be used for evaluation tasks."
            ],
            "answer": "HCX-005 and Gemini are supported.",
            "ground_truth": "HCX-005 and Gemini are supported LLMs."
        }
    ]
    
    # Save evaluation data to a temporary file
    import json
    data_file = Path("temp_evaluation_data.json")
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(evaluation_data, f, ensure_ascii=False, indent=2)
    
    try:
        # Run evaluation with HCX-005
        print("Running evaluation with HCX-005...")
        success = app.evaluate_dataset(
            data_path=str(data_file),
            output_dir="results/hcx",
            llm_provider="hcx"
        )
        
        if success:
            print("✅ HCX-005 evaluation completed successfully!")
        
        # Run evaluation with Gemini
        print("\nRunning evaluation with Gemini...")
        success = app.evaluate_dataset(
            data_path=str(data_file),
            output_dir="results/gemini",
            llm_provider="gemini"
        )
        
        if success:
            print("✅ Gemini evaluation completed successfully!")
        
        # List recent evaluations
        print("\nRecent evaluations:")
        app.list_evaluations(limit=5)
        
    finally:
        # Clean up
        app.cleanup()
        if data_file.exists():
            data_file.unlink()


if __name__ == "__main__":
    main()