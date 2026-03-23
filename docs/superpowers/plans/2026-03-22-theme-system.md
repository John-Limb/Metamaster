# Theme System Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace hardcoded Tailwind colour classes with semantic CSS custom properties and ship Matrix + Synthwave as user-selectable themes alongside the existing default light/dark theme.

**Architecture:** CSS custom properties scoped to `[data-theme="..."]` selectors on `<html>` define all structural colours. Tailwind config wires `primary-*` and new semantic tokens (`bg-page`, `text-body`, etc.) to these variables via the `@config` compatibility bridge. `ThemeContext` gains a `colourTheme` field alongside the existing `theme`/`resolvedTheme` API. ~46 component files have hardcoded `slate-*`/`indigo-*` classes replaced with semantic tokens.

**Tech Stack:** React 18, TypeScript, Tailwind CSS v4.1 (`@config` bridge), CSS custom properties, Zustand, localStorage

**Spec:** `docs/superpowers/specs/2026-03-22-theme-system-design.md`

**Prerequisite:** None. Implement before the Plex UI deduplication plan (AlertMessage will consume CSS variable tokens defined here).

**Note on commits:** Per project policy (`CLAUDE.md`), always stage with `git add` but do NOT commit — the user commits manually.

---

## Chunk 1: Tailwind Config + CSS Variables

### Task 1: Update `tailwind.config.js`

**Files:**
- Modify: `frontend/tailwind.config.js`

- [ ] **Step 1: Wire `primary` scale to CSS variables**

Replace the hardcoded hex `primary` scale (lines 11–22) with CSS variable references:

```js
primary: {
  50:  'var(--accent-50)',
  100: 'var(--accent-100)',
  200: 'var(--accent-200)',
  300: 'var(--accent-300)',
  400: 'var(--accent-400)',
  500: 'var(--accent-500)',
  600: 'var(--accent-600)',
  700: 'var(--accent-700)',
  800: 'var(--accent-800)',
  900: 'var(--accent-900)',
},
```

- [ ] **Step 2: Add semantic colour tokens**

Add these entries alongside `primary` inside `theme.extend.colors`:

```js
// Semantic layout tokens
page:    'var(--bg-page)',
card:    'var(--bg-card)',
popover: 'var(--bg-popover)',
subtle:  'var(--bg-subtle)',
body:    'var(--text-body)',
dim:     'var(--text-dim)',
hint:    'var(--text-hint)',
edge:    'var(--border-edge)',
rule:    'var(--border-rule)',
```

- [ ] **Step 3: Update single-value state tokens to CSS variables**

Replace the four single-value state colours:

```js
success: 'var(--success)',
warning: 'var(--warning)',
danger:  'var(--danger)',
info:    'var(--info)',
```

- [ ] **Step 4: Verify build has no errors**

```bash
cd frontend && npm run build 2>&1 | grep -E "^✓|error|Error" | head -20
```

Expected: Build line like `✓ built in Xs`. If there are errors, check for syntax issues in the config.

- [ ] **Step 5: Stage**

```bash
git add frontend/tailwind.config.js
```

---

### Task 2: Add CSS variable theme blocks to `index.css`

**Files:**
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Update `body` base colour declarations**

In `frontend/src/index.css`, find the inner `body` block inside `@layer base` (around line 26) that has `color: var(--color-text)` and `background-color: var(--color-background)`. Replace only those two lines:

```css
  color: var(--text-body);
  background-color: var(--bg-page);
```

Leave `font-size`, `line-height`, and all other properties unchanged.

- [ ] **Step 2: Append per-theme CSS variable blocks**

Add the following at the very bottom of `frontend/src/index.css`:

