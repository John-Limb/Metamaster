# Queue & System Health Drill-Down — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `/queue` and `/system-health` pages with click-through from dashboard widgets, plus a live 2-second log tail per health component on the System Health page.

**Architecture:** New backend endpoint tails component-specific log files and returns parsed JSON entries; two new frontend pages wrap existing components; dashboard stat cards and health activity item get `onClick` navigation; sidebar gets two new nav entries.

**Tech Stack:** FastAPI + Python stdlib (pathlib), React + TypeScript, Zustand (already in use), react-router-dom, react-icons/fa

**Working directory for all commands:** `.worktrees/feat/queue-health-drilldown`

**Baseline:** 10 pre-existing TypeScript errors (all `EnrichmentBadge` import errors, unrelated to this feature). Do not introduce new ones.

---

### Task 1: Backend — `_tail_log` helper + `/health/logs` endpoint

**Files:**
- Modify: `app/api/v1/health/endpoints.py`
- Create: `tests/test_health_logs.py`

**Context:** Log files are written to `logs/<component>.log` by `app/core/logging_config.py`. Each line is JSON with at minimum `timestamp`, `level`, `message` keys. Files may not exist on fresh installs. The helper is module-level so tests can import it directly.

**Step 1: Write the failing tests**

Create `tests/test_health_logs.py`:

```python
"""Tests for the /health/logs endpoint helper."""
import json
import pytest
from pathlib import Path


def test_tail_log_returns_empty_for_missing_file():
    from app.api.v1.health.endpoints import _tail_log
    result = _tail_log("nonexistent_file_xyz.log", 10)
    assert result == []


def test_tail_log_returns_last_n_lines(tmp_path):
    from app.api.v1.health.endpoints import _tail_log
    log_file = tmp_path / "test.log"
    entries = [
        json.dumps({"timestamp": f"2026-03-01T00:00:0{i}", "level": "INFO", "message": f"msg {i}"})
        for i in range(15)
    ]
    log_file.write_text("\n".join(entries), encoding="utf-8")
    result = _tail_log(str(log_file), 10)
    assert len(result) == 10
    assert result[-1]["message"] == "msg 14"
    assert result[0]["message"] == "msg 5"


def test_tail_log_returns_all_lines_when_fewer_than_n(tmp_path):
    from app.api.v1.health.endpoints import _tail_log
    log_file = tmp_path / "test.log"
    entries = [
        json.dumps({"timestamp": "2026-03-01T00:00:00", "level": "INFO", "message": "only line"})
    ]
    log_file.write_text("\n".join(entries), encoding="utf-8")
    result = _tail_log(str(log_file), 10)
    assert len(result) == 1
    assert result[0]["message"] == "only line"


def test_tail_log_skips_invalid_json_gracefully(tmp_path):
    from app.api.v1.health.endpoints import _tail_log
    log_file = tmp_path / "test.log"
    log_file.write_text(
        '{"timestamp": "t", "level": "INFO", "message": "ok"}\nnot json at all\n',
        encoding="utf-8",
    )
    result = _tail_log(str(log_file), 10)
    assert len(result) == 2
    assert result[0]["message"] == "ok"
    assert result[1]["level"] == "RAW"
    assert "not json at all" in result[1]["message"]


def test_tail_log_skips_blank_lines(tmp_path):
    from app.api.v1.health.endpoints import _tail_log
    log_file = tmp_path / "test.log"
    log_file.write_text(
        '{"timestamp": "t", "level": "INFO", "message": "line1"}\n\n\n',
        encoding="utf-8",
    )
    result = _tail_log(str(log_file), 10)
    assert len(result) == 1
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_health_logs.py -v
```
Expected: `ImportError` or `AttributeError` — `_tail_log` doesn't exist yet.

**Step 3: Add `_tail_log` and the endpoint to `app/api/v1/health/endpoints.py`**

Add these imports at the top of the file (after existing imports):
```python
import json
from pathlib import Path
from typing import Any
```

Add the helper function and new endpoint **before** the existing `@router.get("/")` line:

