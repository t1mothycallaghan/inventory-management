---
name: vue-saas-redesign
description: Redesign a Vue 3 app's UI into a modern SaaS-style interface. Replaces the top navigation bar with a fixed left sidebar with inline SVG icons, introduces design tokens (spacing scale, radii, shadows, semantic colours) and sweeps every view onto them, and refreshes shared cards, tables, badges and buttons for clean modern card layouts and a polished, professional look, without changing routes, logic or data. Use this whenever the user wants to modernise, restyle, polish or "make professional" a Vue / Vite frontend, move navigation to a sidebar, switch from top nav to side nav, make an admin panel or dashboard look like a SaaS product, or fix inconsistent spacing across pages, even if they don't say "redesign" or "SaaS".
---

# Vue 3 SaaS redesign

Turn a Vue 3 app with a top nav bar into a SaaS-style app shell. The result
has a fixed left sidebar with icon and label nav items, a slim top bar for
utilities, and content that sits on one consistent spacing, radius,
elevation and colour system.

This is a **presentation-layer change**. Routes, component APIs, i18n keys,
data fetching and business logic stay exactly as they are. That constraint
keeps the change safe to ship and easy to review: if something
behaves differently afterwards, it's a bug in the redesign. It also means you
don't need to understand every view's logic, only its styles.

## Reference files

Read these when you reach the matching step, not all up front:

- `references/sidebar-shell.md`: shell template, CSS, where each header item moves, active-state logic, and a pitfalls checklist
- `references/design-tokens.md`: token template, how to derive the palette from the app, and sweep rules
- `references/icons.md`: inline SVG icon set and how to pick icons
- `scripts/style_audit.py`: counts raw style values per file and flags offsets tied to the old header height

## Workflow

### 1. Read the project's rules first

Check `CLAUDE.md`, `README`, `.claude/agents/` and any design-system notes
before planning. Projects often specify:

- **A palette or design system.** It overrides the example values in
  design-tokens.md. Use the project's colours, not a new brand.
