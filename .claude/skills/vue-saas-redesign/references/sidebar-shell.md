# Sidebar app shell

This is the reference structure for replacing a top navigation bar with a
fixed left sidebar. Adapt the names to the app: keep its component names,
translation calls, and anything already rendered in the old header.

## Contents
1. Layout model
2. Template skeleton
3. Styles
4. Moving the old header's contents
5. Active state
6. Narrow screens
7. Pitfalls checklist

---

## 1. Layout model

```
+-----------+---------------------------------------------+
|  Brand    |  Top bar: page title / utilities (sticky)   |
|           +---------------------------------------------+
|  Nav      |  Filter bar or sub-toolbar (sticky, if any) |
|  items    +---------------------------------------------+
|           |                                             |
|           |  <router-view />  (max-width, centred)      |
|  Footer   |                                             |
+-----------+---------------------------------------------+
 fixed,        margin-left: var(--sidebar-width)
 full height
```

The sidebar is `position: fixed` and spans the full viewport height. The
content column is offset by `--sidebar-width` and scrolls with the
document, so window scrolling, scroll restoration and any `window.scrollTo`
code keep working. A sidebar inside a CSS grid with an inner scroll
container also works, but it breaks code that listens to `window` scroll.
Prefer the fixed version unless the app already scrolls an inner element.

## 2. Template skeleton

```vue
<template>
  <div class="app-shell">
    <aside class="sidebar" aria-label="Primary">
      <div class="sidebar-brand">
        <!-- Whatever the old header used as the logo / product name -->
        <span class="brand-mark" aria-hidden="true"><!-- small inline SVG or initial --></span>
        <div class="brand-text">
          <span class="brand-name">{{ t('nav.companyName') }}</span>
          <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="sidebar-link"
          :class="{ active: isActive(item) }"
        >
          <svg class="sidebar-icon" viewBox="0 0 24 24" aria-hidden="true" v-html="item.icon" />
          <span class="sidebar-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <!-- Optional: profile menu, version, help link -->
      </div>
    </aside>

    <div class="app-main">
      <header class="topbar">
        <h1 class="topbar-title">{{ currentTitle }}</h1>
        <div class="topbar-actions">
          <!-- Utilities moved from the old header: language switcher, profile menu, notifications -->
        </div>
      </header>
      <!-- Sticky sub-toolbars (filter bars) go here, between the top bar and the content -->
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <!-- Modals stay at the root, outside both columns, so they overlay everything -->
  </div>
</template>
```

`navItems` is a plain array in `setup()`:

```js
// Icons are inline SVG inner markup (see icons.md): no icon library, no emojis.
const navItems = computed(() => [
  { to: '/', label: t('nav.overview'), icon: ICONS.grid, exact: true },
  { to: '/inventory', label: t('nav.inventory'), icon: ICONS.box },
  // ...one entry per link that was in the old nav, same order, same labels
])
```

Make it `computed` when labels come from an i18n function, so that
switching language updates the sidebar. If the old nav had a hard-coded
label that wasn't translated, keep it hard-coded and mention it in the
report. Adding translation keys is out of scope.

`v-html` on an `<svg>` with static strings that you wrote is safe. Never
feed it user or API data. If the project lints against `v-html`, render the
icons with a tiny `NavIcon` component that switches on a name and emits
`<path>` elements instead.

`currentTitle` can come from the active nav item's label, falling back to
`route.meta.title` or nothing. The top bar is optional. If every page
already renders its own large page header, the top bar can hold only the
utilities, with no title, so the page name doesn't appear twice.

## 3. Styles

The global (unscoped) stylesheet already has `* { box-sizing }`, `body`, and
similar rules. Replace the old `.top-nav` / `.nav-tabs` rules with these
(the token names come from design-tokens.md):