```css
/* ─────────────────────────────────────────────────────────────────────────
   Theme definitions
   ThemeContext sets both data-theme and the dark/light class on <html>.
   ───────────────────────────────────────────────────────────────────────── */

[data-theme="default"].light {
  --bg-page:        #f8fafc;
  --bg-card:        #ffffff;
  --bg-popover:     #ffffff;
  --bg-subtle:      #f1f5f9;
  --border-edge:    #e2e8f0;
  --border-rule:    #f1f5f9;
  --text-body:      #0f172a;
  --text-dim:       #475569;
  --text-hint:      #94a3b8;
  --accent-50:  #f0f4ff;  --accent-100: #e0e7ff;  --accent-200: #c7d2fe;
  --accent-300: #a5b4fc;  --accent-400: #818cf8;  --accent-500: #6366f1;
  --accent-600: #4f46e5;  --accent-700: #4338ca;  --accent-800: #3730a3;
  --accent-900: #312e81;
  --success: #10b981;  --warning: #f59e0b;  --danger: #ef4444;  --info: #3b82f6;
  --danger-bg: #fef2f2;  --danger-border: #fecaca;  --danger-text: #b91c1c;
  --success-bg: #f0fdf4;  --success-border: #bbf7d0;  --success-text: #15803d;
}

[data-theme="default"].dark {
  --bg-page:        #0f172a;
  --bg-card:        #1e293b;
  --bg-popover:     #1e293b;
  --bg-subtle:      #334155;
  --border-edge:    #334155;
  --border-rule:    #1e293b;
  --text-body:      #f1f5f9;
  --text-dim:       #94a3b8;
  --text-hint:      #64748b;
  --accent-50:  #f0f4ff;  --accent-100: #e0e7ff;  --accent-200: #c7d2fe;
  --accent-300: #a5b4fc;  --accent-400: #818cf8;  --accent-500: #6366f1;
  --accent-600: #4f46e5;  --accent-700: #4338ca;  --accent-800: #3730a3;
  --accent-900: #312e81;
  --success: #10b981;  --warning: #f59e0b;  --danger: #ef4444;  --info: #3b82f6;
  --danger-bg: #1f0000;  --danger-border: #7f1d1d;  --danger-text: #fca5a5;
  --success-bg: #052e16;  --success-border: #14532d;  --success-text: #86efac;
}

[data-theme="matrix"] {
  --bg-page:        #000000;
  --bg-card:        #0a0f0a;
  --bg-popover:     #0d150d;
  --bg-subtle:      #0a1a0a;
  --border-edge:    #0a2a0a;
  --border-rule:    #051005;
  --text-body:      #00ff41;
  --text-dim:       #00b835;
  --text-hint:      #006620;
  --accent-50:  #001a00;  --accent-100: #002a00;  --accent-200: #003a00;
  --accent-300: #005a00;  --accent-400: #008020;  --accent-500: #00b835;
  --accent-600: #00c83b;  --accent-700: #00ff41;  --accent-800: #33ff66;
  --accent-900: #66ffaa;
  --success: #00c83b;  --warning: #ffcc00;  --danger: #ff2244;  --info: #00ccff;
  --danger-bg: #1a0000;  --danger-border: #440011;  --danger-text: #ff6688;
  --success-bg: #001a00;  --success-border: #003300;  --success-text: #00ff41;
}

[data-theme="synthwave"] {
  --bg-page:        #0d0117;
  --bg-card:        #120220;
  --bg-popover:     #180328;
  --bg-subtle:      #1f0535;
  --border-edge:    #1f0535;
  --border-rule:    #150122;
  --text-body:      #e8d5ff;
  --text-dim:       #c084fc;
  --text-hint:      #7c3aed;
  --accent-50:  #1a0030;  --accent-100: #250040;  --accent-200: #3b0060;
  --accent-300: #5b00a0;  --accent-400: #7b2fff;  --accent-500: #a855f7;
  --accent-600: #c84dff;  --accent-700: #ff2d78;  --accent-800: #ff6faa;
  --accent-900: #ffb3d0;
  --success: #22d3ee;  --warning: #fbbf24;  --danger: #ff2d78;  --info: #38bdf8;
  --danger-bg: #1f0020;  --danger-border: #3f0040;  --danger-text: #ff80b0;
  --success-bg: #001520;  --success-border: #003040;  --success-text: #22d3ee;
}
```

- [ ] **Step 3: Stage**

```bash
git add frontend/src/index.css
```

---

## Chunk 2: ThemeContext