- **Bans** (such as no emojis in the UI, or no new dependencies).
- **Delegation rules** (such as "all .vue edits go to the vue-expert
  agent"). If one exists, you still do discovery and write the plan
  yourself, then hand each implementation step to that agent with a precise
  brief: the file list, the token block, the shell spec, the pitfalls found
  in discovery, and paths to this skill's reference files so it can read
  them. Splitting the work into shell + tokens first and the view sweep
  second keeps each brief focused.

### 2. Discover the current shell

Find out, concretely:

1. **Where the nav lives.** Usually the root component (`App.vue`) or a
   `Header` / `Navbar` component. List every link in order, with its route,
   label expression (`t('nav.x')` or a literal) and active-state logic.
2. **Everything else in the header.** Brand and subtitle, language
   switcher, profile menu, notifications, search. Each needs a new home (see
   the table in sidebar-shell.md, section 4).
3. **The router.** Make sure every nav link matches a route. Routes with no
   nav link stay without one.
4. **Global styles.** Find where they live (an unscoped `<style>` in
   `App.vue`, or `main.css` / `style.css`) and whether tokens already exist.
5. **Sticky and fixed elements, and z-indexes.** Look at filter bars,
   toolbars, modals and dropdowns.
6. **The old header's height.** Then run the audit:

```bash
python <skill-dir>/scripts/style_audit.py <client>/src --header-height <N>
```

Keep the output. It's the "before" picture for the report and the to-do list
for the sweep. The "Offsets tied to the header" section lists things that
will break when the header goes away.

7. **Do pages render their own heading?** Look for a large `<h1>`/`<h2>`
   or a `.page-header` at the top of each view. If they do, the top bar
   should hold only utilities. Putting the page name there as well shows it
   twice on every screen, which reads as unfinished, not polished.

### 2b. Settle the sidebar tone

The sidebar is the most visible single choice in the redesign, and both
options are legitimate SaaS looks. A dark sidebar gives strong contrast and
the "app" feel. A light one (white with a right border) is quieter and
closer to most existing light UIs. Don't default silently:

- If the user or the project docs already say which, use that.
- Otherwise, if you can ask the user (an ask-question tool, or an
  interactive session), offer both with a one-line description of each,
  and recommend the one that fits the app's current look.
- If you can't ask, infer it. A white top bar and a very light UI suggest
  light, and an app that already has dark chrome suggests dark. State the
  choice in the report and point out that switching it means changing
  only the `--sidebar-*` tokens (see sidebar-shell.md, section 3).

### 3. Add design tokens

Add a `:root { ... }` token block to the global stylesheet, following
design-tokens.md. Take the colours from the audit's "most used colours" and
the project's documented palette. Tokens come first because both the shell
and the sweep are written in terms of them.

### 4. Rebuild the shell

Follow sidebar-shell.md:

- Replace the top nav with `.sidebar` (brand, nav, footer) and `.app-main`
  (top bar, any existing sub-toolbar such as a filter bar, then
  `<main><router-view/></main>`).
- Drive the nav from a `navItems` array. Keep the same links, order and
  label expressions, and add one icon from icons.md per item.
- Move every other header item to its new home. Nothing disappears.
- Keep modals mounted at the root, outside both columns.
- Fix every header-height offset the audit flagged, and check the rest of
  the pitfalls checklist, especially sticky sub-toolbars, max-width
  alignment, and modals staying above the sidebar.
- Delete the old `.top-nav` / `.nav-tabs` CSS once nothing references it.
  Dead nav CSS confuses the next person.

### 4b. Polish the shared components

Tokens make values consistent, but the "modern SaaS" feel comes mostly from
how the shared building blocks look: cards, stat tiles, tables, badges,
buttons and inputs. These are usually defined once in the global
stylesheet, so restyling them there updates every page with no markup
changes. Apply the component recipe in design-tokens.md, section 5. Do this
before the sweep, so the sweep can line per-view overrides up with the
refreshed defaults.

### 5. Sweep the views and components onto the tokens

Go through every `.vue` file under `src/views` and `src/components`, and
any `.css` files. Edit only `<style>` blocks, using the sweep rules in
design-tokens.md, section 3. Work file by file, starting with the files the
audit ranks highest. Re-run the audit as you go, so the counts show
progress.

The aim is visible consistency, not a zero count. Shared chrome (page
headers, cards, card headers, stat cards, tables, badges, buttons, inputs)
should use the same spacing steps, radii and shadows on every page. Leave
chart colours, chart geometry and one-off dimensions alone (see section 4 of
that file).

### 6. Verify

1. **Build.** Run the project's build (`npm run build`, or the equivalent
   from `package.json`). It must pass.
2. **Re-run the audit.** Raw spacing, radius, shadow and font-size counts
   should drop substantially, and "Offsets tied to the header" should list
   nothing. Explain anything left over.
3. **Look at it.** If a browser tool is available (Playwright MCP, Claude in
   Chrome), start the dev server and visit every route at about 1440px wide.
   Check that:
   - the sidebar shows every link, and the active state follows navigation,
     including `/` not lighting up everywhere;
   - the language switcher (if any) still relabels the sidebar;
   - the profile and other menus open and aren't clipped;
   - a modal overlays the sidebar;
   - sticky bars stick directly under the top bar with no gap;
   - nothing scrolls horizontally;
   - the view at about 800px wide is usable.

   Take a screenshot of two or three key pages. If no browser tool is
   available, say so plainly and give the user the checklist to run.
4. **Diff review.** `git diff --stat` should touch style blocks almost
   everywhere, and markup only in the shell component (plus an icon module,
   if you created one). Treat script or markup changes in views as a red
   flag: revert them.

### 7. Report

Tell the user:

- what the new shell looks like and where each header item went;
- the audit counts before and after (a small table);
- the pitfalls found and fixed (such as "filter bar was sticky at 70px, now
  sits under the top bar");
- anything deliberately left alone and why (charts, one-off geometry, a
  hard-coded untranslated label);
- whether it was verified in a browser, or which checks are still manual.

Don't commit unless the user asks.

## Out of scope

Unless the user asks, don't add:

- **UI frameworks, Tailwind, or icon packages.** New dependencies turn a
  style change into a build-system change.
- **Mobile drawers, a collapsible rail, dark mode, or new nav groupings.**
  These are separate features, each with its own behaviour to test. The
  basic narrow-screen fallback in sidebar-shell.md is enough to keep the
  layout from breaking.
- **New translation keys, renamed routes, or changed page content or
  copy.**

If one of these would clearly help, mention it at the end as a follow-up.
