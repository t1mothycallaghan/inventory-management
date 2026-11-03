# Inline SVG nav icons

These are simple line icons for a 24x24 viewBox. Render them with `fill: none;
stroke: currentColor; stroke-width: 1.75; stroke-linecap: round;
stroke-linejoin: round` so they take on the link colour, including the
hover and active states. There's no dependency to install, and they look
consistent because they share one stroke weight and grid.

Pick by meaning, not by name. "Finance", "Spending" and "Budget" all take
the `wallet` icon, and "Analytics", "Reports" and "Insights" take `chart` or
`file`. When nothing fits, use `circle-dot`, which beats a misleading icon.
Never use emoji as icons.

```js
// Inner markup for <svg viewBox="0 0 24 24">, keyed by name
export const ICONS = {
  // Overview / dashboard / home
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  home: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9v12h14V9"/><path d="M10 21v-6h4v6"/>',

  // Inventory / products / stock / catalogue
  box: '<path d="M12 3 3 7.5v9L12 21l9-4.5v-9L12 3z"/><path d="M3 7.5 12 12l9-4.5"/><path d="M12 12v9"/>',

  // Orders / tasks / checklists
  clipboard: '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1"/><path d="M9 10h6"/><path d="M9 14h6"/><path d="M9 18h3"/>',

  // Finance / spending / billing / budget
  wallet: '<rect x="3" y="6" width="18" height="14" rx="2"/><path d="M3 10h18"/><path d="M16 15h2"/><path d="M6 6V5a1 1 0 0 1 1-1h10"/>',

  // Forecast / trends / growth / demand
  trend: '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',

  // Restocking / shipping / delivery / suppliers
  truck: '<path d="M2 6h12v11H2z"/><path d="M14 10h4l4 4v3h-8z"/><circle cx="6" cy="18.5" r="1.75"/><circle cx="18" cy="18.5" r="1.75"/>',

  // Reports / documents
  file: '<path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8z"/><path d="M14 3v5h5"/><path d="M9 13h6"/><path d="M9 17h6"/>',

  // Analytics / charts
  chart: '<path d="M4 20V10"/><path d="M10 20V4"/><path d="M16 20v-7"/><path d="M22 20H2"/>',

  // Backlog / queue / layers
  layers: '<path d="M12 3 2 8l10 5 10-5-10-5z"/><path d="M2 13l10 5 10-5"/>',

  // Customers / users / team
  users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7"/><path d="M18 14a6 6 0 0 1 3.5 6"/>',

  // Calendar / schedule
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18"/><path d="M8 3v4"/><path d="M16 3v4"/>',

  // Settings
  settings: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M2 12h3M19 12h3M4.9 19.1 7 17M17 7l2.1-2.1"/>',

  // Fallback
  'circle-dot': '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="1.5"/>',
}
```

You can put the map in its own module (`src/components/navIcons.js`) or
directly in the shell component's `<script>`. The separate module is nicer
when more than one component shows icons.

For the brand mark, a rounded square in the primary colour with the
product's initial in white is a clean default:

```html
<span class="brand-mark">F</span>
```

```css
.brand-mark {
  width: 32px; height: 32px; border-radius: var(--radius-md);
  display: grid; place-items: center;
  background: var(--color-primary); color: #fff; font-weight: 700; font-size: var(--font-sm);
}
```
