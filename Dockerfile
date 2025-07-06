# Multi-stage build for RAGTrace Lite
# Stage 1: Builder
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy pyproject.toml and other necessary files
COPY pyproject.toml setup.py MANIFEST.in README.md ./
COPY src/ ./src/

# Build the package
RUN pip install --upgrade pip setuptools wheel build && \
    python -m build --wheel

# Stage 2: Runtime
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 ragtrace && \
    mkdir -p /app /app/data /app/reports /app/logs && \
    chown -R ragtrace:ragtrace /app

# Set working directory
WORKDIR /app

# Copy wheel from builder
COPY --from=builder /build/dist/*.whl /tmp/

# Install the package
RUN pip install --no-cache-dir /tmp/*.whl && \
    rm -rf /tmp/*.whl

# Copy configuration files
COPY --chown=ragtrace:ragtrace config.yaml .env.example ./
COPY --chown=ragtrace:ragtrace data/ ./data/

# Switch to non-root user
USER ragtrace

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/ragtrace/.local/bin:${PATH}"

# Create volume mount points
VOLUME ["/app/data", "/app/reports", "/app/logs"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from ragtrace_lite import __version__; print(__version__)" || exit 1

# Default command
ENTRYPOINT ["ragtrace-lite"]
CMD ["--help"]