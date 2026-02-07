# Alerting Configuration and Procedures

## Overview

The Media Management Web Tool implements a comprehensive alerting system to notify operators of issues requiring attention. The alerting infrastructure integrates with monitoring metrics to detect anomalies and trigger notifications through multiple channels.

## Alert Architecture

### Components

1. **Alert Rules**: Conditions that trigger alerts
2. **Alert Channels**: Notification destinations (email, Slack, PagerDuty)
3. **Alert Escalation**: Escalation procedures for unresolved alerts
4. **Alert Response**: Procedures for responding to alerts
5. **Alert Tuning**: Optimization of alert thresholds

## Alert Rules and Thresholds

### System Alerts

#### High CPU Usage
- **Metric**: `system_cpu_percent`
- **Threshold**: > 80% for 5 minutes
- **Severity**: Warning
- **Action**: Investigate running processes, consider scaling

```promql
system_cpu_percent > 80
```

#### Critical CPU Usage
- **Metric**: `system_cpu_percent`
- **Threshold**: > 95% for 2 minutes
- **Severity**: Critical
- **Action**: Immediate investigation required

```promql
system_cpu_percent > 95
```

#### High Memory Usage
- **Metric**: `system_memory_percent`
- **Threshold**: > 85% for 5 minutes
- **Severity**: Warning
- **Action**: Check for memory leaks, consider scaling

```promql
system_memory_percent > 85
```

#### Critical Memory Usage
- **Metric**: `system_memory_percent`
- **Threshold**: > 95% for 2 minutes
- **Severity**: Critical
- **Action**: Immediate investigation required

```promql
system_memory_percent > 95
```

#### High Disk Usage
- **Metric**: `system_disk_percent`
- **Threshold**: > 90% for 10 minutes
- **Severity**: Warning
- **Action**: Clean up logs, consider expanding disk

```promql
system_disk_percent > 90
```

#### Critical Disk Usage
- **Metric**: `system_disk_percent`
- **Threshold**: > 95% for 5 minutes
- **Severity**: Critical
- **Action**: Immediate action required to free disk space

```promql
system_disk_percent > 95
```

### Application Alerts

#### High Error Rate
- **Metric**: `http_requests_total` with status >= 400
- **Threshold**: > 5% error rate for 5 minutes
- **Severity**: Warning
- **Action**: Check application logs, investigate errors

```promql
rate(http_requests_total{status=~"4..|5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
```

#### Critical Error Rate
- **Metric**: `http_requests_total` with status >= 500
- **Threshold**: > 10% error rate for 2 minutes
- **Severity**: Critical
- **Action**: Immediate investigation required

```promql
rate(http_requests_total{status=~"5.."}[2m]) / rate(http_requests_total[2m]) > 0.10
```

#### High Request Latency
- **Metric**: `http_request_duration_seconds`
- **Threshold**: 95th percentile > 1 second for 5 minutes
- **Severity**: Warning
- **Action**: Investigate slow endpoints, check database performance

```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
```

#### Critical Request Latency
- **Metric**: `http_request_duration_seconds`
- **Threshold**: 95th percentile > 5 seconds for 2 minutes
- **Severity**: Critical
- **Action**: Immediate investigation required

```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[2m])) > 5
```

#### No Requests
- **Metric**: `http_requests_total`
- **Threshold**: No requests for 5 minutes
- **Severity**: Critical
- **Action**: Application may be down

```promql
rate(http_requests_total[5m]) == 0
```

### Database Alerts

#### High Query Duration
- **Metric**: `db_query_duration_seconds`
- **Threshold**: Average > 500ms for 5 minutes
- **Severity**: Warning
- **Action**: Investigate slow queries, check indexes

```promql
rate(db_query_duration_seconds_sum[5m]) / rate(db_query_duration_seconds_count[5m]) > 0.5
```

#### High Slow Query Rate
- **Metric**: `db_slow_queries_total`
- **Threshold**: > 10 slow queries per minute
- **Severity**: Warning
- **Action**: Review slow query log, optimize queries

```promql
rate(db_slow_queries_total[1m]) > 10
```

#### Database Connection Errors
- **Metric**: `db_connections_total{status="error"}`
- **Threshold**: > 0 errors in 5 minutes
- **Severity**: Critical
- **Action**: Check database connectivity, verify credentials

```promql
rate(db_connections_total{status="error"}[5m]) > 0
```

#### High Active Connections
- **Metric**: `db_connections_active`
- **Threshold**: > 80% of pool size for 5 minutes
- **Severity**: Warning
- **Action**: Investigate connection leaks, consider scaling

```promql
db_connections_active > 8
```

### Cache Alerts

#### Low Cache Hit Rate
- **Metric**: `cache_hits_total` vs `cache_misses_total`
- **Threshold**: < 80% hit rate for 10 minutes
- **Severity**: Warning
- **Action**: Investigate cache configuration, check TTLs

```promql
rate(cache_hits_total[10m]) / (rate(cache_hits_total[10m]) + rate(cache_misses_total[10m])) < 0.8
```

