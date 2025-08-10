# RAGTrace Lite Installation Guide

## System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, Linux
- **Memory**: 4GB RAM minimum (8GB recommended for BGE-M3)
- **Storage**: 1GB free space (5GB if using BGE-M3 embeddings)

## Installation Methods

### 1. Basic Installation (Minimal Dependencies)

Install only the core functionality with minimal dependencies:

```bash
pip install ragtrace-lite
```

This installs:
- Core evaluation framework (RAGAS)
- Data processing utilities
- Database support
- Configuration management

### 2. Installation with LLM Support

To use Google Gemini or Naver HCX LLMs:

```bash
pip install "ragtrace-lite[llm]"
```

Additional components:
- Google Generative AI SDK
- LangChain framework
- LangChain Community extensions

### 3. Installation with Local Embeddings

To use BGE-M3 local embeddings (offline capability):

```bash
pip install "ragtrace-lite[embeddings]"
```

Additional components:
- Sentence Transformers
- PyTorch (CPU/GPU support)
- BGE-M3 model (downloaded on first use)

### 4. Enhanced Features Installation

For advanced analytics and visualizations:

```bash
pip install "ragtrace-lite[enhanced]"
```

Additional components:
- Plotly for interactive visualizations
- PSUtil for system monitoring
- SciPy for statistical analysis
- Scikit-learn for anomaly detection

### 5. Full Installation (All Features)

To install everything:

```bash
pip install "ragtrace-lite[all]"
```

### 6. Development Installation

For contributors and developers:

```bash
# Clone the repository
git clone https://github.com/yourusername/ragtrace-lite.git
cd ragtrace-lite

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

## GPU Support for BGE-M3

### NVIDIA GPU (CUDA)

```bash
# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Then install RAGTrace Lite
pip install "ragtrace-lite[embeddings]"
```

### Apple Silicon (M1/M2/M3)

```bash
# PyTorch with MPS support is included by default
pip install "ragtrace-lite[embeddings]"
```

### CPU Only

```bash
# Explicitly install CPU-only PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Then install RAGTrace Lite
pip install "ragtrace-lite[embeddings]"
```

## Environment Configuration

### 1. Create `.env` File

Copy the example configuration:

```bash
cp .env.example .env
```

### 2. Set API Keys

Edit `.env` file:

```bash
# For Naver HCX-005
CLOVA_STUDIO_API_KEY=your_clova_api_key_here

# For Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Default LLM (optional)
DEFAULT_LLM=hcx

# Default embedding (optional)
DEFAULT_EMBEDDING=bge_m3
```

### 3. Verify Installation

```bash
# Check installation
ragtrace-lite version

# Test LLM connection
ragtrace-lite test-connection
```

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'ragtrace_lite'**
   ```bash
   # Ensure proper installation
   pip show ragtrace-lite
   
   # Reinstall if needed
   pip install --force-reinstall ragtrace-lite
   ```

2. **API Key Errors**
   ```bash
   # Check environment variables
   echo $GEMINI_API_KEY
   echo $CLOVA_STUDIO_API_KEY
   
   # Or use Python
   python -c "import os; print(os.getenv('GEMINI_API_KEY'))"
   ```

3. **PyTorch/CUDA Issues**
   ```bash
   # Check PyTorch installation
   python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
   ```

4. **Memory Issues with BGE-M3**
   ```bash
   # Use CPU instead of GPU
   BGE_M3_DEVICE=cpu ragtrace-lite evaluate data.json
   ```

## Docker Installation

### Using Pre-built Image

```bash
# Pull the image
docker pull ragtrace/ragtrace-lite:latest

# Run with environment variables
docker run -it \
  -e GEMINI_API_KEY=$GEMINI_API_KEY \
  -e CLOVA_STUDIO_API_KEY=$CLOVA_STUDIO_API_KEY \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/reports:/app/reports \
  ragtrace/ragtrace-lite evaluate /app/data/evaluation_data.json
```

### Building from Source

```bash
# Build the image
docker build -t ragtrace-lite .

# Run the container
docker run -it --rm \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/reports:/app/reports \
  ragtrace-lite evaluate /app/data/evaluation_data.json
```

## Next Steps

1. **Quick Start**: See [README.md](README.md#quick-start) for usage examples
2. **Configuration**: Refer to [Configuration Guide](docs/configuration.md)
3. **API Documentation**: Check [API Reference](docs/api_reference.md)
4. **Contributing**: Read [CONTRIBUTING.md](CONTRIBUTING.md)

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/ragtrace-lite/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ragtrace-lite/discussions)
- **Documentation**: [Read the Docs](https://ragtrace-lite.readthedocs.io)