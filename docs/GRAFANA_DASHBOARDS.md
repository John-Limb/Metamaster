# Grafana Dashboard Configuration

## Overview

This document provides guidance for creating and configuring Grafana dashboards to visualize metrics from the Media Management Web Tool. Dashboards provide real-time visibility into application health, performance, and resource utilization.

## Dashboard Architecture

### Dashboard Types

1. **Overview Dashboard**: High-level system health and key metrics
2. **Application Dashboard**: Request metrics, error rates, latency
3. **Database Dashboard**: Query performance, connections, slow queries
4. **Cache Dashboard**: Hit rates, memory usage, evictions
5. **Task Dashboard**: Queue size, execution time, failure rates
6. **System Dashboard**: CPU, memory, disk, process metrics
7. **Alert Dashboard**: Alert status, history, statistics

## Grafana Setup

### Prerequisites

1. **Prometheus Data Source**
   - URL: `http://prometheus:9090`
   - Access: Server
   - Scrape interval: 15s

2. **Grafana Installation**
   ```bash
   docker run -d \
     -p 3000:3000 \
     -e GF_SECURITY_ADMIN_PASSWORD=admin \
     grafana/grafana:latest
   ```

3. **Access Grafana**
   - URL: `http://localhost:3000`
   - Username: admin
   - Password: admin

## Overview Dashboard

### Dashboard JSON

```json
{
  "dashboard": {
    "title": "Media Management - Overview",
    "tags": ["overview", "production"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Application Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"media-app\"}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              {
                "type": "value",
                "options": {
                  "1": {
                    "text": "UP",
                    "color": "green"
                  },
                  "0": {
                    "text": "DOWN",
                    "color": "red"
                  }
                }
              }
            ]
          }
        }
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "P95 Latency",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "CPU Usage",
        "type": "gauge",
        "targets": [
          {
            "expr": "system_cpu_percent"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "max": 100,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "green", "value": 0},
                {"color": "yellow", "value": 70},
                {"color": "red", "value": 90}
              ]
            }
          }
        }
      },
      {
        "title": "Memory Usage",
        "type": "gauge",
        "targets": [
          {
            "expr": "system_memory_percent"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "max": 100,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "green", "value": 0},
                {"color": "yellow", "value": 75},
                {"color": "red", "value": 90}
              ]
            }
          }
        }
      },
      {
        "title": "Disk Usage",
        "type": "gauge",
        "targets": [
          {
            "expr": "system_disk_percent"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "max": 100,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "green", "value": 0},
                {"color": "yellow", "value": 80},
                {"color": "red", "value": 95}
              ]
            }
          }
        }
      }
    ]
  }
}
```

## Application Dashboard

### Key Metrics

1. **Request Metrics**
   - Total requests
   - Request rate (req/s)
   - Request distribution by endpoint
   - Request distribution by method

2. **Latency Metrics**
   - Average latency
   - P50, P95, P99 latency
   - Latency by endpoint
   - Latency trends

3. **Error Metrics**
   - Error rate
   - Error count by status code
   - Error count by endpoint
   - Error trends

4. **Throughput**
   - Requests per second
   - Bytes in/out
   - Response size distribution

### Dashboard Queries

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Average latency
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# P99 latency
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Requests by endpoint
rate(http_requests_total[5m]) by (endpoint)

# Errors by status code
rate(http_requests_total{status=~"[45].."}[5m]) by (status)

# Latency by endpoint
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) by (endpoint)
```

## Database Dashboard

### Key Metrics

1. **Query Performance**
   - Average query time
   - Query count
   - Slow query count
   - Query rate

2. **Connections**
   - Active connections
   - Connection pool usage
   - Connection errors
   - Connection rate

3. **Query Distribution**
   - Queries by operation type
   - Query time by operation
   - Slow queries by operation

### Dashboard Queries

```promql
# Average query time
rate(db_query_duration_seconds_sum[5m]) / rate(db_query_duration_seconds_count[5m])

# Query rate
rate(db_queries_total[5m])

# Slow query rate
rate(db_slow_queries_total[5m])

# Active connections
db_connections_active

# Connection errors
rate(db_connections_total{status="error"}[5m])

# Query time by operation
rate(db_query_duration_seconds_sum[5m]) by (operation) / rate(db_query_duration_seconds_count[5m]) by (operation)

# Queries by operation
rate(db_queries_total[5m]) by (operation)
```

## Cache Dashboard

### Key Metrics

1. **Cache Efficiency**
   - Hit rate
   - Hit count
   - Miss count
   - Eviction count

2. **Cache Performance**
   - Operation latency
   - Memory usage
   - Eviction rate

3. **Cache Trends**
   - Hit rate over time
   - Memory usage over time
   - Eviction trends

### Dashboard Queries

```promql
# Cache hit rate
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))

# Cache hits
rate(cache_hits_total[5m])

# Cache misses
rate(cache_misses_total[5m])

# Cache evictions
rate(cache_evictions_total[5m])

# Cache memory usage
cache_memory_bytes

