# RAGTrace Lite Documentation

Welcome to RAGTrace Lite, a lightweight RAG (Retrieval-Augmented Generation) evaluation framework optimized for Korean language support.

## Features

- 🤖 **Multi-LLM Support**: Google Gemini and Naver HCX-005
- 🌐 **Local Embeddings**: BGE-M3 with GPU acceleration
- 📊 **Comprehensive Metrics**: All RAGAS evaluation metrics
- 🏗️ **Clean Architecture**: Dependency injection and modular design
- 🐳 **Production Ready**: Docker support and monitoring integration
- 📚 **Extensive Documentation**: Guides, examples, and API reference

## Quick Start

```bash
# Install from PyPI
pip install ragtrace-lite

# Run evaluation
ragtrace-lite evaluate your_data.json --llm gemini
```

## Documentation Contents

```{toctree}
:maxdepth: 2
:caption: Getting Started

installation
quickstart
configuration
```

```{toctree}
:maxdepth: 2
:caption: User Guide

evaluation
llm-models
embeddings
metrics
data-format
```

```{toctree}
:maxdepth: 2
:caption: Advanced Topics

architecture
customization
deployment
monitoring
troubleshooting
```

```{toctree}
:maxdepth: 2
:caption: API Reference

api/cli
api/core
api/adapters
api/services
```

```{toctree}
:maxdepth: 1
:caption: Project Info

changelog
contributing
license
```

## Indices and tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`