```python
_COMPONENT_LOG_FILES: dict[str, str] = {
    "database": "logs/database.log",
    "cache": "logs/cache.log",
    "tasks": "logs/tasks.log",
    "api": "logs/api.log",
    "external_api": "logs/external_api.log",
}


def _tail_log(filepath: str, n: int) -> list[dict[str, Any]]:
    """Return the last n parsed log entries from a JSON-per-line log file."""
    path = Path(filepath)
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        tail = lines[-n:] if len(lines) > n else lines
        result: list[dict[str, Any]] = []
        for raw in tail:
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
                result.append({
                    "timestamp": entry.get("timestamp", ""),
                    "level": entry.get("level", ""),
                    "message": entry.get("message", ""),
                })
            except json.JSONDecodeError:
                result.append({"timestamp": "", "level": "RAW", "message": raw})
        return result
    except Exception:
        return []


@router.get("/logs")
async def component_logs(lines: int = 10) -> dict[str, list[dict[str, Any]]]:
    """Return the last N log lines per component."""
    return {
        component: _tail_log(filepath, lines)
        for component, filepath in _COMPONENT_LOG_FILES.items()
    }
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_health_logs.py -v
```
Expected: 5 passed.

**Step 5: Stage files**

```bash
git add app/api/v1/health/endpoints.py tests/test_health_logs.py
```

---

### Task 2: Frontend — `healthService.getComponentLogs()` method

**Files:**
- Modify: `frontend/src/services/healthService.ts`

**Context:** Add types and a new method to the existing healthService export object. No test needed — it's a thin API wrapper.

**Step 1: Add the types and method**

At the top of `frontend/src/services/healthService.ts`, after the existing interfaces, add:

```typescript
export interface LogEntry {
  timestamp: string
  level: string
  message: string
}

export interface ComponentLogs {
  database: LogEntry[]
  cache: LogEntry[]
  tasks: LogEntry[]
  api: LogEntry[]
  external_api: LogEntry[]
}
```

Inside the `healthService` object, after `isAlive`, add:

```typescript
  getComponentLogs: async (lines = 10): Promise<ComponentLogs> => {
    try {
      const response = await apiClient.get<ComponentLogs>(`/health/logs?lines=${lines}`)
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'getComponentLogs')
      throw error
    }
  },
```

**Step 2: Stage**

```bash
git add frontend/src/services/healthService.ts
```

---

### Task 3: Frontend — Fix `QueuePanel` `handleViewDetails`

**Files:**
- Modify: `frontend/src/components/queue/QueuePanel.tsx`

**Context:** `QueueItem` already calls `retryTask`/`cancelTask` from `queueStore` directly — those actions are functional. Only `handleViewDetails` is a stub (`console.log`). Implement it as a toggle: clicking "Details" on a task sets `selectedTaskId`; a detail panel renders inline below that task row showing full task data fetched from the store.

**Step 1: Add `selectedTaskId` state and fix the handler**

Replace the existing `handleViewDetails` callback and update the task list render in `QueuePanel.tsx`.

At the top of the `QueuePanel` function body, after the store destructure, add:
```typescript
const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
const { fetchTaskDetails } = useQueueStore()
```

Replace the existing stub handler:
```typescript
// OLD (remove):
const handleViewDetails = useCallback((taskId: string) => {
  console.log('Viewing details for task:', taskId)
}, [])

// NEW:
const handleViewDetails = useCallback((taskId: string) => {
  setSelectedTaskId((prev) => (prev === taskId ? null : taskId))
}, [])
```

In the task list render, replace:
```typescript
// OLD:
{filteredTasks.map((task) => (
  <QueueItem
    key={task.id}
    task={task}
    onRetry={handleRetryTask}
    onCancel={handleCancelTask}
    onViewDetails={handleViewDetails}
  />
))}

// NEW:
{filteredTasks.map((task) => (
  <React.Fragment key={task.id}>
    <QueueItem
      task={task}
      onRetry={handleRetryTask}
      onCancel={handleCancelTask}
      onViewDetails={handleViewDetails}
    />
    {selectedTaskId === task.id && (
      <div className="border border-t-0 border-gray-200 rounded-b-lg bg-gray-50 dark:bg-gray-800 p-4 text-sm font-mono space-y-1">
        <div><span className="text-gray-500">ID:</span> <span className="text-gray-900 dark:text-gray-100">{task.id}</span></div>
        <div><span className="text-gray-500">Type:</span> <span className="text-gray-900 dark:text-gray-100">{task.type}</span></div>
        <div><span className="text-gray-500">Status:</span> <span className="text-gray-900 dark:text-gray-100">{task.status}</span></div>
        <div><span className="text-gray-500">Created:</span> <span className="text-gray-900 dark:text-gray-100">{new Date(task.createdAt).toISOString()}</span></div>
        {task.updatedAt && (
          <div><span className="text-gray-500">Updated:</span> <span className="text-gray-900 dark:text-gray-100">{new Date(task.updatedAt).toISOString()}</span></div>
        )}
        {task.error && (
          <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
            <span className="text-red-600 dark:text-red-400">{task.error}</span>
          </div>
        )}
      </div>
    )}
  </React.Fragment>
))}
```

