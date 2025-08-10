# RAGTrace Lite Offline Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying RAGTrace Lite v2.0 in offline/closed network environments, particularly for Windows 10/11 systems without internet access.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Preparation Phase (Online Environment)](#preparation-phase-online-environment)
3. [Transfer Phase](#transfer-phase)
4. [Installation Phase (Offline Environment)](#installation-phase-offline-environment)
5. [Configuration](#configuration)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Online Environment (Preparation Machine)
- Python 3.9+ installed
- Git installed
- Internet access
- Sufficient disk space (>5GB)

### Offline Environment (Target Machine)
- Windows 10 or Windows 11
- Python 3.9+ installed
- Administrator privileges
- Minimum 8GB RAM
- 10GB free disk space

## Preparation Phase (Online Environment)

### Step 1: Clone the Repository

```bash
git clone https://github.com/ntts9990/ragtrace-lite.git
cd ragtrace-lite/ragtrace-lite-v2
```

### Step 2: Prepare Offline Package

#### Option A: Automated Preparation (Unix/Linux/Mac)

```bash
# Make script executable
chmod +x scripts/prepare_offline.sh

# Run preparation script
./scripts/prepare_offline.sh 3.9  # Specify Python version
```

#### Option B: Manual Preparation

```bash
# Install dependencies
pip install -r requirements.txt

# Run wheel collection
python scripts/collect_wheels.py \
    --python-version 3.9 \
    --platforms win_amd64 win32 any \
    --create-package
```

### Step 3: Verify Package Contents

The script creates `ragtrace_lite_offline_3.9.zip` containing:

```
offline_package/
├── wheels/              # All Python dependency wheels
│   ├── *.whl           # Individual wheel files
│   └── metadata.json   # Package metadata
├── src/                # RAGTrace Lite source code
├── models/             # BGE-M3 embedding model
│   └── bge-m3/        # Model files
├── config.yaml        # Configuration file
├── requirements.txt   # Dependencies list
├── setup.py          # Setup script
├── install_offline.bat    # Windows batch installer
├── install_offline.ps1    # PowerShell installer
└── README_OFFLINE.md     # Offline installation guide
```

## Transfer Phase

### Step 1: Package Verification

Before transfer, verify the package:

```bash
# Check package size (should be ~2-3GB with models)
ls -lh ragtrace_lite_offline_*.zip

# Verify integrity (optional)
sha256sum ragtrace_lite_offline_*.zip > package.sha256
```

### Step 2: Transfer Methods

Choose one of the following methods:

1. **USB Drive**
   - Copy ZIP file to USB drive
   - Safely eject the drive
   - Transfer to offline machine

2. **Network Share** (if available in closed network)
   - Copy to approved network location
   - Access from target machine

3. **Physical Media**
   - Burn to DVD/Blu-ray if needed
   - Use approved media transfer protocols

### Step 3: Verification After Transfer

On the target machine:
```powershell
# Verify file integrity (if you created SHA256)
certutil -hashfile ragtrace_lite_offline_3.9.zip SHA256
```

## Installation Phase (Offline Environment)

### Step 1: Extract Package

```powershell
# Extract to desired location (e.g., C:\RAGTrace)
Expand-Archive -Path ragtrace_lite_offline_3.9.zip -DestinationPath C:\RAGTrace
cd C:\RAGTrace
```

### Step 2: Install Python Dependencies

#### Option A: Using Batch Script (Recommended)

1. Open Command Prompt as **Administrator**
2. Navigate to extraction directory:
   ```cmd
   cd C:\RAGTrace
   ```
3. Run installer:
   ```cmd
   install_offline.bat
   ```

#### Option B: Using PowerShell

1. Open PowerShell as **Administrator**
2. Navigate to extraction directory:
   ```powershell
   cd C:\RAGTrace
   ```
3. Set execution policy and run:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
   .\install_offline.ps1
   ```

#### Option C: Manual Installation

```cmd
# Install all wheels
pip install --no-index --find-links wheels -r requirements.txt

# Install RAGTrace Lite
pip install -e .

# Verify installation
ragtrace-lite --version
```

### Step 3: Environment Setup

Create environment configuration:

```powershell
# Copy example environment file
copy .env.example .env

# Edit .env file with your API keys
notepad .env
```

Required environment variables:
```
CLOVA_STUDIO_API_KEY=your_hcx_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here  # Optional
LLM_PROVIDER=hcx  # or gemini
EMBEDDINGS_PROVIDER=local  # Use local BGE-M3
DB_PATH=ragtrace.db
LOG_LEVEL=INFO
```

## Configuration

### 1. Edit config.yaml

```yaml
# Key configurations to verify/modify

# LLM Configuration
llm:
  provider: hcx  # or gemini
  hcx:
    api_url: "https://your-internal-hcx-endpoint/v3/chat-completions/HCX-005"
    api_key: "${CLOVA_STUDIO_API_KEY}"

# Embeddings Configuration  
embeddings:
  provider: local  # Use local for offline
  local:
    model_path: "./models/bge-m3"
    use_gpu: false  # Set to true if GPU available

# Offline Mode
offline:
  enabled: true  # Enable offline mode
  models_dir: "./models"
```

### 2. Configure API Endpoints (if using internal servers)

If your closed network has internal API servers:

```yaml
# For internal BGE-M3 embedding server
embeddings:
  provider: api
  api:
    api_url: "http://internal-server:8080/embeddings"
    api_key: "${INTERNAL_API_KEY}"

# For internal HCX server
llm:
  hcx:
    api_url: "http://internal-hcx-server/api/v3/chat"
```

### 3. Database Configuration

```yaml
database:
  path: "C:/RAGTrace/data/ragtrace.db"  # Use absolute path
  wal_mode: true  # Better for Windows
```

## Verification

### Step 1: Test Installation

```cmd
# Check version
ragtrace-lite --version

# Show help
ragtrace-lite --help

# List available commands
ragtrace-lite --help
```

### Step 2: Test Embeddings

```python
# Create test script: test_embeddings.py
from ragtrace_lite.core.embeddings_adapter_v2 import EmbeddingsAdapter

# Test local embeddings
embeddings = EmbeddingsAdapter({"provider": "local"})
vector = embeddings.embed_query("test query")
print(f"Embedding dimension: {len(vector)}")  # Should be 1024 for BGE-M3
```

Run test:
```cmd
python test_embeddings.py
```

### Step 3: Create and Run Test Evaluation

```cmd
# Create template
ragtrace-lite create-template

# Edit template with test data
notepad template_*.xlsx

# Run evaluation
ragtrace-lite evaluate --excel template_*.xlsx --yes
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Python Not Found
**Error**: `'python' is not recognized as an internal or external command`

**Solution**:
```cmd
# Add Python to PATH
set PATH=%PATH%;C:\Python39;C:\Python39\Scripts

# Or use full path
C:\Python39\python.exe install_offline.bat
```

#### 2. Permission Denied
**Error**: `PermissionError: [Errno 13] Permission denied`

**Solution**:
- Run Command Prompt/PowerShell as Administrator
- Check file permissions on extraction directory
- Disable antivirus temporarily during installation

#### 3. Wheel Compatibility Issues
**Error**: `ERROR: wheel is not supported on this platform`

**Solution**:
```cmd
# Check Python version
python --version

# Check platform
python -c "import platform; print(platform.machine())"

# Reinstall with correct platform wheels
pip install --no-index --find-links wheels --force-reinstall package_name
```

#### 4. Missing Dependencies
**Error**: `ModuleNotFoundError: No module named 'xxx'`

**Solution**:
```cmd
# List installed packages
pip list

# Install missing package from wheels directory
pip install --no-index --find-links wheels missing_package
```

#### 5. Model Loading Issues
**Error**: `FileNotFoundError: BGE-M3 model not found`

**Solution**:
```cmd
# Verify model files exist
dir models\bge-m3

# Update config.yaml with correct path
notepad config.yaml
# Set: model_path: "C:/RAGTrace/models/bge-m3"
```

#### 6. API Connection Issues in Closed Network
**Error**: `ConnectionError: Unable to connect to API`

**Solution**:
- Verify internal API endpoints in config.yaml
- Check network connectivity to internal servers
- Confirm API keys are correct
- Test with curl/Invoke-WebRequest:
  ```powershell
  Invoke-WebRequest -Uri "http://internal-server/health" -Method GET
  ```

### Advanced Troubleshooting

#### Enable Debug Logging

```python
# Set in .env file
LOG_LEVEL=DEBUG

# Or in Python script
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Test Individual Components

```python
# test_components.py
from ragtrace_lite.config.config_loader import ConfigLoader
from ragtrace_lite.core.llm_adapter import LLMAdapter
from ragtrace_lite.core.embeddings_adapter_v2 import EmbeddingsAdapter

# Test config loading
config = ConfigLoader()
print("Config loaded successfully")

# Test LLM adapter
llm_config = config.get_llm_config()
llm = LLMAdapter.from_config(llm_config)
print(f"LLM initialized: {llm._llm_type}")

# Test embeddings
emb_config = config.get_embeddings_config()
embeddings = EmbeddingsAdapter(emb_config)
print(f"Embeddings initialized: {embeddings.provider}")
```

## Best Practices

### 1. Pre-deployment Checklist

- [ ] Verify Python version compatibility
- [ ] Test package extraction in similar environment
- [ ] Document all internal API endpoints
- [ ] Prepare API keys and credentials
- [ ] Create backup of configuration files
- [ ] Test with sample data before production use

### 2. Security Considerations

- Store API keys securely (use Windows Credential Manager if possible)
- Limit file permissions to authorized users only
- Audit log access to sensitive configurations
- Use internal certificate validation for API calls

### 3. Performance Optimization

- Use local embeddings to avoid network latency
- Configure appropriate batch sizes in config.yaml
- Enable GPU support if available
- Use SSD for database storage

### 4. Maintenance

- Keep offline wheels updated quarterly
- Document any configuration changes
- Maintain version compatibility matrix
- Create rollback procedures

## Support and Resources

### Internal Resources
- Configuration templates in `docs/templates/`
- Example evaluations in `examples/`
- API documentation in `docs/api/`

### Logs and Diagnostics
- Application logs: `ragtrace.log`
- Database: `ragtrace.db`
- Error reports: `results/*/error_log.txt`

### Contact
For issues specific to offline deployment:
1. Check this guide first
2. Review logs for detailed error messages
3. Contact your system administrator
4. Report issues to the RAGTrace team

---

**Document Version**: 1.0.0  
**Last Updated**: 2024  
**RAGTrace Lite Version**: 2.0.0