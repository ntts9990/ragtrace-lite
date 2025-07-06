# RAGTrace Lite Examples

This directory contains example scripts demonstrating how to use RAGTrace Lite.

## Examples

### 1. Basic Usage (`basic_usage.py`)

Demonstrates the basic programmatic usage of RAGTrace Lite:
- Initializing the framework
- Preparing evaluation data
- Running evaluations with different LLMs
- Viewing results

```bash
python examples/basic_usage.py
```

### 2. CLI Usage

Basic command-line usage examples:

```bash
# Evaluate with default settings (HCX-005)
ragtrace-lite evaluate data/evaluation_data.json

# Evaluate with Gemini
ragtrace-lite evaluate data/evaluation_data.json --llm gemini

# List recent evaluations
ragtrace-lite list

# Show specific evaluation details
ragtrace-lite show run_id_12345678
```

### 3. Enhanced Features

Using the enhanced version with advanced features:

```bash
# Run enhanced evaluation
ragtrace-lite-enhanced evaluate data/evaluation_data.json

# Export logs for Elasticsearch
ragtrace-lite-enhanced export-logs logs_export.ndjson
```

### 4. Docker Usage

Running with Docker:

```bash
# Build and run
docker-compose up

# Run specific evaluation
docker-compose run ragtrace-lite evaluate /app/data/evaluation_data.json
```

## Data Format

Example evaluation data format:

```json
[
  {
    "question": "Your question here",
    "contexts": ["Context 1", "Context 2"],
    "answer": "System generated answer",
    "ground_truth": "Expected correct answer"
  }
]
```

## Environment Setup

Create a `.env` file:

```bash
GEMINI_API_KEY=your-gemini-api-key
CLOVA_STUDIO_API_KEY=your-clova-api-key
DEFAULT_LLM=hcx
DEFAULT_EMBEDDING=bge_m3
```