# Replace react-virtual with @tanstack/react-virtual

## Problem

`react-virtual@2.10.4` declares a peer dependency of `react@"^16.6.3 || ^17.0.0"` but the
project uses React 19. This forces `npm ci --legacy-peer-deps` in the frontend Dockerfile to
suppress the conflict. Without the flag, Docker builds fail with an `ERESOLVE` error.

## Goal

Replace `react-virtual` with `@tanstack/react-virtual` (the maintained successor, v3+), which
fully supports React 19 and is the recommended upgrade path from the same authors.

## What to change

### 1. Update dependencies

```bash
cd frontend
npm uninstall react-virtual
npm install @tanstack/react-virtual
```

### 2. Update imports

Search for all usages:

```bash
grep -r "react-virtual" frontend/src --include="*.tsx" --include="*.ts" -l
```

Change imports from:

```ts
import { useVirtual } from 'react-virtual';
```

to:

```ts
import { useVirtualizer } from '@tanstack/react-virtual';
```

### 3. Update usage (API changed)

`useVirtual` → `useVirtualizer`. The new API differs slightly:

| v2 (`react-virtual`)          | v3 (`@tanstack/react-virtual`)         |
|-------------------------------|----------------------------------------|
| `useVirtual({ size, parentRef, estimateSize })` | `useVirtualizer({ count, getScrollElement, estimateSize })` |
| `virtualItems`                | `getVirtualItems()`                    |
| `item.measureRef`             | `virtualizer.measureElement`           |
| `totalSize`                   | `getTotalSize()`                       |

See the [migration guide](https://tanstack.com/virtual/v3/docs/migration/migrate-from-react-virtual)
for full details.

### 4. Restore strict npm ci in Dockerfile

Once the replacement is complete and `react-virtual` is no longer in `package.json`, revert the
Dockerfile back to plain `npm ci`:

```dockerfile
# frontend/Dockerfile line 13
RUN npm ci   # remove --legacy-peer-deps
```

## Testing

- Run `npm run build` locally after the swap to confirm no TypeScript errors
- Run `npm test` to ensure virtualised list behaviour is unchanged
- Run `docker compose build frontend` to confirm the image builds without `--legacy-peer-deps`
