# Queue & System Health Drill-Down Design

**Date:** 2026-03-01
**Branch:** feat/queue-health-drilldown
**Status:** Approved

## Problem

The dashboard shows a "Health Check" activity entry (overall status only) and "Pending Tasks" / "Completed Tasks" stat cards, but neither is clickable. The underlying data and backend APIs are richer than what's surfaced — the detailed health check returns per-component checks (database, Redis, system, application), and the queue service supports full task management (list, retry, cancel, details). Users cannot drill into either without navigating manually.

## Solution

Add two dedicated full pages — `/queue` and `/system-health` — reachable from the dashboard by clicking the relevant widgets, and accessible directly from the sidebar nav.

## Architecture

### Backend

**New endpoint:** `GET /health/logs?lines=10`

Reads the tail of each component's structured JSON log file and returns parsed entries.

Response shape:
```json
{
  "database": [
    { "timestamp": "2026-03-01T12:00:00", "level": "INFO", "message": "Query executed: 12ms" }
  ],
  "cache": [...],
  "tasks": [...],
  "api": [...],
  "external_api": [...]
}
```

Component-to-file mapping:
| Component | Log file |
|---|---|
| database | `logs/database.log` |
| cache | `logs/cache.log` |
| tasks | `logs/tasks.log` |
| api | `logs/api.log` |
| external_api | `logs/external_api.log` |

Implementation: tail the file, parse each JSON line, return last N entries. Files that don't exist return an empty array (graceful degradation for fresh installs).

**New frontend service method:** `healthService.getComponentLogs(lines?: number)` calling the new endpoint.

### Frontend — `/queue` Page

Wraps the existing `QueuePanel` component (which already handles polling, status filters, and the task list UI) inside a proper page with:

- Page header with title and live status badge
- `QueuePanel` with its stub handlers replaced by real `queueService` calls:
  - `onRetry(id)` → `queueService.retryTask(id)` then refresh
  - `onCancel(id)` → `queueService.cancelTask(id)` then refresh
  - `onViewDetails(id)` → expand an inline detail panel below the task row showing task metadata and error message (if failed)

### Frontend — `/system-health` Page

Fetches `/health/detailed` on mount and polls `/health/logs` every 2 seconds.

Layout: a grid of component cards, one per check returned by the API. Each card shows:
- Component name and coloured status dot (healthy = green, warning/degraded = amber, unhealthy = red)
- Key metrics inline (e.g. CPU %, memory %, error rate, hit rate — whatever the check returns)
- A log tail section showing the last 10 lines for that component, rendered in a dark monospace block (timestamp · level · message)
- The log section auto-updates every 2 seconds without re-fetching the health status

Components shown: `system`, `application`, `database`, `cache`, `redis` (from `/health/detailed`), plus whatever the monitoring service reports.

### Dashboard Wiring

- `StatCard` for "Pending Tasks" → add `onClick={() => navigate('/queue')}`
- `StatCard` for "Completed Tasks" → add `onClick={() => navigate('/queue')}`
- "Health Check" activity item in `RecentActivity` → add `onClick: () => navigate('/system-health')` when building the activity object in `Dashboard.tsx`

### Navigation

Two new entries added to `Sidebar.tsx` `navItems` array, below Storage:

| Label | Path | Icon |
|---|---|---|
| Queue | `/queue` | `FaList` (react-icons/fa) |
| System Health | `/system-health` | `FaServer` (react-icons/fa) |

Two new lazy-loaded routes added to `App.tsx`.

## Data Flow

```
Dashboard widget click
  → navigate('/queue') or navigate('/system-health')

/queue page
  └─ QueuePanel (Zustand queueStore, polls every 5s)
       └─ QueueItem (retry/cancel/view-details → queueService)

/system-health page
  ├─ healthService.getDetailedHealth() [on mount, manual refresh]
  └─ healthService.getComponentLogs(10) [setInterval 2000ms]
       └─ ComponentHealthCard × N
            └─ LogTailBlock (last 10 lines, monospace)
```

## Error Handling

- `/health/logs` endpoint: if a log file doesn't exist, return `[]` for that component — never 500
- System Health page: if `/health/detailed` fails, show error state with retry button; log tail section shows "No logs available" per component
- Queue page: retry/cancel failures surface as inline toast or error banner (reuse existing error patterns); don't optimistically remove the task from the list

## Testing

- Backend: unit test for the log-tail endpoint — verifies file-not-found returns `[]`, verifies correct number of lines returned, verifies JSON parse errors in a line are skipped gracefully
- Frontend: type-check passes with no new errors beyond the 10 pre-existing baseline errors