### Task 3: Extend ThemeContext

**Files:**
- Modify: `frontend/src/context/ThemeContext.tsx`

- [ ] **Step 1: Add `ColourTheme` type and extend the context interface**

Add below the existing `type Theme = ...` line (line 3):

```ts
type ColourTheme = 'default' | 'matrix' | 'synthwave'
```

Extend `ThemeContextType` to add the new fields alongside the existing ones:

```ts
interface ThemeContextType {
  theme: Theme
  setTheme: (theme: Theme) => void
  resolvedTheme: 'light' | 'dark'
  colourTheme: ColourTheme
  setColourTheme: (t: ColourTheme) => void
}
```

- [ ] **Step 2: Add `colourTheme` state inside `ThemeProvider`**

Inside `ThemeProvider`, after the existing `theme` useState, add:

```ts
const [colourTheme, setColourThemeState] = useState<ColourTheme>(() => {
  if (typeof window !== 'undefined') {
    const saved = (localStorage.getItem('colour-theme') as ColourTheme) || 'default'
    // Set data-theme synchronously to avoid flash of wrong theme on reload
    document.documentElement.dataset.theme = saved
    return saved
  }
  return 'default'
})

const setColourTheme = (t: ColourTheme) => {
  setColourThemeState(t)
  localStorage.setItem('colour-theme', t)
}
```

- [ ] **Step 3: Update `resolvedTheme` useMemo to account for colour themes**

Replace the existing `resolvedTheme` useMemo:

```ts
const resolvedTheme = useMemo<'light' | 'dark'>(() => {
  if (colourTheme !== 'default') return 'dark'
  if (theme === 'system') return systemIsDark ? 'dark' : 'light'
  return theme
}, [theme, systemIsDark, colourTheme])
```

- [ ] **Step 4: Update the main `useEffect` to set `data-theme`**

Replace the existing theme-application `useEffect`:

```ts
useEffect(() => {
  const root = window.document.documentElement
  root.classList.remove('light', 'dark')
  root.classList.add(resolvedTheme)
  root.dataset.theme = colourTheme
  localStorage.setItem('theme', theme)
}, [theme, resolvedTheme, colourTheme])
```

- [ ] **Step 5: Gate the OS media-query listener on `colourTheme === 'default'`**

Replace the existing system-theme `useEffect`:

```ts
useEffect(() => {
  if (theme !== 'system' || colourTheme !== 'default') return
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  const handleChange = () => setSystemIsDark(mediaQuery.matches)
  mediaQuery.addEventListener('change', handleChange)
  return () => mediaQuery.removeEventListener('change', handleChange)
}, [theme, colourTheme])
```

- [ ] **Step 6: Expose new fields in the Provider value**

```tsx
<ThemeContext.Provider value={{ theme, setTheme, resolvedTheme, colourTheme, setColourTheme }}>
```

- [ ] **Step 7: TypeScript check**

```bash
cd frontend && npm run type-check 2>&1 | head -30
```

Expected: 0 errors. Fix any type errors before proceeding.

- [ ] **Step 8: Stage**

```bash
git add frontend/src/context/ThemeContext.tsx
```

---

## Chunk 3: Settings UI + Header

### Task 4: Add colour theme swatches to SettingsPage

**Files:**
- Modify: `frontend/src/pages/SettingsPage.tsx`

- [ ] **Step 1: Update the `useTheme` destructure**

Find the existing line (around line 42):
```ts
const { setTheme: applyTheme } = useTheme()
```

Replace with:
```ts
const { theme: contextTheme, setTheme: applyTheme, colourTheme, setColourTheme } = useTheme()
```

Note: `theme` is aliased to `contextTheme` to avoid clashing with the local `theme` state at line 49.

- [ ] **Step 2: Verify `RadioInput` is already imported**

Check that `RadioInput` is in the existing import at line 4:
```ts
import { CheckboxInput, RadioInput } from '@/components/common'
```

If it is not present, add `RadioInput` to that import. (It is present in the current file.)

- [ ] **Step 3: Add `ColourThemeSwatch` helper component**

