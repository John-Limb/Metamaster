# Theme System Design

**Date:** 2026-03-22
**Scope:** Frontend — theme infrastructure, CSS variables, Tailwind config, ThemeContext, SettingsPage

**Stack note:** The project uses **Tailwind CSS v4.1** via the `@config` compatibility bridge (`index.css` uses `@import "tailwindcss"` and `@config "../tailwind.config.js"`). All Tailwind config changes in this spec use the legacy `tailwind.config.js` path — no native v4 `@theme` blocks. The `darkMode: 'class'` key in `tailwind.config.js` is read through this compatibility bridge.

---

## Goal

Replace hardcoded Tailwind colour classes with semantic CSS custom properties, and add Matrix and Synthwave as selectable themes alongside the existing default (light/dark) theme. The user picks their theme in Settings; the selection is persisted in `localStorage` and applied immediately.

---

## Themes

Three themes, selectable by the user:

| ID | Name | Style | Dark only? |
|----|------|-------|------------|
| `default` | Default | Existing indigo/slate palette, supports light + dark mode | No |
| `matrix` | Matrix | Black background, phosphor green accents | Yes |
| `synthwave` | Synthwave | Deep purple background, hot pink + violet accents | Yes |

Matrix and Synthwave are always dark — no light variant. The existing `dark`/`light` class toggle on `<html>` is only meaningful when `colourTheme === 'default'`.

---

## Token Names

Semantic CSS custom properties use names that do **not** conflict with existing Tailwind built-ins or the current `primary` / `secondary` custom colour scales in `tailwind.config.js`.

### Backgrounds
| CSS variable | Tailwind class | Usage |
|---|---|---|
| `--bg-page` | `bg-page` | Page/app background |
| `--bg-card` | `bg-card` | Cards, panels, table containers |
| `--bg-popover` | `bg-popover` | Drawers, dropdowns, modals |
| `--bg-subtle` | `bg-subtle` | Row hover, section headers, muted fills |

### Borders
| CSS variable | Tailwind class | Usage |
|---|---|---|
| `--border-edge` | `border-edge` | Panel borders, table borders |
| `--border-rule` | `border-rule` | Dividers, row separators |

Note: `divide-rule` also works automatically — Tailwind generates `divide-*` utilities from the same colour scale as `border-*`, so no extra config is needed.

### Text
| CSS variable | Tailwind class | Usage |
|---|---|---|
| `--text-body` | `text-body` | Main body text, headings |
| `--text-dim` | `text-dim` | Labels, secondary copy |
| `--text-hint` | `text-hint` | Timestamps, hints, placeholder text |

### Accent (primary scale — replaces `indigo-*` hardcoded references)
The existing `primary-*` colour scale in `tailwind.config.js` is updated to read from CSS variables instead of hex values. Existing classes like `bg-primary-600`, `text-primary-500`, `border-primary-300` continue to work unchanged — they just pick up the themed value.

### Semantic states
The existing single-value tokens in `tailwind.config.js` (`success`, `warning`, `danger`, `info`) are updated to reference CSS variables. Each theme defines these as an all-purpose mid-range colour suitable for use as both background fill (`bg-success`) and icon/text colour (`text-success`).

| CSS variable | Tailwind token | Usage |
|---|---|---|
| `--success` | `success` | General success green |
| `--warning` | `warning` | General amber/yellow |
| `--danger` | `danger` | General red/danger |
| `--info` | `info` | General blue/cyan |

For alert banners (error/success boxes), dedicated semantic tokens are defined but do **not** replace the Tailwind tokens — they are consumed directly via CSS variables in the inline error/success `<div>` patterns across the app (e.g. in `SettingsPage`, `PlexCollectionsPage`, `Toast.tsx`) and by the `AlertMessage` component being introduced as part of the Plex UI deduplication spec:

| CSS variable | Usage |
|---|---|
| `--danger-bg` | Error banner background |
| `--danger-border` | Error banner border |
| `--danger-text` | Error banner text |
| `--success-bg` | Success banner background |
| `--success-border` | Success banner border |
| `--success-text` | Success banner text |

---

## Token Values Per Theme

### Default — Light
```css
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
  /* primary accent scale */
  --accent-50:  #f0f4ff;  --accent-100: #e0e7ff;  --accent-200: #c7d2fe;
  --accent-300: #a5b4fc;  --accent-400: #818cf8;  --accent-500: #6366f1;
  --accent-600: #4f46e5;  --accent-700: #4338ca;  --accent-800: #3730a3;
  --accent-900: #312e81;
  /* state colours */
  --success: #10b981;  --warning: #f59e0b;  --danger: #ef4444;  --info: #3b82f6;
  --danger-bg: #fef2f2;  --danger-border: #fecaca;  --danger-text: #b91c1c;
  --success-bg: #f0fdf4;  --success-border: #bbf7d0;  --success-text: #15803d;
}
```