# Cache operation latency
rate(cache_operation_duration_seconds_sum[5m]) by (operation) / rate(cache_operation_duration_seconds_count[5m]) by (operation)
```

## Task Dashboard

### Key Metrics

1. **Task Execution**
   - Task count
   - Task rate
   - Success rate
   - Failure rate

2. **Task Performance**
   - Average execution time
   - Execution time by task
   - Queue size

3. **Task Trends**
   - Task rate over time
   - Failure rate over time
   - Queue size over time

### Dashboard Queries

```promql
# Task rate
rate(celery_tasks_total[5m])

# Task success rate
rate(celery_tasks_total{status="success"}[5m]) / rate(celery_tasks_total[5m])

# Task failure rate
rate(celery_tasks_total{status="error"}[5m]) / rate(celery_tasks_total[5m])

# Average task execution time
rate(celery_task_duration_seconds_sum[5m]) by (task_name) / rate(celery_task_duration_seconds_count[5m]) by (task_name)

# Queue size
celery_queue_size

# Active tasks
celery_active_tasks

# Task rate by task name
rate(celery_tasks_total[5m]) by (task_name)
```

## System Dashboard

### Key Metrics

1. **CPU Metrics**
   - System CPU usage
   - Process CPU usage
   - CPU usage over time

2. **Memory Metrics**
   - System memory usage
   - Process memory usage
   - Available memory
   - Memory usage over time

3. **Disk Metrics**
   - Disk usage
   - Available disk space
   - Disk usage over time

4. **Process Metrics**
   - Process memory
   - Process CPU
   - Uptime

### Dashboard Queries

```promql
# System CPU
system_cpu_percent

# Process CPU
process_cpu_percent

# System memory
system_memory_percent

# Available memory
system_memory_available_bytes

# Process memory
process_memory_bytes

# Disk usage
system_disk_percent

# Available disk
system_disk_available_bytes

# Uptime
app_uptime_seconds
```

## Alert Dashboard

### Key Metrics

1. **Alert Status**
   - Firing alerts
   - Resolved alerts
   - Alert count by severity

2. **Alert History**
   - Alert trends
   - Mean time to resolution
   - Alert frequency

3. **Alert Statistics**
   - Total alerts
   - Alerts by type
   - Alerts by severity

### Dashboard Panels

```json
{
  "title": "Firing Alerts",
  "type": "table",
  "targets": [
    {
      "expr": "ALERTS{alertstate=\"firing\"}"
    }
  ]
}
```

## Creating Custom Dashboards

### Step 1: Create Dashboard

1. Click "+" in left sidebar
2. Select "Dashboard"
3. Click "Add new panel"

### Step 2: Add Panels

1. Select visualization type
2. Enter Prometheus query
3. Configure display options
4. Save panel

### Step 3: Configure Dashboard

1. Set dashboard title
2. Add tags
3. Set refresh interval
4. Configure time range
5. Save dashboard

### Step 4: Share Dashboard

1. Click "Share" button
2. Generate link
3. Configure sharing options
4. Share with team

## Dashboard Best Practices

1. **Clear Titles**: Use descriptive panel titles
2. **Appropriate Visualizations**: Choose visualization that best represents data
3. **Consistent Units**: Use consistent units across panels
4. **Color Coding**: Use colors to indicate status
5. **Drill-Down**: Link panels for drill-down analysis
6. **Refresh Rate**: Set appropriate refresh interval
7. **Time Range**: Use appropriate time range for analysis
8. **Documentation**: Add descriptions to dashboards

## Dashboard Templates

### Template Variables

Create reusable dashboards with template variables:

```json
{
  "templating": {
    "list": [
      {
        "name": "instance",
        "type": "query",
        "datasource": "Prometheus",
        "query": "label_values(up, instance)"
      },
      {
        "name": "job",
        "type": "query",
        "datasource": "Prometheus",
        "query": "label_values(up, job)"
      }
    ]
  }
}
```

### Using Variables

```promql
# Query with variables
http_requests_total{instance="$instance", job="$job"}
```

## Dashboard Export and Import

### Export Dashboard

1. Click "Share" button
2. Select "Export"
3. Choose "Save to file" or "Copy JSON"

### Import Dashboard

1. Click "+" in left sidebar
2. Select "Import"
3. Paste JSON or upload file
4. Select data source
5. Click "Import"

## Alerting in Grafana

### Create Alert Rule

1. Open dashboard panel
2. Click "Alert" tab
3. Configure alert condition
4. Set notification channel
5. Save alert

### Alert Notification Channels

1. Click "Alerting" → "Notification channels"
2. Click "New channel"
3. Select channel type (Email, Slack, PagerDuty, etc.)
4. Configure channel settings
5. Test notification
6. Save channel

## Performance Optimization

### Dashboard Performance

1. **Limit Time Range**: Use appropriate time range
2. **Reduce Query Complexity**: Simplify queries
3. **Use Recording Rules**: Pre-compute common queries
4. **Increase Scrape Interval**: If appropriate
5. **Archive Old Data**: Remove old metrics

### Query Optimization

```promql
# Inefficient: High cardinality
rate(http_requests_total[5m])

# Efficient: Aggregated
rate(http_requests_total[5m]) by (endpoint)

# Efficient: Filtered
rate(http_requests_total{job="media-app"}[5m])
```

## Related Documentation

- [Monitoring Documentation](MONITORING.md)
- [Alerting Configuration](ALERTING.md)
- [Logging Documentation](LOGGING.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