Add this above the `SettingsPage` component definition:

```tsx
interface SwatchProps {
  label: string
  chips: [string, string, string]
  active: boolean
  onClick: () => void
}

function ColourThemeSwatch({ label, chips, active, onClick }: SwatchProps) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-3 px-3 py-2 rounded-lg border-2 transition-colors text-left w-full ${
        active
          ? 'border-primary-600 bg-primary-50 dark:bg-primary-900/20'
          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
      }`}
    >
      <div className="flex gap-1">
        {chips.map((c, i) => (
          <span key={i} className="w-4 h-4 rounded-full border border-white/20" style={{ background: c }} />
        ))}
      </div>
      <span className="text-sm font-medium text-gray-800 dark:text-gray-200">{label}</span>
      {active && <span className="ml-auto text-xs text-primary-600 font-semibold">Active</span>}
    </button>
  )
}
```

- [ ] **Step 4: Replace the Theme section children**

Find the `{/* Theme Settings */}` `SettingsSection` block (around line 190). Replace only the children (`<div className="space-y-3">` through its closing tag, but keep the outer `SettingsSection` wrapper). New children:

```tsx
<div className="space-y-4">
  {/* Colour theme */}
  <div className="space-y-2">
    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Colour Theme</p>
    <div className="space-y-2">
      <ColourThemeSwatch
        label="Default"
        chips={['#1e293b', '#4f46e5', '#f1f5f9']}
        active={colourTheme === 'default'}
        onClick={() => setColourTheme('default')}
      />
      <ColourThemeSwatch
        label="Matrix"
        chips={['#000000', '#00ff41', '#00b835']}
        active={colourTheme === 'matrix'}
        onClick={() => setColourTheme('matrix')}
      />
      <ColourThemeSwatch
        label="Synthwave"
        chips={['#0d0117', '#c84dff', '#e8d5ff']}
        active={colourTheme === 'synthwave'}
        onClick={() => setColourTheme('synthwave')}
      />
    </div>
  </div>

  {/* Light / dark mode — only relevant for Default theme */}
  <div className={colourTheme !== 'default' ? 'opacity-40 pointer-events-none select-none' : ''}>
    <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
      Light / Dark Mode
      {colourTheme !== 'default' && (
        <span className="ml-2 text-xs font-normal text-gray-400">(not available for this theme)</span>
      )}
    </p>
    <div className="space-y-2">
      {(['light', 'dark', 'auto'] as const).map((option) => (
        <label key={option} className="flex items-center gap-2 cursor-pointer">
          <RadioInput
            name="theme"
            value={option}
            checked={theme === option}
            onChange={(val) => setTheme(val as 'light' | 'dark' | 'auto')}
          />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">{option}</span>
        </label>
      ))}
    </div>
  </div>