#### High Cache Eviction Rate
- **Metric**: `cache_evictions_total`
- **Threshold**: > 100 evictions per minute
- **Severity**: Warning
- **Action**: Increase cache size, review eviction policy

```promql
rate(cache_evictions_total[1m]) > 100
```

#### Cache Unavailable
- **Metric**: Health check cache status
- **Threshold**: Cache status != healthy
- **Severity**: Critical
- **Action**: Check Redis connectivity, restart if needed

### Task Alerts

#### High Task Failure Rate
- **Metric**: `celery_tasks_total{status="error"}`
- **Threshold**: > 5% failure rate for 5 minutes
- **Severity**: Warning
- **Action**: Check task logs, investigate failures

```promql
rate(celery_tasks_total{status="error"}[5m]) / rate(celery_tasks_total[5m]) > 0.05
```

#### Large Task Queue
- **Metric**: `celery_queue_size`
- **Threshold**: > 1000 pending tasks
- **Severity**: Warning
- **Action**: Investigate queue backlog, consider scaling workers

```promql
celery_queue_size > 1000
```

#### Long Task Execution Time
- **Metric**: `celery_task_duration_seconds`
- **Threshold**: Average > 5 minutes for 10 minutes
- **Severity**: Warning
- **Action**: Investigate slow tasks, optimize if possible

```promql
rate(celery_task_duration_seconds_sum[10m]) / rate(celery_task_duration_seconds_count[10m]) > 300
```

## Alert Channels

### Email Notifications

**Configuration:**
```yaml
# Prometheus AlertManager config
receivers:
  - name: 'email'
    email_configs:
      - to: 'ops-team@example.com'
        from: 'alerts@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'alerts@example.com'
        auth_password: 'password'
        headers:
          Subject: 'Alert: {{ .GroupLabels.alertname }}'
```

**Email Template:**
```
Alert: {{ .GroupLabels.alertname }}
Severity: {{ .GroupLabels.severity }}
Status: {{ .Status }}

{{ range .Alerts }}
Instance: {{ .Labels.instance }}
Message: {{ .Annotations.description }}
{{ end }}

View in Grafana: http://grafana.example.com/
```

### Slack Notifications

**Configuration:**
```yaml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true
```

**Slack Message Format:**
```
🚨 Alert: High CPU Usage
Severity: Warning
Status: Firing

Instance: prod-app-01
Value: 85%
Duration: 5 minutes

View in Grafana: http://grafana.example.com/
```

### PagerDuty Integration

**Configuration:**
```yaml
receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_SERVICE_KEY'
        description: '{{ .GroupLabels.alertname }}'
        details:
          firing: '{{ template "pagerduty.default.instances" .Alerts.Firing }}'
```

**Severity Mapping:**
- Critical → PagerDuty Severity: Critical
- Warning → PagerDuty Severity: Warning
- Info → PagerDuty Severity: Info

### Webhook Integration

**Configuration:**
```yaml
receivers:
  - name: 'webhook'
    webhook_configs:
      - url: 'http://example.com/alerts'
        send_resolved: true
```

**Webhook Payload:**
```json
{
  "status": "firing",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "HighCPUUsage",
        "severity": "warning",
        "instance": "prod-app-01"
      },
      "annotations": {
        "summary": "High CPU usage detected",
        "description": "CPU usage is 85% on prod-app-01"
      }
    }
  ]
}
```

## Alert Escalation Procedures

### Level 1: Warning (Automated Response)

**Trigger**: Warning-level alert fires
**Automated Actions**:
1. Send Slack notification to #alerts channel
2. Send email to ops-team@example.com
3. Log alert in monitoring system
4. Create incident ticket (optional)

**Response Time**: 30 minutes

### Level 2: Critical (Immediate Response)

**Trigger**: Critical-level alert fires
**Automated Actions**:
1. Send Slack notification to #critical-alerts channel
2. Send email to ops-team@example.com
3. Create PagerDuty incident
4. Page on-call engineer
5. Create incident ticket
6. Start incident bridge (if needed)

**Response Time**: 5 minutes

### Level 3: Escalation (Management Notification)

**Trigger**: Critical alert unresolved for 15 minutes
**Actions**:
1. Notify engineering manager
2. Notify operations manager
3. Consider incident commander activation
4. Prepare status update for stakeholders

**Response Time**: 15 minutes

### Level 4: Executive Escalation

**Trigger**: Critical alert unresolved for 1 hour
**Actions**:
1. Notify VP of Engineering
2. Notify VP of Operations
3. Activate incident commander
4. Prepare customer communication
5. Consider service degradation notice

**Response Time**: 1 hour

## Alert Response Procedures

### Initial Response

1. **Acknowledge Alert**
   - Acknowledge in PagerDuty/Slack
   - Add comment with initial findings

2. **Gather Information**
   - Check monitoring dashboard
   - Review recent logs
   - Check recent deployments
   - Verify alert accuracy

3. **Assess Impact**
   - Determine customer impact
   - Estimate resolution time
   - Identify affected services

### Investigation

