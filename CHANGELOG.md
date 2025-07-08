# Changelog

All notable changes to RAGTrace Lite will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.7] - 2025-07-08

### Fixed
- Fixed pandas DataFrame.empty ambiguous truth value error on Windows
- Updated main.py to use len() instead of .empty for DataFrame checks

### Added
- Comprehensive DEVELOPMENT_GUIDE.md for contributors
- Detailed instructions for LLM and embedding model replacement
- Error pattern analysis and solutions

### Changed
- Updated .gitignore to exclude development test files
- Improved project structure for open source release

## [1.0.6] - 2025-07-07

### Fixed
- Enhanced None value handling in report_generator.py with explicit float conversions
- Fixed format string errors when statistics contain None or NaN values
- Added pandas notna() checks for DataFrame values in performance analysis
- Improved robustness of metric score formatting throughout report generation

## [1.0.5] - 2025-07-07

### Fixed
- Fixed TypeError in report_generator.py when metric statistics contain None values
- Added proper None value handling in metric score formatting
- Fixed Windows compatibility issue with report generation

## [1.0.4] - 2025-07-07

### Changed
- Version bump to 1.0.4
- Updated all version references across the codebase

## [1.0.3] - 2025-07-07

### Fixed
- CLI version command now shows correct version
- Updated license display to show only Apache-2.0
- Fixed GitHub repository URL in version command

## [1.0.2] - 2025-07-07

### Changed
- Removed MIT license, now using only Apache-2.0
- Updated offline deployment documentation for Windows
- Enhanced project description

## [1.0.1] - 2025-07-07

### Changed
- English README translation
- Updated PyPI package metadata

## [1.0.0] - 2025-07-07

### Added
- 🚀 Initial release as independent package
- 📦 PyPI package support with optional dependencies
- 🤖 Multi-LLM support (HCX-005, Gemini 2.5 Flash)
- 🌐 BGE-M3 local embedding with GPU auto-detection
- 📊 All 5 RAGAS metrics including Answer Correctness
- 💾 Enhanced database with comprehensive data storage
- 📈 Advanced analytics (EDA, time series, anomaly detection)
- 🔍 Complete logging system for API calls and events
- 📤 Elasticsearch-ready NDJSON export
- 🎨 Interactive web dashboard with Plotly visualizations
- 📝 Excel/CSV data import with automatic format detection
- 🔧 Environment-based configuration management
- 🐳 Docker support with multi-stage builds

### Changed
- Restructured from monorepo to standalone package
- Simplified CLI interface with subcommands
- Improved error handling and user feedback
- Enhanced report generation with multiple formats
- Optimized memory usage for large datasets

### Fixed
- LangChain timeout issues with HTTP wrapper implementation
- HCX-005 authentication with proper Bearer token
- Rate limiting for HCX-005 API calls
- Gemini API key configuration issues
- Database transaction handling

### Security
- API keys managed through environment variables
- No hardcoded credentials in codebase
- Secure database file permissions
- HTTPS-only API communications

## [0.2.0] - 2025-07-06 (Pre-release)

### Added
- Enhanced database manager with 6 specialized tables
- Comprehensive logging system
- Elasticsearch export functionality
- Answer Correctness metric integration
- Advanced statistical analysis features

### Changed
- Database schema for better data organization
- Report generation with more detailed insights

## [0.1.0] - 2025-07-05 (Pre-release)

### Added
- Basic RAG evaluation functionality
- Support for HCX-005 and Gemini LLMs
- SQLite database for result storage
- Basic report generation
- Command-line interface

### Known Issues
- LangChain timeout with Google GenAI
- Limited batch processing capabilities

## Version History

- **1.0.0**: First stable release as independent package
- **0.2.0**: Enhanced features and database improvements
- **0.1.0**: Initial development version within RAGTrace

[Unreleased]: https://github.com/yourusername/ragtrace-lite/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/ragtrace-lite/releases/tag/v1.0.0
[0.2.0]: https://github.com/yourusername/ragtrace-lite/releases/tag/v0.2.0
[0.1.0]: https://github.com/yourusername/ragtrace-lite/releases/tag/v0.1.0