</div>
```

Note: `theme` and `setTheme` in the JSX above refer to the *local state variable at line 49* (initialised from `userSettings.theme`), not to `contextTheme`. This is the existing save-on-confirm pattern: local state is updated via radio buttons, then flushed to the context only inside `handleSaveSettings` via `applyTheme`. Do **not** replace `theme` / `setTheme` here with `contextTheme` / `applyTheme`.

Note on `colourTheme` persistence: `setColourTheme` writes to `localStorage` immediately on click (in Task 3's wrapper). The Zustand settings store (`updateUserSettings`) does **not** need to be updated — `colourTheme` is intentionally a frontend-only preference managed via `ThemeContext` + `localStorage`, not a backend-synced setting. No change to `handleSaveSettings` is required.

- [ ] **Step 5: TypeScript check**

```bash
cd frontend && npm run type-check 2>&1 | head -30
```

Expected: 0 errors.

- [ ] **Step 6: Stage**

```bash
git add frontend/src/pages/SettingsPage.tsx
```

---

### Task 5: Hide light/dark toggle in Header for non-default themes

**Files:**
- Modify: `frontend/src/components/layout/Header/Header.tsx`

- [ ] **Step 1: Import `colourTheme` from `useTheme`**

Update the existing destructure (line ~32):

```ts
const { setTheme, resolvedTheme, colourTheme } = useTheme()
```

- [ ] **Step 2: Wrap the toggle button in a conditional**

Find the theme toggle `<button>` block (around line 279) and wrap it:

```tsx
{colourTheme === 'default' && (
  <button
    onClick={toggleTheme}
    className="p-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-indigo-500"
    aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
  >
    {resolvedTheme === 'dark' ? (
      <FaSun className="w-5 h-5" />
    ) : (
      <FaMoon className="w-5 h-5" />
    )}
  </button>
)}
```

- [ ] **Step 3: TypeScript check and lint**

```bash
cd frontend && npm run type-check 2>&1 | head -20 && npm run lint 2>&1 | head -20
```

Expected: 0 errors, 0 new lint warnings.

- [ ] **Step 4: Stage**

```bash
git add frontend/src/components/layout/Header/Header.tsx
```

---

## Chunk 4: Colour Class Migration

> **Overview:** ~46 files need hardcoded `slate-*` and `indigo-*` colour classes replaced with semantic tokens. The migration runs in four batches by area. After each batch: type-check, lint, stage.
>
> **Replacement map** (paired `dark:` variants collapse into a single token):
>
> | From | To |
> |---|---|
> | `bg-white dark:bg-slate-800` or `bg-white dark:bg-gray-800` | `bg-card` |
> | `bg-slate-900` / `dark:bg-slate-900` | `bg-page` |
> | `bg-slate-800` / `dark:bg-slate-800` | `bg-card` |
> | `bg-slate-700` / `dark:bg-slate-700` | `bg-popover` |
> | `bg-slate-50 dark:bg-slate-700/50` / `dark:bg-slate-700/50` / `bg-slate-50` | `bg-subtle` |
> | `text-slate-900 dark:text-white` or `text-slate-800 dark:text-slate-200` | `text-body` |
> | `text-slate-700 dark:text-slate-300` or `text-slate-600 dark:text-slate-400` | `text-dim` |
> | `text-slate-500 dark:text-slate-400` or `text-slate-500` or `text-slate-400` | `text-hint` |
> | `border-slate-200 dark:border-slate-700` | `border-edge` |
> | `border-slate-100 dark:border-slate-700` | `border-rule` |
> | `divide-slate-100 dark:divide-slate-700` | `divide-rule` |
> | `bg-indigo-*` | `bg-primary-*` |
> | `text-indigo-*` | `text-primary-*` |
> | `border-indigo-*` | `border-primary-*` |
>
> **Important:** `dark:text-white` sed rule is intentionally omitted — it appears on coloured badge/button backgrounds (e.g. `bg-red-600 text-white`) and must be handled manually. Review every occurrence in the diff.

### Task 6: Migrate layout + auth components

**Files (batch 1):**
```
frontend/src/components/layout/Header/Header.tsx
frontend/src/components/layout/MainLayout/MainLayout.tsx
frontend/src/components/layout/Footer.tsx
frontend/src/components/layout/NotificationDropdown/NotificationDropdown.tsx
frontend/src/components/layout/UserMenu/UserMenu.tsx
frontend/src/components/auth/LoginForm.tsx
frontend/src/components/auth/ChangePasswordForm.tsx
frontend/src/components/auth/ProtectedRoute.tsx
```

- [ ] **Step 1: Run sed replacements on batch 1 files**

```bash
cd frontend/src
FILES=(
  "components/layout/Header/Header.tsx"
  "components/layout/MainLayout/MainLayout.tsx"
  "components/layout/Footer.tsx"
  "components/layout/NotificationDropdown/NotificationDropdown.tsx"
  "components/layout/UserMenu/UserMenu.tsx"
  "components/auth/LoginForm.tsx"
  "components/auth/ChangePasswordForm.tsx"
  "components/auth/ProtectedRoute.tsx"
)

