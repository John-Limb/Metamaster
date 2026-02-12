# Metamaster UI Revamp - Design System

## Overview

This document defines the modern design system for Metamaster, inspired by industry-leading media management applications like Sonarr and Radarr.

## Critical Design Principles

### Design System as Single Source of Truth
- **All UI components must use the design system** - No custom styling outside the design system
- **Deprecate legacy components** - Remove all existing components that don't conform to the design system
- **Enforce consistency** - Every visual element must follow design tokens and component specifications
- **No exceptions** - All new features must use design system components exclusively

### Empty States & Configuration Status
- **No dummy data** - Never display placeholder/mock data in the UI
- **Clean slate approach** - Show "Nothing here, yet" messages for empty states
- **Configuration status bar** - Display a prominent status bar at the top of the UI showing:
  - Incomplete configurations
  - Required setup steps
  - Missing API keys or settings
  - Action items for the user
- **Progressive disclosure** - Hide features until properly configured
- **Clear guidance** - Provide links to configuration pages from status messages

---

## Color Palette

### Primary Colors (Modern Indigo)
| Shade | Hex | Usage |
|-------|-----|-------|
| 50 | #f0f4ff | Lightest backgrounds |
| 100 | #e0e7ff | Light backgrounds |
| 200 | #c7d2fe | Hover states |
| 300 | #a5b4fc | Borders |
| 400 | #818cf8 | Secondary elements |
| 500 | #6366f1 | Main primary color |
| 600 | #4f46e5 | Darker primary |
| 700 | #4338ca | Active states |
| 800 | #3730a3 | Dark elements |
| 900 | #312e81 | Darkest |

### Accent Colors
| Color | Hex | Usage |
|-------|-----|-------|
| Success | #10b981 | Positive actions, confirmations |
| Warning | #f59e0b | Caution, warnings |
| Danger | #ef4444 | Destructive actions, errors |
| Info | #3b82f6 | Information, notifications |

### Neutral Colors
| Shade | Light | Dark | Usage |
|-------|-------|------|-------|
| 50/900 | #f8fafc | #0f172a | Backgrounds |
| 100/800 | #f1f5f9 | #1e293b | Surface |
| 200/700 | #e2e8f0 | #334155 | Borders |
| 500/400 | #64748b | #94a3b8 | Secondary text |
| 600/300 | #475569 | #cbd5e1 | Primary text |
| 700/200 | #334155 | #e2e8f0 | Headings |
| 900/50 | #0f172a | #f8fafc | Text on dark |

---

## Typography

| Element | Size | Weight | Line Height | Usage |
|---------|------|--------|-------------|-------|
| Display | 48px | Bold | 56px | Page titles |
| H1 | 36px | Bold | 44px | Section titles |
| H2 | 28px | Bold | 36px | Subsection titles |
| H3 | 24px | Semibold | 32px | Card titles |
| Body Large | 18px | Normal | 28px | Large text |
| Body | 16px | Normal | 24px | Default text |
| Body Small | 14px | Normal | 20px | Secondary text |
| Caption | 12px | Medium | 16px | Labels, hints |

---

## Spacing System

```
xs:   4px
sm:   8px
md:   12px
lg:   16px
xl:   24px
2xl:  32px
3xl:  48px
4xl:  64px
```

---

## Border Radius

```
sm:   4px
md:   8px
lg:   12px
xl:   16px
2xl:  20px
full: 9999px
```

---

## Shadows

```
Subtle:  0 1px 2px 0 rgba(0, 0, 0, 0.05)
Small:   0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)
Medium:  0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)
Large:   0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)
XL:      0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)
```

---

## Component Variants

### Button
```
Primary:   Indigo background, white text
Secondary: Gray background, dark text
Outline:   Transparent, indigo border
Ghost:     Transparent, indigo text
```

### Card
```
Default:   White background, subtle shadow
Elevated:  White background, larger shadow
Outlined:  Transparent, border
```

### Badge
```
Primary:   Indigo background, white text
Success:   Green background, white text
Warning:   Amber background, white text
Danger:    Red background, white text
Info:      Blue background, white text
```

---

## Responsive Breakpoints

```
sm:  640px
md:  768px
lg:  1024px
xl:  1280px
2xl: 1536px
```

---

## Animations

```
Transition Duration: 150ms (fast), 300ms (normal), 500ms (slow)
Easing: cubic-bezier(0.4, 0, 0.2, 1) (standard)
```

---

## Key Design Principles

1. **Modern Aesthetics**: Clean, contemporary design with proper spacing and typography
2. **User-Centric**: Intuitive navigation and clear visual hierarchy
3. **Functional**: Every design decision serves a purpose
4. **Accessible**: WCAG 2.1 AA compliance
5. **Responsive**: Works seamlessly on all devices
6. **Performant**: Optimized animations and transitions
7. **Consistent**: Unified design language throughout
8. **Dark Mode Ready**: Full support for light and dark themes