Make sure `React` is imported (it already is via `import React, { ... } from 'react'`).

**Step 2: Type check**

```bash
cd frontend && npm run type-check 2>&1 | grep "error TS" | wc -l
```
Expected: still 10 (no new errors).

**Step 3: Stage**

```bash
git add frontend/src/components/queue/QueuePanel.tsx
```

---

### Task 4: Frontend — Create `QueuePage`

**Files:**
- Create: `frontend/src/pages/QueuePage.tsx`

**Context:** Thin page wrapper around the existing `QueuePanel`. Adds a page header and connects the back-navigation link.

**Step 1: Create the file**

```typescript
import React from 'react'
import { QueuePanel } from '@/components/queue/QueuePanel'

export function QueuePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Task Queue</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Monitor and manage background tasks — retry failures, cancel pending work, inspect task details.
        </p>
      </div>
      <QueuePanel autoRefresh refreshInterval={5000} />
    </div>
  )
}

export default QueuePage
```

**Step 2: Type check**

```bash
cd frontend && npm run type-check 2>&1 | grep "error TS" | wc -l
```
Expected: still 10.

**Step 3: Stage**

```bash
git add frontend/src/pages/QueuePage.tsx
```

---

### Task 5: Frontend — Create `SystemHealthPage`

**Files:**
- Create: `frontend/src/pages/SystemHealthPage.tsx`

**Context:** Fetches `/health/detailed` on mount (and on manual refresh). Polls `/health/logs` every 2 seconds using `setInterval`. Renders one card per component check. The `DetailedHealthCheck` type is already in `healthService.ts`.

**Step 1: Create the file**

```typescript
import React, { useEffect, useState, useRef, useCallback } from 'react'
import { healthService, type DetailedHealthCheck, type ComponentLogs, type LogEntry } from '@/services/healthService'
import { Card } from '@/components/common/Card'
import { Button } from '@/components/common/Button'

const STATUS_DOT: Record<string, string> = {
  healthy: 'bg-emerald-500',
  warning: 'bg-amber-400',
  degraded: 'bg-amber-400',
  unhealthy: 'bg-red-500',
  unavailable: 'bg-slate-400',
}

const STATUS_LABEL: Record<string, string> = {
  healthy: 'Healthy',
  warning: 'Warning',
  degraded: 'Degraded',
  unhealthy: 'Unhealthy',
  unavailable: 'Unavailable',
}

const LOG_COMPONENT_MAP: Record<string, keyof ComponentLogs> = {
  database: 'database',
  cache: 'cache',
  redis: 'cache',
  tasks: 'tasks',
  application: 'api',
  system: 'api',
  api: 'api',
  external_api: 'external_api',
}

function LogTail({ entries }: { entries: LogEntry[] }) {
  if (entries.length === 0) {
    return (
      <p className="text-xs text-slate-500 dark:text-slate-400 italic">No log entries available.</p>
    )
  }
  return (
    <div className="bg-slate-950 rounded p-3 space-y-0.5 overflow-x-auto">
      {entries.map((entry, i) => (
        <div key={i} className="flex gap-2 text-xs font-mono whitespace-nowrap">
          <span className="text-slate-500 flex-shrink-0">
            {entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : '—'}
          </span>
          <span className={`flex-shrink-0 font-semibold ${
            entry.level === 'ERROR' ? 'text-red-400' :
            entry.level === 'WARNING' ? 'text-amber-400' :
            entry.level === 'RAW' ? 'text-slate-400' :
            'text-emerald-400'
          }`}>
            {entry.level || '—'}
          </span>
          <span className="text-slate-300 truncate">{entry.message}</span>
        </div>
      ))}
    </div>
  )
}

function ComponentCard({
  name,
  check,
  logs,
}: {
  name: string
  check: { status: string; [key: string]: unknown }
  logs: LogEntry[]
}) {
  const status = check.status ?? 'unknown'
  const dotColor = STATUS_DOT[status] ?? 'bg-slate-400'
  const label = STATUS_LABEL[status] ?? status

  const extraKeys = Object.keys(check).filter((k) => k !== 'status' && k !== 'error')

  return (
    <Card variant="elevated" className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${dotColor}`} />
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white capitalize">
            {name.replace(/_/g, ' ')}
          </h3>
        </div>
        <span className={`text-xs font-medium ${
          status === 'healthy' ? 'text-emerald-600 dark:text-emerald-400' :
          status === 'unhealthy' ? 'text-red-600 dark:text-red-400' :
          'text-amber-600 dark:text-amber-400'
        }`}>
          {label}
        </span>
      </div>

      {extraKeys.length > 0 && (
        <div className="flex flex-wrap gap-x-4 gap-y-1">
          {extraKeys.map((key) => (
            <div key={key} className="text-xs text-slate-600 dark:text-slate-400">
              <span className="font-medium">{key.replace(/_/g, ' ')}:</span>{' '}
              {typeof check[key] === 'number'
                ? (check[key] as number).toFixed(1)
                : String(check[key])}
            </div>
          ))}
        </div>
      )}

      {check.error && (
        <p className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded p-2">
          {String(check.error)}
        </p>
      )}

      <div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-1 font-medium uppercase tracking-wide">
          Recent logs
        </p>
        <LogTail entries={logs} />
      </div>
    </Card>
  )
}

