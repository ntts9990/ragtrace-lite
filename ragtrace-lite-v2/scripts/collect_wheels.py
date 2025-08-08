#!/usr/bin/env python
"""
Collect all dependency wheels for offline installation
Supports Windows 10/11 deployment
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import argparse
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class WheelCollector:
    """Collect wheels for offline deployment"""
    
    def __init__(self, python_version: str = "3.9", platforms: list = None):
        """
        Initialize wheel collector
        
        Args:
            python_version: Target Python version (e.g., "3.9", "3.10", "3.11")
            platforms: List of target platforms (default: Windows platforms)
        """
        self.python_version = python_version
        self.platforms = platforms or ["win_amd64", "win32", "any"]
        self.project_root = Path(__file__).parent.parent
        self.wheels_dir = self.project_root / "offline_wheels"
        self.requirements_file = self.project_root / "requirements.txt"
        
    def collect_wheels(self):
        """Collect all wheels for offline installation"""
        logger.info(f"Collecting wheels for Python {self.python_version}")
        logger.info(f"Target platforms: {', '.join(self.platforms)}")
        
        # Create wheels directory
        self.wheels_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean existing wheels
        for file in self.wheels_dir.glob("*.whl"):
            file.unlink()
        
        # Collect wheels for each platform
        for platform in self.platforms:
            self._collect_platform_wheels(platform)
        
        # Create metadata file
        self._create_metadata()
        
        logger.info(f"Wheels collected in: {self.wheels_dir}")
        
    def _collect_platform_wheels(self, platform: str):
        """Collect wheels for specific platform"""
        logger.info(f"Collecting wheels for platform: {platform}")
        
        # Build pip download command
        cmd = [
            sys.executable, "-m", "pip", "download",
            "-r", str(self.requirements_file),
            "-d", str(self.wheels_dir),
            "--python-version", self.python_version,
            "--no-deps"  # Will resolve deps separately
        ]
        
        # Add platform specifier if not 'any'
        if platform != "any":
            cmd.extend(["--platform", platform])
        
        # Add --only-binary for compiled packages
        cmd.extend(["--only-binary", ":all:"])
        
        try:
            # First pass: download with platform specification
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.warning(f"Some packages may not have {platform} wheels, trying universal...")
            
        # Second pass: get dependencies
        cmd_deps = [
            sys.executable, "-m", "pip", "download",
            "-r", str(self.requirements_file),
            "-d", str(self.wheels_dir),
            "--python-version", self.python_version
        ]
        
        try:
            subprocess.run(cmd_deps, check=True, capture_output=True, text=True)
            logger.info(f"Successfully collected wheels for {platform}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to collect some wheels: {e.stderr}")
            
    def _create_metadata(self):
        """Create metadata file for offline installation"""
        metadata = {
            "python_version": self.python_version,
            "platforms": self.platforms,
            "packages": [],
            "collection_date": str(Path.ctime(Path.cwd())),
            "requirements_hash": self._hash_file(self.requirements_file)
        }
        
        # List all collected wheels
        for wheel_file in self.wheels_dir.glob("*.whl"):
            metadata["packages"].append({
                "name": wheel_file.name,
                "size": wheel_file.stat().st_size,
                "platform": self._extract_platform(wheel_file.name)
            })
        
        # Save metadata
        metadata_file = self.wheels_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata saved: {metadata_file}")
        logger.info(f"Total packages collected: {len(metadata['packages'])}")
        
    def _hash_file(self, filepath: Path) -> str:
        """Calculate file hash for verification"""
        import hashlib
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()
    
    def _extract_platform(self, wheel_name: str) -> str:
        """Extract platform from wheel filename"""
        parts = wheel_name.split('-')
        if len(parts) >= 5:
            return parts[-1].replace('.whl', '')
        return 'any'
    
    def create_offline_package(self):
        """Create complete offline installation package"""
        logger.info("Creating offline installation package...")
        
        package_dir = self.project_root / "offline_package"
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy wheels
        wheels_dest = package_dir / "wheels"
        if wheels_dest.exists():
            shutil.rmtree(wheels_dest)
        shutil.copytree(self.wheels_dir, wheels_dest)
        
        # Copy source code
        src_dest = package_dir / "src"
        if src_dest.exists():
            shutil.rmtree(src_dest)
        shutil.copytree(self.project_root / "src", src_dest)
        
        # Copy models (BGE-M3)
        models_src = self.project_root / "models"
        if models_src.exists():
            models_dest = package_dir / "models"
            if models_dest.exists():
                shutil.rmtree(models_dest)
            shutil.copytree(models_src, models_dest)
            logger.info("Models copied to offline package")
        
        # Copy configuration files
        for config_file in ["config.yaml", "pyproject.toml", "setup.py", "requirements.txt"]:
            src_file = self.project_root / config_file
            if src_file.exists():
                shutil.copy2(src_file, package_dir / config_file)
        
        # Create offline installation script
        self._create_offline_installer(package_dir)
        
        # Create README
        self._create_offline_readme(package_dir)
        
        # Create ZIP archive
        archive_name = f"ragtrace_lite_offline_{self.python_version}"
        shutil.make_archive(
            str(self.project_root / archive_name),
            'zip',
            package_dir
        )
        
        logger.info(f"Offline package created: {archive_name}.zip")
        
    def _create_offline_installer(self, package_dir: Path):
        """Create offline installation script"""
        installer_content = '''@echo off
echo ===================================
echo RAGTrace Lite Offline Installation
echo ===================================
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ first
    pause
    exit /b 1
)

echo Installing RAGTrace Lite...
echo.

REM Install from local wheels
echo Installing dependencies from offline wheels...
pip install --no-index --find-links wheels -r requirements.txt

if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Install the package itself
echo Installing RAGTrace Lite package...
pip install -e .

if %errorlevel% neq 0 (
    echo ERROR: Failed to install RAGTrace Lite
    pause
    exit /b 1
)

echo.
echo ===================================
echo Installation completed successfully!
echo ===================================
echo.
echo You can now use RAGTrace Lite:
echo   ragtrace-lite --help
echo.
pause
'''
        
        installer_file = package_dir / "install_offline.bat"
        with open(installer_file, 'w') as f:
            f.write(installer_content)
        
        # Also create PowerShell version
        ps_installer = '''
# RAGTrace Lite Offline Installation Script

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "RAGTrace Lite Offline Installation" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.9+ first" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Install dependencies
Write-Host "Installing dependencies from offline wheels..." -ForegroundColor Yellow
pip install --no-index --find-links wheels -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install package
Write-Host "Installing RAGTrace Lite package..." -ForegroundColor Yellow
pip install -e .

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install RAGTrace Lite" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "===================================" -ForegroundColor Green
Write-Host "Installation completed successfully!" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green
Write-Host ""
Write-Host "You can now use RAGTrace Lite:" -ForegroundColor Cyan
Write-Host "  ragtrace-lite --help" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"
'''
        
        ps_file = package_dir / "install_offline.ps1"
        with open(ps_file, 'w') as f:
            f.write(ps_installer)
            
    def _create_offline_readme(self, package_dir: Path):
        """Create README for offline package"""
        readme_content = f'''# RAGTrace Lite Offline Installation Package

This package contains everything needed to install RAGTrace Lite in an offline/closed network environment.

## Contents

- `wheels/` - All Python dependency wheels
- `src/` - RAGTrace Lite source code
- `models/` - BGE-M3 embedding model (for local use)
- `config.yaml` - Configuration file
- `requirements.txt` - Python dependencies list
- `install_offline.bat` - Windows batch installer
- `install_offline.ps1` - PowerShell installer

## System Requirements

- Windows 10 or Windows 11
- Python {self.python_version} or higher
- At least 4GB of free disk space
- 8GB+ RAM recommended

## Installation Instructions

### Option 1: Using Batch Script (Recommended)

1. Extract this ZIP file to your desired location
2. Open Command Prompt as Administrator
3. Navigate to the extracted folder
4. Run: `install_offline.bat`

### Option 2: Using PowerShell

1. Extract this ZIP file to your desired location
2. Open PowerShell as Administrator
3. Navigate to the extracted folder
4. Run: `powershell -ExecutionPolicy Bypass -File install_offline.ps1`

### Option 3: Manual Installation

1. Extract this ZIP file
2. Open Command Prompt/PowerShell
3. Navigate to the extracted folder
4. Run the following commands:
   ```
   pip install --no-index --find-links wheels -r requirements.txt
   pip install -e .
   ```

## Configuration

1. Copy `.env.example` to `.env`
2. Edit `.env` file to set your API keys:
   - `CLOVA_STUDIO_API_KEY` for HCX
   - `GEMINI_API_KEY` for Gemini (if using)

3. Edit `config.yaml` to configure:
   - LLM provider (hcx or gemini)
   - Embeddings provider (local or api)
   - API endpoints (if different from defaults)

## Usage

After installation, you can use RAGTrace Lite:

```bash
# Show help
ragtrace-lite --help

# Create evaluation template
ragtrace-lite create-template

# Run evaluation
ragtrace-lite evaluate --excel your_data.xlsx

# View evaluation history
ragtrace-lite history
```

## Troubleshooting

1. **Python not found**: Ensure Python is installed and added to PATH
2. **Permission denied**: Run installer as Administrator
3. **Package conflicts**: Create a virtual environment first:
   ```
   python -m venv venv
   venv\\Scripts\\activate
   ```

## Support

For issues or questions, please contact your system administrator.

---
Package created: {Path.ctime(Path.cwd())}
Python version: {self.python_version}
Target platforms: {', '.join(self.platforms)}
'''
        
        readme_file = package_dir / "README_OFFLINE.md"
        with open(readme_file, 'w') as f:
            f.write(readme_content)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Collect wheels for offline deployment")
    parser.add_argument(
        "--python-version",
        default="3.9",
        help="Target Python version (default: 3.9)"
    )
    parser.add_argument(
        "--platforms",
        nargs="+",
        default=["win_amd64", "win32", "any"],
        help="Target platforms (default: Windows platforms)"
    )
    parser.add_argument(
        "--create-package",
        action="store_true",
        help="Create complete offline installation package"
    )
    
    args = parser.parse_args()
    
    collector = WheelCollector(
        python_version=args.python_version,
        platforms=args.platforms
    )
    
    # Collect wheels
    collector.collect_wheels()
    
    # Create offline package if requested
    if args.create_package:
        collector.create_offline_package()
    
    logger.info("Done!")


if __name__ == "__main__":
    main()