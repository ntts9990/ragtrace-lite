# Maintenance Guide

This guide covers routine maintenance tasks for RAGTrace Lite.

## Daily Tasks

### 1. Monitor System Health

```bash
# Run health check
python scripts/health_check.py

# Check logs for errors
grep ERROR logs/ragtrace_lite.log | tail -20

# Monitor disk usage
df -h | grep -E "/$|/data"
```

### 2. Verify Backups

```bash
# List recent backups
ls -lht backups/ | head -10

# Verify backup integrity
tar -tzf backups/latest_backup.tar.gz | head
```

### 3. Check API Quotas

Monitor your API usage:
- **Gemini**: Check Google Cloud Console
- **HCX-005**: Check Naver Cloud Platform Console

## Weekly Tasks

### 1. Database Optimization

```bash
# Run optimization script
./scripts/optimize_db.sh

# Check database size
du -h data/ragtrace_lite.db
```

### 2. Log Rotation

```bash
# Rotate logs
logrotate -f /etc/logrotate.d/ragtrace-lite

# Clean old logs
find logs/ -name "*.log" -mtime +30 -delete
```

### 3. Security Updates

```bash
# Check for security vulnerabilities
pip audit

# Update dependencies
pip install --upgrade -r requirements.txt
```

### 4. Performance Review

Review metrics in Grafana:
- Average evaluation time
- Error rates
- API latency
- Resource usage

## Monthly Tasks

### 1. Full System Backup

```bash
# Create full backup
./scripts/backup.sh

# Upload to cloud storage (optional)
aws s3 cp backups/monthly_backup.tar.gz s3://your-bucket/
```

### 2. Database Maintenance

```bash
# Analyze database performance
sqlite3 data/ragtrace_lite.db "EXPLAIN QUERY PLAN SELECT ..."

# Archive old data
python scripts/archive_old_data.py --days 90
```

### 3. Dependency Updates

```bash
# Update all dependencies
pip list --outdated
pip install --upgrade -r requirements.txt

# Run tests after update
pytest tests/
```

### 4. Cost Analysis

Review API usage and costs:
- Calculate cost per evaluation
- Identify optimization opportunities
- Plan capacity for next month

## Troubleshooting Common Issues

### High Memory Usage

1. Check for memory leaks:
   ```bash
   ps aux | grep ragtrace
   ```

2. Restart the service:
   ```bash
   docker-compose restart ragtrace-lite
   ```

3. Reduce batch size in config.yaml

### Slow Evaluations

1. Check API latency:
   ```bash
   curl -w "@curl-format.txt" -o /dev/null -s "https://api.example.com"
   ```

2. Optimize database:
   ```bash
   ./scripts/optimize_db.sh
   ```

3. Review batch sizes and concurrency settings

### API Errors

1. Verify API keys:
   ```bash
   python -c "import os; print('Keys set:', bool(os.getenv('GEMINI_API_KEY')))"
   ```

2. Check rate limits:
   - HCX: Max 1 request per 2 seconds
   - Gemini: Check quota in Google Cloud Console

3. Review error logs:
   ```bash
   grep "API.*error" logs/ragtrace_lite.log
   ```

## Automation Scripts

### Crontab Example

```cron
# Daily health check at 6 AM
0 6 * * * /path/to/scripts/health_check.py >> /var/log/health_check.log 2>&1

# Weekly database optimization on Sunday at 2 AM
0 2 * * 0 /path/to/scripts/optimize_db.sh

# Daily backup at 3 AM
0 3 * * * /path/to/scripts/backup.sh

# Log rotation daily at midnight
0 0 * * * /usr/sbin/logrotate -f /etc/logrotate.d/ragtrace-lite
```

### Monitoring Script

Create a simple monitoring script:

```bash
#!/bin/bash
# monitor.sh

# Check if service is running
if ! pgrep -f "ragtrace-lite" > /dev/null; then
    echo "RAGTrace Lite is not running!" | mail -s "Service Down" admin@example.com
    # Attempt restart
    docker-compose up -d ragtrace-lite
fi

# Check disk space
USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $USAGE -gt 80 ]; then
    echo "Disk usage is at ${USAGE}%" | mail -s "Disk Space Warning" admin@example.com
fi

# Check database size
DB_SIZE=$(du -m data/ragtrace_lite.db | cut -f1)
if [ $DB_SIZE -gt 1000 ]; then
    echo "Database size is ${DB_SIZE}MB" | mail -s "Database Size Warning" admin@example.com
fi
```

## Disaster Recovery

### Backup Strategy

1. **Local Backups**: Daily, keep 7 days
2. **Remote Backups**: Weekly, keep 4 weeks
3. **Archive Backups**: Monthly, keep 12 months

### Recovery Procedure

1. Stop the service:
   ```bash
   docker-compose down
   ```

2. Restore from backup:
   ```bash
   tar -xzf backups/backup_YYYYMMDD.tar.gz -C /
   ```

3. Verify database integrity:
   ```bash
   sqlite3 data/ragtrace_lite.db "PRAGMA integrity_check;"
   ```

4. Start the service:
   ```bash
   docker-compose up -d
   ```

5. Run health check:
   ```bash
   python scripts/health_check.py
   ```

## Performance Tuning

### Database Indexes

```sql
-- Add indexes for common queries
CREATE INDEX idx_evaluation_runs_created ON evaluation_runs(created_at);
CREATE INDEX idx_evaluation_results_run ON evaluation_results(run_id);
CREATE INDEX idx_api_logs_timestamp ON api_logs(timestamp);
```

### Configuration Optimization

```yaml
# config.yaml optimizations
evaluation:
  batch_size: 1  # For HCX rate limits
  timeout: 30    # Reduce timeout for faster failures
  
database:
  connection_pool_size: 5
  
api:
  retry_count: 3
  retry_delay: 2
```