for f in "${FILES[@]}"; do
  sed -i '' \
    -e 's/bg-white dark:bg-slate-800/bg-card/g' \
    -e 's/bg-white dark:bg-gray-800/bg-card/g' \
    -e 's/dark:bg-slate-900\b/bg-page/g' \
    -e 's/bg-slate-900\b/bg-page/g' \
    -e 's/dark:bg-slate-800\b/bg-card/g' \
    -e 's/bg-slate-800\b/bg-card/g' \
    -e 's/dark:bg-slate-700\b/bg-popover/g' \
    -e 's/bg-slate-700\b/bg-popover/g' \
    -e 's/bg-slate-50 dark:bg-slate-700\/50/bg-subtle/g' \
    -e 's/dark:bg-slate-700\/50/bg-subtle/g' \
    -e 's/bg-slate-50\b/bg-subtle/g' \
    -e 's/text-slate-900 dark:text-white/text-body/g' \
    -e 's/text-slate-800 dark:text-slate-200/text-body/g' \
    -e 's/text-slate-700 dark:text-slate-300/text-dim/g' \
    -e 's/text-slate-600 dark:text-slate-400/text-dim/g' \
    -e 's/dark:text-slate-300\b/text-dim/g' \
    -e 's/text-slate-500 dark:text-slate-400/text-hint/g' \
    -e 's/text-slate-500\b/text-hint/g' \
    -e 's/text-slate-400\b/text-hint/g' \
    -e 's/border-slate-200 dark:border-slate-700/border-edge/g' \
    -e 's/border-slate-100 dark:border-slate-700/border-rule/g' \
    -e 's/divide-slate-100 dark:divide-slate-700/divide-rule/g' \
    -e 's/dark:border-slate-700\b/border-edge/g' \
    -e 's/border-slate-200\b/border-edge/g' \
    -e 's/bg-indigo-/bg-primary-/g' \
    -e 's/text-indigo-/text-primary-/g' \
    -e 's/border-indigo-/border-primary-/g' \
    "$f"
done
```

- [ ] **Step 2: Review diffs for contextual issues**

```bash
git diff frontend/src/components/layout/ frontend/src/components/auth/
```

Look for: any `dark:` prefix remaining on a replaced token (double-replacement), any `text-white` that was on a coloured badge (should remain `text-white`), any `bg-card-card` (accidental double hit).

Fix any issues manually.

- [ ] **Step 3: Type-check and lint**

```bash
cd frontend && npm run type-check 2>&1 | head -20 && npm run lint 2>&1 | head -20
```

Expected: 0 errors.

- [ ] **Step 4: Stage**

```bash
git add frontend/src/components/layout/ frontend/src/components/auth/
```

---

### Task 7: Migrate common components

**Files (batch 2):**
```
frontend/src/components/common/
```

- [ ] **Step 1: Run sed replacements on common components**

Note: `ConfirmDialog.tsx` uses `gray-*` (not `slate-*`) — the sed also handles those.

```bash
cd frontend/src
find components/common -name "*.tsx" | while read f; do
  sed -i '' \
    -e 's/bg-white dark:bg-gray-800/bg-card/g' \
    -e 's/bg-white dark:bg-slate-800/bg-card/g' \
    -e 's/bg-gray-800\b/bg-card/g' \
    -e 's/dark:bg-gray-800\b/bg-card/g' \
    -e 's/bg-gray-50 dark:bg-gray-700\/50/bg-subtle/g' \
    -e 's/bg-gray-100 dark:bg-gray-700/bg-subtle/g' \
    -e 's/dark:bg-slate-900\b/bg-page/g' \
    -e 's/bg-slate-900\b/bg-page/g' \
    -e 's/dark:bg-slate-800\b/bg-card/g' \
    -e 's/bg-slate-800\b/bg-card/g' \
    -e 's/text-gray-900 dark:text-white/text-body/g' \
    -e 's/text-slate-900 dark:text-white/text-body/g' \
    -e 's/text-gray-700 dark:text-gray-300/text-dim/g' \
    -e 's/text-gray-600 dark:text-gray-400/text-dim/g' \
    -e 's/text-gray-400\b/text-hint/g' \
    -e 's/text-slate-500 dark:text-slate-400/text-hint/g' \
    -e 's/text-slate-500\b/text-hint/g' \
    -e 's/text-slate-400\b/text-hint/g' \
    -e 's/border-gray-200 dark:border-gray-700/border-edge/g' \
    -e 's/border-slate-200 dark:border-slate-700/border-edge/g' \
    -e 's/border-slate-100 dark:border-slate-700/border-rule/g' \
    -e 's/divide-slate-100 dark:divide-slate-700/divide-rule/g' \
    -e 's/dark:border-slate-700\b/border-edge/g' \
    -e 's/bg-indigo-/bg-primary-/g' \
    -e 's/text-indigo-/text-primary-/g' \
    -e 's/border-indigo-/border-primary-/g' \
    "$f"
