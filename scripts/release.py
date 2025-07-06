#!/usr/bin/env python3
"""
Release script for RAGTrace Lite

This script handles the release process:
1. Updates version numbers
2. Updates CHANGELOG
3. Creates git tag
4. Builds package
5. Uploads to PyPI
"""

import subprocess
import sys
import re
from pathlib import Path
from datetime import datetime


def run_command(cmd, check=True):
    """Run a shell command"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def get_current_version():
    """Get current version from pyproject.toml"""
    pyproject = Path("pyproject.toml").read_text()
    match = re.search(r'version = "([^"]+)"', pyproject)
    if match:
        return match.group(1)
    raise ValueError("Version not found in pyproject.toml")


def update_version(new_version):
    """Update version in pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    content = re.sub(
        r'version = "[^"]+"',
        f'version = "{new_version}"',
        content
    )
    pyproject_path.write_text(content)
    print(f"Updated version to {new_version}")


def update_changelog(version, changes):
    """Update CHANGELOG.md"""
    changelog_path = Path("CHANGELOG.md")
    content = changelog_path.read_text()
    
    date = datetime.now().strftime("%Y-%m-%d")
    new_entry = f"\n## [{version}] - {date}\n\n### Changed\n{changes}\n"
    
    # Insert after ## [Unreleased]
    content = content.replace(
        "## [Unreleased]",
        f"## [Unreleased]\n{new_entry}"
    )
    
    changelog_path.write_text(content)
    print("Updated CHANGELOG.md")


def main():
    """Main release process"""
    if len(sys.argv) < 2:
        print("Usage: python release.py <version> [changelog]")
        print("Example: python release.py 1.0.1 'Fixed bug in HCX authentication'")
        sys.exit(1)
    
    new_version = sys.argv[1]
    changelog = sys.argv[2] if len(sys.argv) > 2 else "- Version bump"
    
    # Validate version format
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print("Error: Version must be in format X.Y.Z")
        sys.exit(1)
    
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")
    
    # Run tests
    print("\nRunning tests...")
    run_command("pytest tests/")
    
    # Update version
    update_version(new_version)
    
    # Update CHANGELOG
    update_changelog(new_version, changelog)
    
    # Commit changes
    run_command(f'git add pyproject.toml CHANGELOG.md')
    run_command(f'git commit -m "Release v{new_version}"')
    
    # Create tag
    run_command(f'git tag -a v{new_version} -m "Release v{new_version}"')
    
    # Build package
    print("\nBuilding package...")
    run_command("python -m build")
    
    # Check package
    run_command("twine check dist/*")
    
    print(f"\nRelease v{new_version} prepared!")
    print("\nTo publish:")
    print(f"  git push origin main --tags")
    print(f"  twine upload dist/*")


if __name__ == "__main__":
    main()