# chore: Security Fixes

## 1. Harden `explain_query` against SQL injection

**File:** `app/application/db_optimization/service.py:341`

**Problem:** `QueryExecutionPlanAnalyzer.explain_query()` interpolates the `query` argument directly into a `text()` call via an f-string:

```python
result = db.execute(text(f"EXPLAIN {query}")).fetchall()
```

Currently only called with internally-generated query strings, but the function signature accepts any `str` — a future caller passing user input would be directly exploitable.

**Fix:** Restrict the function to only accept queries generated internally. Add a module-level allowlist or replace with a private helper that is not part of the public API. Since `EXPLAIN` cannot use bind parameters for the query body, the safest approach is to ensure the `query` argument can only come from SQLAlchemy's own query compilation (i.e. pass a compiled query string from the ORM, never a raw user string).

**Suggested implementation:**
- Accept a `ClauseElement` (SQLAlchemy query object) instead of a raw `str`
- Compile it to a string internally using `query.compile(dialect=...)` before passing to `EXPLAIN`
- This makes it impossible for a caller to pass arbitrary SQL

**Test:** Add a unit test confirming the function rejects (or cannot be called with) a raw string containing SQL injection payloads.

---

## 2. Codacy / linter: flag any new `text(f"...")` usage

**Problem:** The pattern `text(f"...{variable}...")` is a footgun. Codacy already flags it; enforce it at the project level.

**Fix:** Add a `flake8` custom rule or `bandit` check to the CI pipeline that fails on `text(f"` patterns. Document the approved exceptions (the hardcoded migration in `init_db.py`) with `# noqa` comments explaining why they are safe.

**Files to update:**
- `.flake8` or `pyproject.toml` — add `bandit` to linting pipeline
- `app/core/init_db.py:111` — add `# noqa: S608` with comment explaining the values are hardcoded

---

## 3. Audit all future `text()` usages

**Rule to document in CLAUDE.md / contributor docs:**

| Situation | Correct approach |
|---|---|
| Simple query with variable | Use ORM `select()` / `filter()` |
| Raw SQL with variable parts | `text("... :param").bindparams(param=value)` |
| DDL with hardcoded identifiers | `text(f"ALTER TABLE {hardcoded_name}...")` — annotate with `# noqa` + comment |
| DDL with user-supplied identifiers | **Not allowed** — use ORM migrations only |
