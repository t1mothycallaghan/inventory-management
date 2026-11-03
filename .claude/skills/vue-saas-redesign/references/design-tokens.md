# Design tokens

Tokens are CSS custom properties declared once on `:root` in the app's global
stylesheet (an unscoped `<style>` in the root component, or `src/style.css` /
`src/assets/main.css` - whichever the app already uses). They exist so that
every page draws spacing, colour, radius and depth from the same small set of
values. That shared set is most of what makes an interface read as "polished".

## Contents
1. Deriving the palette from the app
2. Token set (template)
3. Sweep rules: replacing raw values with tokens
4. What to leave alone
5. Component polish recipe

---

## 1. Deriving the palette from the app

Don't impose a new colour scheme. The user asked for a polished layout, not a
rebrand. Run `scripts/style_audit.py` and look at "Most used raw colours".
The top handful are the app's real palette, and the project's docs
(CLAUDE.md, README, a design-system section) often name them. Map each to a
semantic role:

| Role | How to recognise it |
|------|---------------------|
| `--color-text` | darkest colour used on headings (often a slate/gray 900) |
| `--color-text-muted` | mid gray used for labels, subtitles |
| `--color-border` | light gray used in `border: 1px solid ...` |
| `--color-surface` | card background (usually white) |
| `--color-bg` | page background (`body`), slightly off-white |
| `--color-surface-hover` | the light tint used on row/link hover |
| `--color-primary` | the accent on active nav links, primary buttons, focus rings |
| status colours | the success / warning / danger / info pairs used by badges |

The sidebar needs two more: `--sidebar-bg` and `--sidebar-text`. A dark
sidebar (the darkest text colour as background, light gray text) is the
classic SaaS look and gives the content area contrast. A light sidebar
(surface colour plus a right border) is the right call when the app's
identity is very light or the project docs ask for it. Either is fine. Pick
one and make the active-item treatment clearly visible against it.

## 2. Token set (template)

Fill in the colour values from step 1. The scales below are a sensible
default on a 4px grid. Keep them unless the app clearly uses another rhythm.

```css
:root {
  /* Spacing - 4px grid */
  --space-1: 0.25rem;  /* 4  */
  --space-2: 0.5rem;   /* 8  */
  --space-3: 0.75rem;  /* 12 */
  --space-4: 1rem;     /* 16 */
  --space-5: 1.25rem;  /* 20 */
  --space-6: 1.5rem;   /* 24 */
  --space-8: 2rem;     /* 32 */
  --space-10: 2.5rem;  /* 40 */
  --space-12: 3rem;    /* 48 */

  /* Radius */
  --radius-sm: 6px;    /* inputs, badges, small buttons */
  --radius-md: 8px;    /* buttons, nav items, alerts */
  --radius-lg: 12px;   /* cards, modals */
  --radius-full: 9999px;

  /* Elevation - soft, low-contrast shadows read as "modern" */
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.05);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);
  --shadow-lg: 0 12px 32px rgba(15, 23, 42, 0.12);

  /* Type scale */
  --font-xs: 0.75rem;
  --font-sm: 0.875rem;
  --font-base: 1rem;
  --font-lg: 1.125rem;
  --font-xl: 1.25rem;
  --font-2xl: 1.5rem;
  --font-3xl: 1.875rem;

  /* Colour - semantic roles (values from the app's own palette) */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-surface-hover: #f1f5f9;
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-text: #0f172a;
  --color-text-secondary: #334155;
  --color-text-muted: #64748b;
  --color-primary: #2563eb;
  --color-primary-soft: #eff6ff;

  --color-success: #059669;  --color-success-soft: #d1fae5;
  --color-warning: #d97706;  --color-warning-soft: #fef3c7;
  --color-danger:  #dc2626;  --color-danger-soft:  #fee2e2;
  --color-info:    #2563eb;  --color-info-soft:    #dbeafe;

  /* Layout */
  --sidebar-width: 248px;
  --topbar-height: 60px;
  --content-max-width: 1440px;
  --sidebar-bg: #0f172a;
  --sidebar-text: #94a3b8;
  --sidebar-text-active: #ffffff;
  --sidebar-item-hover: rgba(255, 255, 255, 0.06);
  --sidebar-item-active: rgba(255, 255, 255, 0.10);

  /* Stacking - read the app's existing z-indexes first; keep modals on top */
  --z-filterbar: 20;
  --z-topbar: 30;
  --z-sidebar: 40;
  --z-dropdown: 50;
  --z-modal: 1000;
}
```

The values shown are examples (a slate palette). Replace them with what the
audit found. If the app already defines some tokens, extend its naming rather
than introducing a parallel set.

## 3. Sweep rules: replacing raw values with tokens

The sweep touches only `<style>` blocks and `.css` files. It doesn't touch
template markup, script, or class names, so it can't break behaviour, and
the diff stays reviewable as a pure style change.