1. **Check Metrics**
   - Review related metrics
   - Look for correlations
   - Check system resources

2. **Review Logs**
   - Check application logs
   - Check system logs
   - Check database logs

3. **Verify Root Cause**
   - Identify root cause
   - Document findings
   - Determine fix approach

### Resolution

1. **Implement Fix**
   - Apply fix or workaround
   - Monitor for effectiveness
   - Document changes

2. **Verify Resolution**
   - Confirm alert clears
   - Verify service recovery
   - Check for side effects

3. **Post-Incident**
   - Document incident
   - Schedule post-mortem
   - Update runbooks
   - Implement preventive measures

## Alert Tuning and Optimization

### Reducing False Positives

1. **Adjust Thresholds**
   - Review alert history
   - Identify false positive patterns
   - Adjust thresholds based on baselines

2. **Increase Duration**
   - Require sustained condition
   - Reduce noise from spikes
   - Example: 5 minutes instead of 1 minute

3. **Add Conditions**
   - Combine multiple metrics
   - Reduce false positives
   - Example: High CPU AND high memory

### Improving Alert Quality

1. **Clear Descriptions**
   - Provide actionable information
   - Include remediation steps
   - Link to relevant documentation

2. **Appropriate Severity**
   - Use correct severity level
   - Avoid alert fatigue
   - Reserve critical for true emergencies

3. **Regular Review**
   - Review alert effectiveness
   - Analyze alert history
   - Adjust based on feedback

### Alert Tuning Process

```
1. Monitor alert for 1 week
2. Analyze false positive rate
3. If > 10% false positives:
   - Increase threshold
   - Increase duration
   - Add additional conditions
4. Re-evaluate after 1 week
5. Repeat until acceptable
```

## Alert Runbooks

### High CPU Usage

**Alert**: `system_cpu_percent > 80`

**Investigation**:
```bash
# Check top processes
top -b -n 1 | head -20

# Check CPU usage by container
docker stats

# Check Kubernetes pod metrics
kubectl top pods -n production
```

**Common Causes**:
- High request volume
- Inefficient query
- Memory pressure causing swapping
- Background job running

**Resolution**:
1. Identify high-CPU process
2. Check if expected
3. Optimize if possible
4. Scale if needed

### High Memory Usage

**Alert**: `system_memory_percent > 85`

**Investigation**:
```bash
# Check memory usage
free -h

# Check process memory
ps aux --sort=-%mem | head -10

# Check memory by container
docker stats
```

**Common Causes**:
- Memory leak
- Large cache
- Too many connections
- Inefficient query results

**Resolution**:
1. Identify high-memory process
2. Check for memory leaks
3. Optimize if possible
4. Restart if necessary

### High Error Rate

**Alert**: `error_rate > 5%`

**Investigation**:
```bash
# Check error logs
grep ERROR logs/error.log | tail -100

# Check error rate by endpoint
grep '"level": "ERROR"' logs/api.log | jq '.endpoint' | sort | uniq -c

# Check error types
grep '"level": "ERROR"' logs/error.log | jq '.error_type' | sort | uniq -c
```

**Common Causes**:
- Database connection issues
- External API failures
- Invalid input
- Resource exhaustion

**Resolution**:
1. Identify error type
2. Check related services
3. Fix root cause
4. Monitor for recurrence

### Database Connection Errors

**Alert**: `db_connections_total{status="error"} > 0`

**Investigation**:
```bash
# Check database connectivity
psql -h db.example.com -U user -d database -c "SELECT 1"

# Check connection pool
SELECT count(*) FROM pg_stat_activity;

# Check database logs
tail -f /var/log/postgresql/postgresql.log
```

**Common Causes**:
- Database unavailable
- Connection pool exhausted
- Network connectivity issue
- Authentication failure

**Resolution**:
1. Verify database is running
2. Check network connectivity
3. Verify credentials
4. Check connection pool settings

## Alert Dashboard

### Grafana Alert Dashboard

Create a dashboard to visualize alert status:

1. **Alert Status Panel**
   - Shows firing alerts
   - Color-coded by severity
   - Links to runbooks

2. **Alert History Panel**
   - Shows alert trends
   - Identifies recurring issues
   - Helps with tuning

3. **Alert Statistics Panel**
   - Total alerts
   - Alerts by severity
   - Mean time to resolution

## Best Practices

1. **Alert on Symptoms, Not Causes**: Alert on user-visible issues
2. **Actionable Alerts**: Every alert should have a clear action
3. **Appropriate Severity**: Use correct severity level
4. **Clear Descriptions**: Provide context and remediation steps
5. **Regular Review**: Review and tune alerts regularly
6. **Document Runbooks**: Maintain up-to-date runbooks
7. **Test Alerts**: Regularly test alert channels
8. **Avoid Alert Fatigue**: Reduce false positives

## Related Documentation

- [Monitoring Documentation](MONITORING.md)
- [Logging Documentation](LOGGING.md)
- [Grafana Dashboards](GRAFANA_DASHBOARDS.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Troubleshooting Guide](DEPLOYMENT_TROUBLESHOOTING.md)