export function SystemHealthPage() {
  const [health, setHealth] = useState<DetailedHealthCheck | null>(null)
  const [logs, setLogs] = useState<ComponentLogs | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const logIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchHealth = useCallback(async () => {
    try {
      const data = await healthService.getDetailedHealth()
      setHealth(data)
      setError(null)
    } catch {
      setError('Failed to load health status.')
    }
  }, [])

  const fetchLogs = useCallback(async () => {
    try {
      const data = await healthService.getComponentLogs(10)
      setLogs(data)
    } catch {
      // Non-fatal — keep stale log data
    }
  }, [])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await Promise.all([fetchHealth(), fetchLogs()])
    setIsRefreshing(false)
  }

  useEffect(() => {
    Promise.all([fetchHealth(), fetchLogs()]).finally(() => setIsLoading(false))

    logIntervalRef.current = setInterval(fetchLogs, 2000)
    return () => {
      if (logIntervalRef.current) clearInterval(logIntervalRef.current)
    }
  }, [fetchHealth, fetchLogs])

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-56 bg-slate-200 dark:bg-slate-700 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (error && !health) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">System Health</h1>
        <Card variant="elevated" className="p-8 text-center">
          <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
          <Button variant="primary" onClick={handleRefresh}>Retry</Button>
        </Card>
      </div>
    )
  }

  const overallStatus = health?.status ?? 'unknown'
  const checks = health?.checks ?? {}

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">System Health</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Live component status and log tails — refreshing every 2 seconds.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${STATUS_DOT[overallStatus] ?? 'bg-slate-400'}`} />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300 capitalize">
              {STATUS_LABEL[overallStatus] ?? overallStatus}
            </span>
          </div>
          <Button variant="outline" onClick={handleRefresh} loading={isRefreshing}>
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Object.entries(checks).map(([name, check]) => {
          const logKey = LOG_COMPONENT_MAP[name]
          const componentLogs = logKey && logs ? logs[logKey] : []
          return (
            <ComponentCard
              key={name}
              name={name}
              check={check}
              logs={componentLogs}
            />
          )
        })}
      </div>

      {health?.timestamp && (
        <p className="text-xs text-slate-400 dark:text-slate-500 text-right">
          Health checked at {new Date(health.timestamp).toLocaleTimeString()}
        </p>
      )}
    </div>
  )
}

export default SystemHealthPage
```

**Step 2: Type check**

```bash
cd frontend && npm run type-check 2>&1 | grep "error TS" | wc -l
```
Expected: still 10.

**Step 3: Stage**

```bash
git add frontend/src/pages/SystemHealthPage.tsx
```

---

### Task 6: Frontend — Register routes in `App.tsx`

**Files:**
- Modify: `frontend/src/App.tsx`

**Step 1: Add lazy imports**

After the `OrganisationPage` lazy import line, add:

```typescript
const QueuePage = lazy(() => import('./pages/QueuePage').then(m => ({ default: m.QueuePage })))
const SystemHealthPage = lazy(() => import('./pages/SystemHealthPage').then(m => ({ default: m.SystemHealthPage })))
```

**Step 2: Add route definitions**

After the `/organisation` route block (before the redirects section), add:

```tsx
<Route
  path="/queue"
  element={
    <ProtectedRoute>
      <MainLayout>
        <Suspense fallback={<LoadingFallback />}>
          <QueuePage />
        </Suspense>
      </MainLayout>
    </ProtectedRoute>
  }
/>

<Route
  path="/system-health"
  element={
    <ProtectedRoute>
      <MainLayout>
        <Suspense fallback={<LoadingFallback />}>
          <SystemHealthPage />
        </Suspense>
      </MainLayout>
    </ProtectedRoute>
  }