- **Spacing** (`padding`, `margin`, `gap`): snap each value to the nearest
  step. `0.313rem` becomes `var(--space-1)`, `0.625rem` becomes
  `var(--space-2)` or `var(--space-3)`, and `1.25rem` becomes
  `var(--space-5)`. When a value sits exactly between two steps, pick the
  one that keeps the element's current look. The goal is consistency, not a
  visible jump. Multi-value shorthands get one token per part:
  `padding: var(--space-2) var(--space-3)`.
- **Radius**: collapse the app's assortment (4/5/6/8/10/12px) onto `sm / md /
  lg` by element role. Cards and modals take `lg`, buttons and nav items take
  `md`, and badges and inputs take `sm`. Pills stay `full`.
- **Shadows**: map to `sm / md / lg` by intent: resting card, hover or
  dropdown, then modal. Focus rings (`0 0 0 3px ...`) are not elevation.
  Express them with the primary colour at low alpha, or keep them as they are.
- **Font sizes**: snap to the type scale. Odd values like `0.813rem` and
  `0.938rem` are the clearest sign of drift. Map them to `--font-sm` and
  `--font-base` (or `--font-sm`, if `--font-base` would visibly enlarge dense
  UI such as tables and filters).
- **Colours**: replace exact (case-insensitive) matches of a token's value
  with the token. Near-duplicates (for example `#3b82f6` next to a
  `#2563eb` primary) are worth unifying on interactive elements such as
  buttons, links and focus rings. Leave them alone in data visualisation.
- **Consistent page chrome**: page headers, cards, card headers, tables and
  stat cards are usually defined globally. Make sure their padding comes
  from the same steps, so every page has the same rhythm: page padding
  `--space-8`, gap between cards `--space-6`, card padding `--space-6`, and
  table cell padding `--space-3` by `--space-4`.

## 4. What to leave alone

- Chart and SVG geometry: widths, heights, stroke widths, series colours, and
  anything computed in script. Charts encode data, and "tidying" their
  colours can change meaning.
- `width`, `height`, `min-width`, `max-width`, `flex-basis` and grid track
  sizes. These are layout geometry, not spacing rhythm.
- `0`, `1px` borders, `auto`, percentages, and `em` values that deliberately
  scale with local font size.
- Third-party component styles and anything in `node_modules`.
- Values inside a `@media print` block.

Leaving something raw is fine when tokenising it would make it less clear.
Record it in the final report instead of forcing it.

## 5. Component polish recipe

These are the details that separate "consistent" from "modern SaaS". Apply
them to the shared classes in the global stylesheet: whatever the app calls
its card, stat tile, table, badge and button. Use the app's own class names,
and don't rename them.

**Cards**
- `background: var(--color-surface)`, `border: 1px solid var(--color-border)`,
  `border-radius: var(--radius-lg)`, `box-shadow: var(--shadow-sm)`, and
  `padding: var(--space-6)`.
- Card header: title at `--font-lg`, weight 600. Drop the heavy full-width
  underline in favour of spacing (`margin-bottom: var(--space-4)`), or keep a
  single hairline `var(--color-border)` divider. Don't use both.
- Hover lift only on clickable cards: `box-shadow: var(--shadow-md)`.
  Static cards shouldn't move.

**Stat tiles / KPI cards**
- Label: `--font-xs` or `--font-sm`, muted colour, weight 500, sentence or
  upper case (keep whatever the app uses).
- Value: `--font-2xl` or `--font-3xl`, weight 700, `--color-text`, with
  `font-variant-numeric: tabular-nums` so the digits line up.
- Status tints (warning, danger and so on) colour the value or a small
  accent, not the whole tile background.

**Tables**
- Header row: `--color-bg` background, `--font-xs`, upper case, muted,
  weight 600, letter-spacing 0.04em.
- Cells: `padding: var(--space-3) var(--space-4)`, a `--color-border`
  hairline between rows only (no vertical borders), and row hover
  `--color-surface-hover`.
- A table inside a card sits flush with the card's edges (negative margin
  or zero card padding for that section), so the header row background
  spans the full width.
- Numeric columns are right-aligned with `tabular-nums`, if the app already
  marks them with a class. Don't add classes to markup to achieve it.

**Badges / status pills**
- `border-radius: var(--radius-full)`,
  `padding: var(--space-1) var(--space-3)`, `--font-xs`, weight 600.
- Soft background plus strong text from the same hue (`--color-*-soft` and
  `--color-*`). Use sentence case unless the app's badges are deliberately
  upper case.

**Buttons and inputs**
- Height around 36px (`padding: var(--space-2) var(--space-4)`),
  `border-radius: var(--radius-md)`, weight 500.
- Primary: `--color-primary` background, white text, and a slightly darker
  hover. Secondary: surface background with a `--color-border-strong`
  border.
- Focus: `box-shadow: 0 0 0 3px` the primary colour at about 15% alpha,
  plus a primary-coloured border on inputs. A visible focus ring is part
  of looking professional.

**Page header**
- Title `--font-2xl` to `--font-3xl`, weight 700, letter-spacing -0.02em.
  Subtitle muted at `--font-sm`, with `margin-bottom: var(--space-6)` before
  the first card row.

**Grids of cards**
- One gap value everywhere (`--space-6`), for both rows of stat tiles and
  card grids, so every page has the same rhythm.
