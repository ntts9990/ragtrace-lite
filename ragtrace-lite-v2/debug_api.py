#!/usr/bin/env python
"""Debug API responses"""

import requests
import json

base_url = "http://localhost:8080"

# Get reports
print("Getting reports...")
response = requests.get(f"{base_url}/api/reports")
if response.status_code == 200:
    reports = response.json()
    print(f"Found {len(reports)} reports")
    
    if reports:
        run_id = reports[0]['run_id']
        print(f"\nTesting with run_id: {run_id}")
        
        # Get report details
        print("\nGetting report details...")
        response = requests.get(f"{base_url}/api/report/{run_id}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            details = response.json()
            print("\nReport details keys:", list(details.keys()))
            
            # Check statistics
            if 'statistics' in details:
                print("\nStatistics:", details['statistics'])
            else:
                print("\n⚠️ No statistics in response")
                
            # Check metrics
            for metric in ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall', 'answer_correctness', 'ragas_score']:
                if metric in details:
                    print(f"{metric}: {details[metric]}")
        else:
            print(f"Error: {response.text}")
            
        # Get questions
        print("\n\nGetting questions...")
        response = requests.get(f"{base_url}/api/questions/{run_id}")
        if response.status_code == 200:
            questions = response.json()
            print(f"Found {len(questions)} questions")
            if questions:
                print("\nFirst question keys:", list(questions[0].keys()))
                print("Question:", questions[0].get('question', 'N/A')[:50])
else:
    print(f"Failed to get reports: {response.status_code}")