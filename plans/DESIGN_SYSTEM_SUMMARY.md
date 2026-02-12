# Design System Summary

## Quick Reference

### Color Palette

#### Primary Colors (Modern Indigo)
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

#### Accent Colors
| Color | Hex | Usage |
|-------|-----|-------|
| Success | #10b981 | Positive actions, confirmations |
| Warning | #f59e0b | Caution, warnings |
| Danger | #ef4444 | Destructive actions, errors |
| Info | #3b82f6 | Information, notifications |

#### Neutral Colors
| Shade | Light | Dark | Usage |
|-------|-------|------|-------|
| 50/900 | #f8fafc | #0f172a | Backgrounds |
| 100/800 | #f1f5f9 | #1e293b | Surface |
| 200/700 | #e2e8f0 | #334155 | Borders |
| 500/400 | #64748b | #94a3b8 | Secondary text |
| 600/300 | #475569 | #cbd5e1 | Primary text |
| 700/200 | #334155 | #e2e8f0 | Headings |
| 900/50 | #0f172a | #f8fafc | Text on dark |

### Typography

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

### Spacing Scale

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

### Border Radius

```
sm:   4px
md:   8px
lg:   12px
xl:   16px
2xl:  20px
full: 9999px
```

### Shadows

```
Subtle:  0 1px 2px 0 rgba(0, 0, 0, 0.05)
Small:   0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)
Medium:  0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)
Large:   0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)
XL:      0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)
```

### Component Variants

#### Button
```
Primary:   Indigo background, white text
Secondary: Gray background, dark text
Outline:   Transparent, indigo border
Ghost:     Transparent, indigo text
```

#### Card
```
Default:   White background, subtle shadow
Elevated:  White background, larger shadow
Outlined:  Transparent, border
```

#### Badge
```
Primary:   Indigo background, white text
Success:   Green background, white text
Warning:   Amber background, white text
Danger:    Red background, white text
Info:      Blue background, white text
```

### Responsive Breakpoints

```
sm:  640px
md:  768px
lg:  1024px
xl:  1280px
2xl: 1536px
```

### Animations

```
Transition Duration: 150ms (fast), 300ms (normal), 500ms (slow)
Easing: cubic-bezier(0.4, 0, 0.2, 1) (standard)
```

---

## Component Specifications

### Card Component
```tsx
<Card variant="default" | "elevated" | "outlined">
  <CardHeader title="Title" subtitle="Subtitle" />
  <CardContent>Content</CardContent>
  <CardFooter>Actions</CardFooter>
</Card>
```

**Spacing**: 24px padding
**Border Radius**: 12px
**Shadow**: Medium (default), Large (elevated)

### Button Component
```tsx
<Button 
  variant="primary" | "secondary" | "outline" | "ghost"
  size="sm" | "md" | "lg"
  icon={<Icon />}
  loading={false}
  disabled={false}
>
  Click me
</Button>
```

**Sizes**:
- sm: 8px 12px, 14px font
- md: 10px 16px, 16px font
- lg: 12px 20px, 16px font

**Min Touch Target**: 44px

### Input Component
```tsx
<TextInput
  label="Label"
  placeholder="Placeholder"
  icon={<Icon />}
  error="Error message"
  disabled={false}
/>
```

**Height**: 40px
**Padding**: 10px 12px
**Border Radius**: 8px

### DataTable Component
```tsx
<DataTable
  columns={columns}
  data={data}
  sortable={true}
  filterable={true}
  paginated={true}
/>
```

**Row Height**: 48px
**Header Height**: 48px
**Padding**: 12px

---

## Dark Mode Implementation

### Color Mapping
- Light backgrounds → Dark backgrounds
- Light text → Light text
- Dark text → Dark text
- Borders → Lighter borders
- Shadows → Adjusted shadows

### CSS Variables
```css
:root {
  --color-bg: #ffffff;
  --color-surface: #f8fafc;
  --color-border: #e2e8f0;
  --color-text: #1e293b;
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: #0f172a;
    --color-surface: #1e293b;
    --color-border: #334155;
    --color-text: #f1f5f9;
  }
}
```

---

## Accessibility Guidelines

### Color Contrast
- Text on background: 4.5:1 (normal), 3:1 (large)
- UI components: 3:1 minimum

### Focus States
- Visible focus ring: 2px solid primary-500
- Focus ring offset: 2px

### Touch Targets
- Minimum size: 44x44px
- Minimum spacing: 8px

### Keyboard Navigation
- Tab order: logical and intuitive
- Escape key: close modals/dropdowns
- Enter key: submit forms/activate buttons
- Arrow keys: navigate lists/menus

### Screen Reader
- Semantic HTML
- ARIA labels where needed
- Proper heading hierarchy
- Form labels associated with inputs

---

## Usage Examples

### Creating a Modern Card
```tsx
<Card variant="elevated">
  <CardHeader 
    title="Movie Title"
    subtitle="2024 • Action"
  />
  <CardContent>
    <img src="poster.jpg" alt="Movie poster" />
  </CardContent>
  <CardFooter>
    <Button variant="primary" size="sm">Watch</Button>
    <Button variant="outline" size="sm">Details</Button>
  </CardFooter>
</Card>
```

### Creating a Modern Button Group
```tsx
<div className="flex gap-md">
  <Button variant="primary">Save</Button>
  <Button variant="outline">Cancel</Button>
  <Button variant="ghost" icon={<TrashIcon />}>Delete</Button>
</div>
```

### Creating a Modern Form
```tsx
<form className="space-y-lg">
  <TextInput 
    label="Email"
    type="email"
    placeholder="you@example.com"
  />
  <TextInput 
    label="Password"
    type="password"
    placeholder="••••••••"
  />
  <Button variant="primary" className="w-full">Sign In</Button>
</form>
```

---

## Migration Checklist

- [ ] Update Tailwind configuration
- [ ] Create design tokens CSS
- [ ] Update global styles
- [ ] Create theme context
- [ ] Create Card component
- [ ] Create Button component
- [ ] Create Badge component
- [ ] Create Input components
- [ ] Create DataTable component
- [ ] Create Navigation components
- [ ] Redesign Header
- [ ] Redesign Sidebar
- [ ] Update MainLayout
- [ ] Enhance Dashboard components
- [ ] Create Movies pages
- [ ] Create TV Shows pages
- [ ] Add micro-interactions
- [ ] Implement loading states
- [ ] Add error handling
- [ ] Accessibility audit
- [ ] Performance optimization
- [ ] Testing and QA

---

## Resources

- **Tailwind CSS**: https://tailwindcss.com
- **Radix UI**: https://www.radix-ui.com
- **Heroicons**: https://heroicons.com
- **WCAG 2.1**: https://www.w3.org/WAI/WCAG21/quickref/
- **Web Accessibility**: https://www.a11y-101.com

---

## Questions & Clarifications

### Q: Should we keep the old components during transition?
**A**: Yes, use feature flags to gradually migrate to new components.

### Q: How do we handle dark mode persistence?
**A**: Store preference in localStorage and detect system preference as fallback.

### Q: What about browser support?
**A**: Target modern browsers (Chrome, Firefox, Safari, Edge - latest 2 versions).

### Q: How do we test accessibility?
**A**: Use axe DevTools, WAVE, and manual keyboard/screen reader testing.

### Q: What about performance?
**A**: Monitor bundle size, use code splitting, optimize images, and run Lighthouse regularly.