/>
```

**Step 3: Type check**

```bash
cd frontend && npm run type-check 2>&1 | grep "error TS" | wc -l
```
Expected: still 10.

**Step 4: Stage**

```bash
git add frontend/src/App.tsx
```

---

### Task 7: Frontend — Add sidebar nav entries

**Files:**
- Modify: `frontend/src/components/layout/Sidebar/Sidebar.tsx`

**Step 1: Add imports**

In the react-icons import block, add `FaList` and `FaServer`:

```typescript
// Change the existing import line to include the new icons:
import {
  FaHome,
  FaFolder,
  FaSearch,
  FaFilm,
  FaTv,
  FaFolderOpen,
  FaCog,
  FaChevronLeft,
  FaChevronRight,
  FaInfoCircle,
  FaDatabase,
  FaList,
  FaServer,
} from 'react-icons/fa'
```

**Step 2: Add nav items**

In the `navItems` array, after the `Storage` entry and before `Settings`, add:

```typescript
  { label: 'Queue', path: '/queue', icon: <FaList className="w-5 h-5" /> },
  { label: 'System Health', path: '/system-health', icon: <FaServer className="w-5 h-5" /> },
```

**Step 3: Type check**

```bash
cd frontend && npm run type-check 2>&1 | grep "error TS" | wc -l
```
Expected: still 10.

**Step 4: Stage**

```bash
git add frontend/src/components/layout/Sidebar/Sidebar.tsx
```

---

### Task 8: Frontend — Wire dashboard widgets

**Files:**
- Modify: `frontend/src/components/dashboard/Dashboard/Dashboard.tsx`

**Context:** `navigate` is already imported and used in this file. `StatCard` already accepts `onClick` (used on "Total Files" and "Indexed Files"). The health activity object is built inline when populating `activities`.

**Step 1: Add `onClick` to the "Pending Tasks" stat card**

Find the `StatCard` with `title="Pending Tasks"` and add `onClick`:

```tsx
// OLD:
<StatCard
  title="Pending Tasks"
  value={stats.pendingTasks}
  variant="warning"
  icon={...}
/>

// NEW:
<StatCard
  title="Pending Tasks"
  value={stats.pendingTasks}
  variant="warning"
  onClick={() => navigate('/queue')}
  icon={...}
/>
```

**Step 2: Add `onClick` to the "Completed Tasks" stat card**

```tsx
// OLD:
<StatCard
  title="Completed Tasks"
  value={stats.completedTasks}
  variant="default"
  icon={...}
/>

// NEW:
<StatCard
  title="Completed Tasks"
  value={stats.completedTasks}
  variant="default"
  onClick={() => navigate('/queue')}
  icon={...}
/>
```

**Step 3: Add `onClick` to the Health Check activity item**

Find the block that pushes the health activity and add `onClick`:

```typescript
// OLD:
activities.push({
  id: 'health',
  type: 'update',
  title: 'Health Check',
  description: `Overall status: ${health.status}`,
  timestamp: health.timestamp || new Date().toISOString(),
  status: health.status === 'healthy' ? 'success' : 'error',
})

// NEW:
activities.push({
  id: 'health',
  type: 'update',
  title: 'Health Check',
  description: `Overall status: ${health.status}`,
  timestamp: health.timestamp || new Date().toISOString(),
  status: health.status === 'healthy' ? 'success' : 'error',
  onClick: () => navigate('/system-health'),
})
```

**Step 4: Type check**

```bash
cd frontend && npm run type-check 2>&1 | grep "error TS" | wc -l
```
Expected: still 10.

**Step 5: Stage**

```bash
git add frontend/src/components/dashboard/Dashboard/Dashboard.tsx
```

---

### Task 9: Commit everything

**Step 1: Run backend tests**

```bash
pytest tests/test_health_logs.py -v
```
Expected: 5 passed.

**Step 2: Final type check**

```bash
cd frontend && npm run type-check 2>&1 | grep "error TS" | wc -l
```
Expected: 10 (no new errors introduced).

**Step 3: Commit**

```bash
git add -p  # review any unstaged changes
git commit -m "feat(health,queue): add /queue and /system-health drill-down pages

- Backend: add GET /health/logs endpoint returning last N log lines per component
- Frontend: add QueuePage wrapping QueuePanel with working view-details expand
- Frontend: add SystemHealthPage with per-component status cards and 2s log tail polling
- Frontend: register /queue and /system-health routes in App.tsx
- Frontend: add Queue and System Health entries to sidebar nav
- Frontend: wire dashboard Pending/Completed Tasks stat cards → /queue
- Frontend: wire Health Check activity item → /system-health"
```
