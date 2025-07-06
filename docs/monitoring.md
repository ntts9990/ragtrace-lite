# Monitoring and Observability Guide

This guide describes how to monitor RAGTrace Lite in production.

## Metrics Collection

### 1. Application Metrics

RAGTrace Lite exposes the following metrics:

- **Evaluation Metrics**
  - `ragtrace_evaluations_total`: Total number of evaluations
  - `ragtrace_evaluation_duration_seconds`: Evaluation duration histogram
  - `ragtrace_evaluation_errors_total`: Total evaluation errors
  - `ragtrace_evaluation_items_processed`: Number of items processed

- **LLM Metrics**
  - `ragtrace_llm_requests_total`: Total LLM API calls
  - `ragtrace_llm_request_duration_seconds`: LLM request duration
  - `ragtrace_llm_errors_total`: LLM API errors
  - `ragtrace_llm_tokens_used`: Token usage per request

- **Database Metrics**
  - `ragtrace_db_connections_active`: Active database connections
  - `ragtrace_db_queries_total`: Total database queries
  - `ragtrace_db_query_duration_seconds`: Query duration

### 2. System Metrics

Monitor these system-level metrics:

- CPU usage
- Memory usage
- Disk I/O
- Network traffic

### 3. Setting Up Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ragtrace-lite'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

## Logging

### 1. Log Levels

Configure log levels via environment variable:

```bash
export LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### 2. Log Format

Logs are structured in JSON format for easy parsing:

```json
{
  "timestamp": "2024-01-06T12:00:00Z",
  "level": "INFO",
  "category": "evaluation",
  "message": "Evaluation started",
  "run_id": "run_12345",
  "extra": {
    "llm": "hcx",
    "dataset": "test_data.json"
  }
}
```

### 3. Log Aggregation

Send logs to Elasticsearch:

```bash
# Using Filebeat
filebeat -e -c filebeat.yml

# Or direct export
ragtrace-lite-enhanced export-logs /path/to/export.ndjson
```

## Alerting

### 1. Alert Rules

Example Prometheus alert rules:

```yaml
groups:
  - name: ragtrace
    rules:
      - alert: HighErrorRate
        expr: rate(ragtrace_evaluation_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High error rate detected
          
      - alert: LLMAPIDown
        expr: up{job="ragtrace-lite"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: RAGTrace Lite is down
```

### 2. Notification Channels

Configure alertmanager for notifications:

```yaml
route:
  receiver: 'team-notifications'
  
receivers:
  - name: 'team-notifications'
    email_configs:
      - to: 'team@example.com'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK'
```

## Dashboards

### 1. Grafana Dashboard

Import the provided dashboard:

```bash
# Import dashboard
curl -X POST http://localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @grafana-dashboard.json
```

### 2. Key Panels

- Evaluation success rate
- Average evaluation duration
- LLM API latency
- Error rate by type
- Token usage over time

## Health Checks

### 1. Endpoint

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed
```

### 2. Response Format

```json
{
  "status": "healthy",
  "version": "1.0.4",
  "checks": {
    "database": "ok",
    "llm_gemini": "ok",
    "llm_hcx": "ok",
    "disk_space": "ok"
  }
}
```

## Performance Monitoring

### 1. APM Integration

Use OpenTelemetry for distributed tracing:

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Configure tracing
tracer = trace.get_tracer(__name__)
```

### 2. Performance Baselines

Expected performance metrics:

- Evaluation latency: < 2s per item
- Database query: < 100ms
- LLM API call: < 5s
- Memory usage: < 2GB

## Troubleshooting

### 1. Common Issues

**High Memory Usage**
- Check for memory leaks in embeddings
- Monitor batch sizes
- Review database connection pooling

**Slow Evaluations**
- Check LLM API latency
- Review database query performance
- Monitor network connectivity

**API Errors**
- Verify API keys
- Check rate limits
- Monitor API quotas

### 2. Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
export RAGTRACE_DEBUG=true
```

## Maintenance Tasks

### 1. Regular Tasks

- **Daily**
  - Check error logs
  - Monitor disk usage
  - Verify backups

- **Weekly**
  - Review performance metrics
  - Update dependencies
  - Check security advisories

- **Monthly**
  - Analyze usage patterns
  - Optimize database
  - Review cost metrics

### 2. Automation

Use cron jobs for maintenance:

```bash
# Database optimization
0 2 * * 0 /usr/local/bin/optimize-db.sh

# Log rotation
0 0 * * * /usr/local/bin/rotate-logs.sh

# Backup
0 3 * * * /usr/local/bin/backup.sh
```