done
```

- [ ] **Step 2: Review diffs**

```bash
git diff frontend/src/components/common/
```

Fix any double-replacements or contextual issues manually.

- [ ] **Step 3: Type-check and lint**

```bash
cd frontend && npm run type-check 2>&1 | head -20 && npm run lint 2>&1 | head -20
```

- [ ] **Step 4: Stage**

```bash
git add frontend/src/components/common/
```

---

### Task 8: Migrate feature components

**Files (batch 3):**

```bash
grep -rl "bg-slate-\|text-slate-\|border-slate-\|bg-indigo-\|text-indigo-\|border-indigo-\|divide-slate-" \
  frontend/src/components/features/ \
  frontend/src/components/dashboard/ \
  frontend/src/components/configuration/ \
  frontend/src/components/file/ \
  frontend/src/components/queue/ \
  frontend/src/components/search/ \
  frontend/src/components/settings/ \
  --include="*.tsx"
```

- [ ] **Step 1: Run sed replacements on all matched files**

```bash
cd frontend/src
grep -rl "bg-slate-\|text-slate-\|border-slate-\|bg-indigo-\|text-indigo-\|border-indigo-\|divide-slate-" \
  components/features/ components/dashboard/ components/configuration/ \
  components/file/ components/queue/ components/search/ components/settings/ \
  --include="*.tsx" | while read f; do
  sed -i '' \
    -e 's/bg-white dark:bg-slate-800/bg-card/g' \
    -e 's/bg-white dark:bg-gray-800/bg-card/g' \
    -e 's/dark:bg-slate-900\b/bg-page/g' \
    -e 's/bg-slate-900\b/bg-page/g' \
    -e 's/dark:bg-slate-800\b/bg-card/g' \
    -e 's/bg-slate-800\b/bg-card/g' \
    -e 's/dark:bg-slate-700\b/bg-popover/g' \
    -e 's/bg-slate-700\b/bg-popover/g' \
    -e 's/bg-slate-50 dark:bg-slate-700\/50/bg-subtle/g' \
    -e 's/dark:bg-slate-700\/50/bg-subtle/g' \
    -e 's/bg-slate-50\b/bg-subtle/g' \
    -e 's/text-slate-900 dark:text-white/text-body/g' \
    -e 's/text-slate-800 dark:text-slate-200/text-body/g' \
    -e 's/text-slate-700 dark:text-slate-300/text-dim/g' \
    -e 's/text-slate-600 dark:text-slate-400/text-dim/g' \
    -e 's/text-slate-500 dark:text-slate-400/text-hint/g' \
    -e 's/text-slate-500\b/text-hint/g' \
    -e 's/text-slate-400\b/text-hint/g' \
    -e 's/border-slate-200 dark:border-slate-700/border-edge/g' \
    -e 's/border-slate-100 dark:border-slate-700/border-rule/g' \
    -e 's/divide-slate-100 dark:divide-slate-700/divide-rule/g' \
    -e 's/dark:border-slate-700\b/border-edge/g' \
    -e 's/border-slate-200\b/border-edge/g' \
    -e 's/bg-indigo-/bg-primary-/g' \
    -e 's/text-indigo-/text-primary-/g' \
    -e 's/border-indigo-/border-primary-/g' \
    "$f"
done
```

- [ ] **Step 2: Review diffs**

```bash
git diff frontend/src/components/features/ \
         frontend/src/components/dashboard/ \
         frontend/src/components/configuration/ \
         frontend/src/components/file/ \
         frontend/src/components/queue/ \
         frontend/src/components/search/ \
         frontend/src/components/settings/