### Default — Dark
```css
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
  /* same accent scale as light */
  --accent-50:  #f0f4ff;  --accent-100: #e0e7ff;  --accent-200: #c7d2fe;
  --accent-300: #a5b4fc;  --accent-400: #818cf8;  --accent-500: #6366f1;
  --accent-600: #4f46e5;  --accent-700: #4338ca;  --accent-800: #3730a3;
  --accent-900: #312e81;
  /* state colours */
  --success: #10b981;  --warning: #f59e0b;  --danger: #ef4444;  --info: #3b82f6;
  --danger-bg: #1f0000;  --danger-border: #7f1d1d;  --danger-text: #fca5a5;
  --success-bg: #052e16;  --success-border: #14532d;  --success-text: #86efac;
}
```

### Matrix (always dark)
```css
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
```

### Synthwave (always dark)
```css
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

---

## `index.css` Changes

`frontend/src/index.css` currently imports `design-tokens.css` which defines `--color-text` and `--color-background`. The `body` element reads these:

```css
body {
  color: var(--color-text);
  background-color: var(--color-background);
}
```

**Change:** Update the `body` base styles to use the new tokens:

```css
body {
  color: var(--text-body);
  background-color: var(--bg-page);
}
```

The `design-tokens.css` file is **not removed** — it contains typography, spacing, and other non-colour tokens that are unrelated to theming. The existing `--color-text` / `--color-background` variables within it become redundant for the body rule but are otherwise harmless and can be cleaned up separately.

The new per-theme CSS variable blocks (all four `[data-theme="..."]` rulesets) are added at the **bottom of `index.css`**, after the `@import "tailwindcss"` and `@config` lines (i.e. after line 4 in the current file). This ensures they appear after both the `design-tokens.css` `:root` variables and the Tailwind layer injection, so the per-theme blocks take precedence.

Both `data-theme` and the `dark`/`light` class are set on `document.documentElement` (`<html>`), so the compound selectors `[data-theme="default"].dark` and `[data-theme="default"].light` are valid — both attributes/classes are co-located on the same element.

---

## Tailwind Config Changes

`tailwind.config.js` — three changes:

**1. Wire `primary` scale to CSS variables** (replacing hex values):
```js
primary: {
  50:  'var(--accent-50)',  100: 'var(--accent-100)', 200: 'var(--accent-200)',
  300: 'var(--accent-300)', 400: 'var(--accent-400)', 500: 'var(--accent-500)',
  600: 'var(--accent-600)', 700: 'var(--accent-700)', 800: 'var(--accent-800)',
  900: 'var(--accent-900)',
},
```

**2. Add semantic background/text/border tokens** using names that do not collide with existing scales:
```js
// inside theme.extend.colors:
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

This generates `bg-page`, `text-body`, `border-edge`, `divide-rule`, etc. as valid Tailwind utilities. The existing `secondary-*` scale is untouched. Note: the existing `boxShadow.subtle` key is unrelated and does not conflict.

**3. Update single-value state tokens to use CSS variables:**
```js
success: 'var(--success)',  // was '#10b981'
warning: 'var(--warning)',  // was '#f59e0b'
danger:  'var(--danger)',   // was '#ef4444'
info:    'var(--info)',     // was '#3b82f6'
```

These remain single-value tokens — existing uses of `bg-success`, `text-success`, `bg-danger` etc. continue to work correctly because each theme's `--success` / `--danger` is a mid-range colour suited for both background and text use.

---

## ThemeContext Changes

**File:** `frontend/src/context/ThemeContext.tsx`

The existing `useTheme()` return shape — `{ theme, setTheme, resolvedTheme }` — is **preserved** to avoid breaking `Header.tsx` and `SettingsPage.tsx`. A new field `colourTheme` / `setColourTheme` is added alongside:

```ts
type ColourTheme = 'default' | 'matrix' | 'synthwave'

interface ThemeContextType {
  // Existing API — unchanged
  theme: 'light' | 'dark' | 'system'
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  resolvedTheme: 'light' | 'dark'   // always 'dark' for matrix/synthwave
  // New
  colourTheme: ColourTheme
  setColourTheme: (t: ColourTheme) => void
}
```

**`resolvedTheme` for non-default themes:** always returns `'dark'` when `colourTheme` is `'matrix'` or `'synthwave'`.

**`system` mode:** the OS media-query listener fires only when `colourTheme === 'default'`. For Matrix/Synthwave it is bypassed.