```css
.app-shell { min-height: 100vh; }

.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  width: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  z-index: var(--z-sidebar);
  overflow-y: auto;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: var(--topbar-height);      /* aligns with the top bar's bottom edge */
  padding: 0 var(--space-5);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.brand-text { display: flex; flex-direction: column; min-width: 0; line-height: 1.2; }
.brand-name { color: var(--sidebar-text-active); font-weight: 700; font-size: var(--font-base); }
.brand-subtitle { font-size: var(--font-xs); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4) var(--space-3);
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  color: var(--sidebar-text);
  font-size: var(--font-sm);
  font-weight: 500;
  text-decoration: none;
  transition: background-color 0.15s ease, color 0.15s ease;
}
.sidebar-link:hover { background: var(--sidebar-item-hover); color: var(--sidebar-text-active); }
.sidebar-link.active { background: var(--sidebar-item-active); color: var(--sidebar-text-active); }
.sidebar-link:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }

.sidebar-icon {
  width: 20px; height: 20px; flex-shrink: 0;
  fill: none; stroke: currentColor; stroke-width: 1.75;
  stroke-linecap: round; stroke-linejoin: round;
}

.sidebar-footer { padding: var(--space-4) var(--space-3); border-top: 1px solid rgba(255, 255, 255, 0.06); }

.app-main {
  margin-left: var(--sidebar-width);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  min-width: 0;                        /* lets wide tables scroll instead of pushing the layout */
}

.topbar {
  position: sticky;
  top: 0;
  z-index: var(--z-topbar);
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: 0 var(--space-8);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}
.topbar-title { font-size: var(--font-lg); font-weight: 600; color: var(--color-text); }
.topbar-actions { display: flex; align-items: center; gap: var(--space-3); margin-left: auto; }

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--space-8);
}
```

For a light sidebar, set `--sidebar-bg` to the surface colour,
`--sidebar-text` to the muted text colour and `--sidebar-text-active` to the
primary colour, then add `border-right: 1px solid var(--color-border)` and
switch the brand and footer dividers to `var(--color-border)`.

## 4. Moving the old header's contents

List everything in the old header before deleting it. Nothing should
disappear.

| Was in the top bar | Goes to |
|--------------------|---------|
| Logo / product name / subtitle | `.sidebar-brand` |
| Nav links | `.sidebar-nav`, same order and labels |
| Language / theme switchers | `.topbar-actions` |
| Profile / account menu | `.topbar-actions` (or `.sidebar-footer`) |
| Search, notifications | `.topbar-actions` |
| Global filter bar under the header | stays directly under `.topbar` inside `.app-main` |

Dropdown menus that used to open downward from the top bar still open
downward from `.topbar-actions`. If you move a menu into the sidebar
footer, check that it opens upward or sideways and isn't clipped by
`overflow-y: auto`. Clipping is the usual reason to keep menus in the top
bar.

## 5. Active state

Keep whatever active logic the old nav used, if it worked. It's easy to
regress. The common patterns:

- `router-link` adds `router-link-active`, a prefix match on which `/`
  matches everything, and `router-link-exact-active`. A helper like
  `isActive(item) = item.exact ? route.path === item.to : route.path.startsWith(item.to)`
  makes the intent explicit and handles nested routes (`/orders/123`).
- Router-link sets `aria-current="page"` on the exact-active link
  automatically. Don't remove it.

## 6. Narrow screens

A full mobile drawer is a separate feature. Without one, the layout still
mustn't break on a laptop at 125% zoom or a narrow window:

```css
@media (max-width: 900px) {
  .sidebar { position: static; width: auto; height: auto; flex-direction: row; overflow-x: auto; }
  .sidebar-nav { flex-direction: row; padding: var(--space-2); }
  .sidebar-footer, .brand-subtitle { display: none; }
  .app-main { margin-left: 0; }
}
```

## 7. Pitfalls checklist

These are the things that silently break when the header goes away. Check
each one:

- **Offsets tied to the old header height.** `style_audit.py --header-height N`
  lists them. Typical examples are a sticky filter bar with `top: 70px`,
  `calc(100vh - 70px)` panels, `scroll-margin-top`, and JS that reads
  `offsetHeight` of the header. Re-point them at `var(--topbar-height)`, or
  at `0` if there is no top bar.
- **Max-width containers.** The old header often centred its content with
  `max-width` plus `margin: 0 auto`, and sub-toolbars copied that. Inside
  `.app-main` they should line up with `.main-content`'s padding and
  max-width, otherwise the filter bar and the page content start at
  different x positions.
- **z-index.** Modals and dropdowns must stay above the sidebar. Grep the
  existing z-indexes. The sidebar should sit above the content, and modal
  overlays (often `z-index: 1000` or more) should sit above the sidebar. A
  modal overlay with `position: fixed; inset: 0` already covers the sidebar
  if its z-index is higher.
- **Horizontal overflow.** `min-width: 0` on `.app-main` stops wide tables
  from pushing the page wider than the viewport.
- **Full-width backgrounds.** Elements that relied on `width: 100vw` now
  extend under the sidebar. Use `100%` instead.
