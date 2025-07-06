# Changelog

All notable changes to RAGTrace Lite will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial standalone package structure
- Dual licensing (MIT/Apache 2.0)
- Comprehensive installation guide
- Migration guide from RAGTrace
- Security policy documentation

## [1.0.0] - 2025-01-06

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

## [0.2.0] - 2024-12-30 (Pre-release)

### Added
- Enhanced database manager with 6 specialized tables
- Comprehensive logging system
- Elasticsearch export functionality
- Answer Correctness metric integration
- Advanced statistical analysis features

### Changed
- Database schema for better data organization
- Report generation with more detailed insights

## [0.1.0] - 2024-12-15 (Pre-release)

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