**`data-theme` attribute:** on every colour theme change, set `document.documentElement.dataset.theme = colourTheme`. For Matrix/Synthwave, also add `dark` class to `<html>` (they are always dark).

**localStorage:**
- New key `colour-theme` stores `ColourTheme`, defaulting to `'default'` on first visit
- Existing key `theme` is unchanged — continues to store `'light' | 'dark' | 'system'`
- No migration needed: both keys are independent

---

## SettingsPage Changes

**File:** `frontend/src/pages/SettingsPage.tsx`

The colour theme swatch selector is added **directly in `SettingsPage.tsx`**, alongside the existing light/dark radio button section. `GeneralSettings.tsx` is not involved.

Changes:
1. Import `colourTheme` and `setColourTheme` from `useTheme()`
2. Add a new "Colour Theme" section above the existing light/dark toggle with three swatches (Default / Matrix / Synthwave), each showing a small colour preview and label
3. The existing light/dark radio buttons are **disabled and visually greyed out** when `colourTheme !== 'default'`, with a helper note ("Light/dark mode only applies to the Default theme")

**File:** `frontend/src/components/layout/Header/Header.tsx`

The dark/light mode toggle button is **hidden** when `colourTheme !== 'default'` (Matrix/Synthwave are always dark so the toggle is meaningless). Import `colourTheme` from `useTheme()` and add a conditional render around the toggle.

---

## Colour Class Migration

Systematic find-and-replace across `frontend/src/**/*.tsx`. Dark-mode paired classes collapse to a single semantic token:

| From (and dark: pair) | To |
|---|---|
| `bg-slate-900` / `dark:bg-slate-900` | `bg-page` |
| `bg-white` + `dark:bg-slate-800` | `bg-card` |
| `bg-slate-800` / `dark:bg-slate-800` | `bg-card` |
| `bg-slate-700` / `dark:bg-slate-700` | `bg-popover` |
| `bg-slate-50` + `dark:bg-slate-700/50` | `bg-subtle` |
| `bg-slate-700/50` / `dark:bg-slate-700/50` | `bg-subtle` |
| `text-slate-900` + `dark:text-white` | `text-body` |
| `text-slate-800` + `dark:text-slate-200` | `text-body` |
| `text-slate-700` + `dark:text-slate-300` | `text-dim` |
| `text-slate-600` + `dark:text-slate-400` | `text-dim` |
| `text-slate-500` + `dark:text-slate-400` | `text-hint` |
| `text-slate-400` / `dark:text-slate-500` | `text-hint` |
| `border-slate-200` + `dark:border-slate-700` | `border-edge` |
| `border-slate-100` + `dark:border-slate-700` | `border-rule` |
| `divide-slate-100` + `dark:divide-slate-700` | `divide-rule` |
| `bg-indigo-*` | `bg-primary-*` |
| `text-indigo-*` | `text-primary-*` |
| `border-indigo-*` | `border-primary-*` |

After migration, standalone `dark:` prefixed structural colour classes are removed — each theme is self-contained. Non-structural `dark:` classes (decorative elements not covered above) are reviewed case-by-case.

---

## File Inventory

### New / heavily modified
| File | Change |
|------|--------|
| `frontend/src/index.css` | Add per-theme CSS variable blocks; update `body` to use `--text-body` / `--bg-page` |
| `frontend/tailwind.config.js` | Wire `primary` + semantic tokens to CSS variables; update state colours |
| `frontend/src/context/ThemeContext.tsx` | Add `colourTheme` / `setColourTheme`; set `data-theme` attribute; gate OS listener |
| `frontend/src/pages/SettingsPage.tsx` | Add colour theme swatches; grey out light/dark toggle for non-default themes |
| `frontend/src/components/layout/Header/Header.tsx` | Hide dark/light toggle when `colourTheme !== 'default'` |

### Migration (colour class replacement)
All `.tsx` files under `frontend/src/` containing `bg-slate-*`, `text-slate-*`, `border-slate-*`, `divide-slate-*`, `bg-indigo-*`, `text-indigo-*`, or `border-indigo-*` — estimated 40–60 files.

---

## What Is Not Changed

- Font (Inter stays across all themes)
- Component structure — colour token change only
- `design-tokens.css` — file is kept; only the `body` colour/background declarations in `index.css` are updated to stop reading from it
- `secondary-*` Tailwind colour scale — untouched
- `success-*` scale usages (e.g. `bg-success-500` in Button, `text-success-800` in Toast) — these work via the updated `var(--success)` mid-range colour; no separate scale migration needed
- Test files — not in scope
