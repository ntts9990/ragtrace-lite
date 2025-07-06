# RAGTrace Lite Development Guide

## Environment Setup
- **Python**: >= 3.9 (updated from 3.8 due to google-generativeai dependency)
- **Package Manager**: uv (recommended)

## Setup Commands
```bash
# Install dependencies
uv sync --extra llm --extra dev

# Set environment variables for testing
export CLOVA_STUDIO_API_KEY="your_hcx_key"
export GEMINI_API_KEY="your_gemini_key"
```

## Development Commands
```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=ragtrace_lite --cov-report=html

# Run specific test
uv run pytest tests/unit/test_config_loader.py -v

# Run linting
uv run ruff check .
uv run black --check .

# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy src/ragtrace_lite
```

## Configuration
- Main config: `config.yaml`
- Supports HCX and Gemini LLM providers
- Environment variables take precedence over config file values

## Test Results & Status ✅

### Successful Fixes Applied:
- **Pydantic v1→v2 Migration**: All validators migrated to `@field_validator`
- **API Key Integration**: Real HCX and Gemini keys working correctly
- **CLI Functionality**: Commands working (version, list-datasets, evaluate)
- **LLM Connections**: HCX API connection successful
- **Database Operations**: SQLite operations working correctly
- **Data Processing**: JSON/Excel file loading functional

### Test Coverage: 42% (Significant Improvement)
- Config loader: 83% coverage
- LLM factory: 50% coverage  
- CLI: 59% coverage
- Main application: 48% coverage
- Database manager: 41% coverage

### Verified Working Features:
- ✅ Configuration loading from .env and YAML
- ✅ HCX LLM API connection and testing
- ✅ RAG evaluation pipeline initialization
- ✅ Data validation and conversion
- ✅ Database table creation and management
- ✅ CLI command interface

### Known Issues (Minor):
- Some unit tests expect mock values vs real API responses
- HuggingFace embeddings deprecation warning (non-blocking)
- Rate limiting tests need refinement for actual API calls

## Project Structure
- `src/ragtrace_lite/`: Main source code
- `tests/`: Unit and integration tests
- `examples/`: Usage examples
- `docs/`: Documentation

## AI Collaboration (Claude Code + Gemini)
Claude Code can collaborate with Gemini to solve complex problems through bash commands. This enables a problem-solving dialogue between the two AI assistants.
### How to Collaborate
1. **Execute Gemini commands via bash**: Use the `gemini -p` command in bash to interact with Gemini
2. **Pass prompts as arguments**: Provide your question or request as arguments to the gemini command
3. **Iterative problem solving**: Use the responses from Gemini to refine your approach and continue the dialogue
### Example Usage
```bash
# Ask Gemini for help with a specific problem
gemini "How should I optimize this Flutter widget for better performance?"
# Request code review or suggestions
gemini "Review this GetX controller implementation and suggest improvements"
# Collaborate on debugging
gemini "This error occurs when running flutter build ios. What could be the cause?"
```
### Collaboration Workflow
1. **Identify complex problems**: When encountering challenging issues, consider leveraging Gemini's perspective
2. **Formulate clear questions**: Create specific, context-rich prompts for better responses
3. **Iterate on solutions**: Use responses to refine your approach and ask follow-up questions
4. **Combine insights**: Merge insights from both Claude Code and Gemini for comprehensive solutions