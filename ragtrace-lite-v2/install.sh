#!/bin/bash

echo "Installing RAGTrace Lite v2.0..."
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found. Please install Python 3.9 or higher."
    echo "Visit: https://www.python.org/downloads/"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "Found Python $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Warning: Some dependencies failed to install"
fi

# Install package in development mode
echo "Installing RAGTrace Lite..."
pip install -e .

# Test installation
echo ""
echo "Testing installation..."
python -c "import ragtrace_lite; print(f'RAGTrace Lite {ragtrace_lite.__version__} installed successfully!')"
if [ $? -ne 0 ]; then
    echo "Error: Installation test failed"
    exit 1
fi

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env file to add your API keys"
fi

# Make the script executable
chmod +x install.sh

echo ""
echo "========================================"
echo "Installation completed successfully!"
echo "========================================"
echo ""
echo "To use RAGTrace Lite:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Edit .env file with your API keys"
echo "  3. Run: ragtrace --help"
echo ""
echo "Quick start:"
echo "  ragtrace create-template"
echo "  ragtrace evaluate --excel template.xlsx"
echo ""