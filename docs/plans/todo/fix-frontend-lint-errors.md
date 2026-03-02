# Fix Frontend Lint Errors

The ESLint config was broken (referencing non-existent plugin rules) so these errors were never surfaced. Now that the config is fixed, the following pre-existing errors need to be resolved.

## Summary

| Category | Count | Rule |
|----------|-------|------|
| Explicit `any` types | ~150 | `@typescript-eslint/no-explicit-any` |
| Unused variables/imports | ~60 | `@typescript-eslint/no-unused-vars` |
| React Compiler violations | ~7 | `react-hooks/incompatible-library` |
| Fast refresh violations | ~5 | `react-refresh/only-export-components` |
| Misc (`no-case-declarations`, `no-control-regex`, `no-unused-expressions`) | ~6 | various |

## Approach

### 1. Unused variables/imports (~60 errors) — mechanical
Remove or prefix with `_` for intentionally unused parameters. Mostly dead imports.

Run to find all affected files:
```bash
cd frontend && npm run lint 2>&1 | grep "no-unused-vars" | awk -F: '{print $1}' | sort -u
```

### 2. Explicit `any` types (~150 errors) — needs typing
Replace `any` with proper types. Use the generated API schema types from `src/types/api-schema.ts` where applicable.

Run to find all affected files:
```bash
cd frontend && npm run lint 2>&1 | grep "no-explicit-any" | awk -F: '{print $1}' | sort -u
```

### 3. React Compiler violations (~7 errors)
`react-hooks/incompatible-library` fires on `react-hook-form`'s `watch()` return value being used in memoized contexts. Either:
- Restructure the affected components to not memoize the watched value
- Or suppress with `// eslint-disable-next-line react-hooks/incompatible-library` where unavoidable

### 4. Fast refresh violations (~5 errors)
`react-refresh/only-export-components` — move non-component exports (constants, types) to separate files.

### 5. Misc
- `no-case-declarations`: Add `{}` block scope inside `case` branches
- `no-control-regex`: Review regexes containing control characters (`\x00`, `\x1f`)
- `no-unused-expressions`: Wrap standalone expressions in a function call or remove them

## Verification

After fixes:
```bash
cd frontend && npm run lint
# Should exit 0 with zero errors
```