```

- [ ] **Step 3: Type-check and lint**

```bash
cd frontend && npm run type-check 2>&1 | head -20 && npm run lint 2>&1 | head -20
```

- [ ] **Step 4: Stage**

```bash
git add frontend/src/components/features/ \
        frontend/src/components/dashboard/ \
        frontend/src/components/configuration/ \
        frontend/src/components/file/ \
        frontend/src/components/queue/ \
        frontend/src/components/search/ \
        frontend/src/components/settings/
```

---

### Task 9: Migrate pages

- [ ] **Step 1: Run sed replacements on all pages**

```bash
cd frontend/src
find pages/ -name "*.tsx" | while read f; do
  sed -i '' \
    -e 's/bg-white dark:bg-slate-800/bg-card/g' \
    -e 's/bg-white dark:bg-gray-800/bg-card/g' \
    -e 's/dark:bg-slate-900\b/bg-page/g' \
    -e 's/bg-slate-900\b/bg-page/g' \
    -e 's/dark:bg-slate-800\b/bg-card/g' \
    -e 's/bg-slate-800\b/bg-card/g' \
    -e 's/dark:bg-slate-700\b/bg-popover/g' \
    -e 's/bg-slate-700\b/bg-popover/g' \
    -e 's/bg-slate-50 dark:bg-slate-700\/50/bg-subtle/g' \
    -e 's/dark:bg-slate-700\/50/bg-subtle/g' \
    -e 's/bg-slate-50\b/bg-subtle/g' \
    -e 's/text-slate-900 dark:text-white/text-body/g' \
    -e 's/text-slate-800 dark:text-slate-200/text-body/g' \
    -e 's/text-slate-700 dark:text-slate-300/text-dim/g' \
    -e 's/text-slate-600 dark:text-slate-400/text-dim/g' \
    -e 's/text-slate-500 dark:text-slate-400/text-hint/g' \
    -e 's/text-slate-500\b/text-hint/g' \
    -e 's/text-slate-400\b/text-hint/g' \
    -e 's/border-slate-200 dark:border-slate-700/border-edge/g' \
    -e 's/border-slate-100 dark:border-slate-700/border-rule/g' \
    -e 's/divide-slate-100 dark:divide-slate-700/divide-rule/g' \
    -e 's/dark:border-slate-700\b/border-edge/g' \
    -e 's/border-slate-200\b/border-edge/g' \
    -e 's/bg-indigo-/bg-primary-/g' \
    -e 's/text-indigo-/text-primary-/g' \
    -e 's/border-indigo-/border-primary-/g' \
    "$f"
done
```

- [ ] **Step 2: Review diffs**

```bash
git diff frontend/src/pages/
```

- [ ] **Step 3: Final type-check, lint, and test**

```bash
cd frontend && npm run type-check 2>&1 | head -30 && npm run lint 2>&1 | head -30 && npm run test 2>&1 | tail -20
```

Expected: 0 type errors, 0 new lint errors, tests pass.

- [ ] **Step 4: Manual browser verification** *(human only — cannot be automated)*

```bash
cd frontend && npm run dev
```

Open http://localhost:5173 → Settings → select Matrix (black + green), Synthwave (purple + pink), Default (indigo/slate). Toggle light/dark on Default. Light/dark toggle should be hidden in Header for Matrix/Synthwave.

- [ ] **Step 5: Stage**

```bash
git add frontend/src/pages/
```

---

## Appendix: Remaining `dark:` class audit

After all batches, sweep for any remaining paired structural `dark:` classes:

```bash
grep -rn "dark:bg-slate-\|dark:text-slate-\|dark:border-slate-\|dark:bg-gray-\|dark:text-gray-\|dark:border-gray-" \
  frontend/src/ --include="*.tsx" | grep -v ".test.tsx"
```

Fix any remaining occurrences manually, then:

```bash
cd frontend && npm run type-check && npm run lint && npm run test
git add frontend/src/
```
