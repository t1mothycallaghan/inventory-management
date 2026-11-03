<template>
  <div class="app-shell" :class="shellClasses">
    <aside id="app-sidebar" ref="sidebarRef" class="sidebar" aria-label="Primary">
      <div class="sidebar-brand">
        <span class="brand-mark" aria-hidden="true">F</span>
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
          :data-label="item.label"
        >
          <!-- v-html is safe here: icon markup is a static, hard-coded map in this file, never user/API data -->
          <svg class="sidebar-icon" viewBox="0 0 24 24" aria-hidden="true" v-html="item.icon" />
          <span class="sidebar-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <button
          type="button"
          class="sidebar-toggle"
          aria-controls="app-sidebar"
          :aria-expanded="String(!isRail)"
          :aria-label="toggleLabel"
          :title="toggleLabel"
          @click="toggleSidebar"
        >
          <svg class="sidebar-toggle-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M15 6l-6 6 6 6" />
          </svg>
        </button>
      </div>
    </aside>

    <div class="app-main">
      <!-- Top bar holds utilities only: each view renders its own page header -->
      <header class="topbar">
        <div class="topbar-actions">
          <LanguageSwitcher />
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </div>
      </header>
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

const SIDEBAR_KEY = 'inventory.sidebarCollapsed'
const LARGE_QUERY = '(min-width: 1024px)'

// localStorage can throw (private mode, blocked storage): fall back to expanded / skip saving.
const readSavedCollapsed = () => {
  try { return localStorage.getItem(SIDEBAR_KEY) === 'true' } catch (e) { return false }
}
const saveCollapsed = (value) => {
  try { localStorage.setItem(SIDEBAR_KEY, String(value)) } catch (e) { /* ignore */ }
}

// Inline SVG inner markup for a 24x24 viewBox (no icon library). Static strings only.
const ICONS = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  box: '<path d="M12 3 3 7.5v9L12 21l9-4.5v-9L12 3z"/><path d="M3 7.5 12 12l9-4.5"/><path d="M12 12v9"/>',
  clipboard: '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1"/><path d="M9 10h6"/><path d="M9 14h6"/><path d="M9 18h3"/>',
  wallet: '<rect x="3" y="6" width="18" height="14" rx="2"/><path d="M3 10h18"/><path d="M16 15h2"/><path d="M6 6V5a1 1 0 0 1 1-1h10"/>',
  trend: '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
  truck: '<path d="M2 6h12v11H2z"/><path d="M14 10h4l4 4v3h-8z"/><circle cx="6" cy="18.5" r="1.75"/><circle cx="18" cy="18.5" r="1.75"/>',
  chart: '<path d="M4 20V10"/><path d="M10 20V4"/><path d="M16 20v-7"/><path d="M22 20H2"/>'
}

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const route = useRoute()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Breakpoint logic: at >= 1024px the user's saved choice (collapsed or expanded) applies.
    // Below it the sidebar is always a rail, and the toggle opens it as an overlay instead.
    const mql = window.matchMedia(LARGE_QUERY)
    const isLargeScreen = ref(mql.matches)
    // Saved large-screen preference. Only written by the toggle while on a large screen, so
    // small screens (which force the rail) never overwrite it and it is restored on resize up.
    const userCollapsed = ref(readSavedCollapsed())
    const overlayOpen = ref(false)
    const sidebarRef = ref(null)

    const isRail = computed(() =>
      isLargeScreen.value ? userCollapsed.value : !overlayOpen.value
    )
    // Overlay (not push): on small screens the content keeps the rail's margin and the
    // expanded sidebar floats above it, so opening the menu never reflows the page.
    const shellClasses = computed(() => ({
      'sidebar-collapsed': isRail.value,
      'sidebar-overlay-open': !isLargeScreen.value && overlayOpen.value
    }))
    const toggleLabel = computed(() =>
      isRail.value ? t('nav.expandSidebar') : t('nav.collapseSidebar')
    )

    const toggleSidebar = () => {
      if (isLargeScreen.value) {
        userCollapsed.value = !userCollapsed.value
        saveCollapsed(userCollapsed.value)
      } else {
        overlayOpen.value = !overlayOpen.value
      }
    }

    const onBreakpointChange = (e) => {
      isLargeScreen.value = e.matches
      overlayOpen.value = false
    }
    const onDocumentClick = (e) => {
      if (overlayOpen.value && sidebarRef.value && !sidebarRef.value.contains(e.target)) {
        overlayOpen.value = false
      }
    }
    const onKeydown = (e) => {
      if (e.key === 'Escape' && overlayOpen.value) overlayOpen.value = false
    }

    // Close the overlay after navigating via a nav link
    watch(() => route.path, () => { overlayOpen.value = false })

    onMounted(() => {
      mql.addEventListener('change', onBreakpointChange)
      document.addEventListener('click', onDocumentClick)
      document.addEventListener('keydown', onKeydown)
    })
    onBeforeUnmount(() => {
      mql.removeEventListener('change', onBreakpointChange)
      document.removeEventListener('click', onDocumentClick)
      document.removeEventListener('keydown', onKeydown)
    })

    // computed so labels re-translate when the language changes.
    // 'Reports' was hard-coded (untranslated) in the old nav; kept as is.
    const navItems = computed(() => [
      { to: '/', label: t('nav.overview'), icon: ICONS.grid, exact: true },
      { to: '/inventory', label: t('nav.inventory'), icon: ICONS.box },
      { to: '/orders', label: t('nav.orders'), icon: ICONS.clipboard },
      { to: '/spending', label: t('nav.finance'), icon: ICONS.wallet },
      { to: '/demand', label: t('nav.demandForecast'), icon: ICONS.trend },
      { to: '/restocking', label: t('nav.restocking'), icon: ICONS.truck },
      { to: '/reports', label: 'Reports', icon: ICONS.chart }
    ])

    // '/' is exact-only because every path starts with '/'; others use a
    // prefix match so nested routes (e.g. /orders/123) keep the item active.
    const isActive = (item) =>
      item.exact ? route.path === item.to : route.path.startsWith(item.to)

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      navItems,
      isActive,
      sidebarRef,
      isRail,
      shellClasses,
      toggleLabel,
      toggleSidebar,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

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

  /* Elevation */
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.05);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);
  --shadow-lg: 0 12px 32px rgba(15, 23, 42, 0.12);
  --focus-ring: 0 0 0 3px rgba(37, 99, 235, 0.15);

  /* Type scale */
  --font-xs: 0.75rem;
  --font-sm: 0.875rem;
  --font-base: 1rem;
  --font-lg: 1.125rem;
  --font-xl: 1.25rem;
  --font-2xl: 1.5rem;
  --font-3xl: 1.875rem;

  /* Colour - semantic roles, from the project's slate palette */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-surface-hover: #f1f5f9;
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-text: #0f172a;
  --color-text-secondary: #334155;
  --color-text-subtle: #475569;
  --color-text-muted: #64748b;
  --color-text-faint: #94a3b8;
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-primary-soft: #eff6ff;

  --color-success: #059669;  --color-success-soft: #d1fae5;  --color-success-text: #065f46;
  --color-warning: #ea580c;  --color-warning-soft: #fed7aa;  --color-warning-text: #92400e;
  --color-danger:  #dc2626;  --color-danger-soft:  #fecaca;  --color-danger-text:  #991b1b;
  --color-info:    #2563eb;  --color-info-soft:    #dbeafe;  --color-info-text:    #1e40af;

  /* Layout */
  --sidebar-width: 248px;
  --sidebar-width-collapsed: 72px;
  --topbar-height: 60px;
  --content-max-width: 1440px;
  /* Light sidebar: white surface, muted text, blue active item.
     Switching to dark later means changing only these --sidebar-* tokens. */
  --sidebar-bg: var(--color-surface);
  --sidebar-text: var(--color-text-muted);
  --sidebar-text-active: var(--color-primary);
  --sidebar-item-hover: var(--color-surface-hover);
  --sidebar-item-active: var(--color-primary-soft);

  /* Stacking - modals (1000/2000 in components) stay above the sidebar */
  --z-filterbar: 20;
  --z-topbar: 30;
  --z-sidebar: 40;
  --z-dropdown: 50;
  --z-tooltip: 60;   /* rail tooltips: above top bar/sidebar, far below modals */
  --z-modal: 1000;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--color-bg);
  color: #1e293b;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ---- App shell ---- */
.app-shell {
  min-height: 100vh;
  /* --sidebar-current: the sidebar's own width. --sidebar-offset: space reserved for it beside the content. */
  --sidebar-current: var(--sidebar-width);
  --sidebar-offset: var(--sidebar-width);
}
.app-shell.sidebar-collapsed {
  --sidebar-current: var(--sidebar-width-collapsed);
  --sidebar-offset: var(--sidebar-width-collapsed);
}
/* Overlay: sidebar is full width but content keeps the rail's margin (no reflow) */
.app-shell.sidebar-overlay-open {
  --sidebar-current: var(--sidebar-width);
  --sidebar-offset: var(--sidebar-width-collapsed);
}

.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  width: var(--sidebar-current);
  display: flex;
  flex-direction: column;
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  border-right: 1px solid var(--color-border);
  z-index: var(--z-sidebar);
  overflow-y: auto;
  overflow-x: hidden;
  transition: width 0.2s ease, box-shadow 0.2s ease;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: var(--topbar-height);      /* aligns with the top bar's bottom edge */
  padding: 0 var(--space-5);
  border-bottom: 1px solid var(--color-border);
}

.brand-mark {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: var(--radius-md);
  display: grid;
  place-items: center;
  background: var(--color-primary);
  color: #fff;
  font-weight: 700;
  font-size: var(--font-sm);
}

.brand-text { display: flex; flex-direction: column; min-width: 0; line-height: 1.2; }
.brand-name { color: var(--color-text); /* dark text; --sidebar-text-active is blue in the light theme */ font-weight: 700; font-size: var(--font-base); }
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
  white-space: nowrap;
  position: relative;
  transition: background-color 0.15s ease, color 0.15s ease;
}
.sidebar-link:hover { background: var(--sidebar-item-hover); color: var(--color-text); }
.sidebar-link.active { background: var(--sidebar-item-active); color: var(--sidebar-text-active); }
.sidebar-link:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }

.sidebar-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.sidebar-footer { padding: var(--space-4) var(--space-3); border-top: 1px solid var(--color-border); }
.sidebar-toggle {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-faint);
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}
.sidebar-toggle:hover { background: var(--sidebar-item-hover); color: var(--color-text); }
.sidebar-toggle:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }
.sidebar-toggle-icon {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: transform 0.2s ease;
}

/* ---- Rail mode (icons only) ---- */
.sidebar-collapsed .sidebar-brand { justify-content: center; padding: 0; gap: 0; }
.sidebar-collapsed .brand-text { display: none; }
.sidebar-collapsed .sidebar-nav { align-items: center; }
.sidebar-collapsed .sidebar-link { width: 40px; height: 40px; padding: 0; justify-content: center; gap: 0; }
.sidebar-collapsed .sidebar-footer { display: flex; justify-content: center; padding-left: 0; padding-right: 0; }
.sidebar-collapsed .sidebar-toggle-icon { transform: rotate(180deg); }
/* Labels stay in the DOM for screen readers, just visually hidden (not display:none) */
.sidebar-collapsed .sidebar-label {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}
/* Tooltips are absolutely positioned outside the 72px rail, so the sidebar must not clip them.
   overflow-y:auto/overflow-x:hidden would, so rail mode uses overflow:visible. Trade-off: the
   rail (7 icons) doesn't scroll on very short viewports; the expanded sidebar still does. */
.sidebar-collapsed .sidebar { overflow: visible; }
.sidebar-collapsed .sidebar-link::after {
  content: attr(data-label);
  position: absolute;
  left: calc(100% + var(--space-2));
  top: 50%;
  transform: translateY(-50%);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  background: var(--color-text);
  color: #fff;
  font-size: var(--font-xs);
  font-weight: 500;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  visibility: hidden;
  z-index: var(--z-tooltip);
  transition: opacity 0.12s ease;
}
.sidebar-collapsed .sidebar-link:hover::after,
.sidebar-collapsed .sidebar-link:focus-visible::after { opacity: 1; visibility: visible; }

/* Small screens: the toggle opens the sidebar above the content */
.sidebar-overlay-open .sidebar { box-shadow: var(--shadow-lg); }

@media (prefers-reduced-motion: reduce) {
  .sidebar, .app-main, .sidebar-toggle-icon, .sidebar-link::after { transition: none; }
}

.app-main {
  margin-left: var(--sidebar-offset);
  transition: margin-left 0.2s ease;
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
.topbar-actions { display: flex; align-items: center; gap: var(--space-3); margin-left: auto; }

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--space-8);
}

/* ---- Page chrome ---- */
.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: var(--font-3xl);
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: var(--space-2);
  letter-spacing: -0.02em;
}

.page-header p {
  color: var(--color-text-muted);
  font-size: var(--font-sm);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-6);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: var(--font-xs);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: var(--font-3xl);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

.stat-card.warning .stat-value {
  color: var(--color-warning);
}

.stat-card.success .stat-value {
  color: var(--color-success);
}

.stat-card.danger .stat-value {
  color: var(--color-danger);
}

.stat-card.info .stat-value {
  color: var(--color-info);
}

.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-6);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  /* spacing only: no divider, so the header doesn't get both a rule and a gap */
  margin-bottom: var(--space-4);
}

.card-title {
  font-size: var(--font-lg);
  font-weight: 600;
  color: var(--color-text);
}

.table-container {
  overflow-x: auto;
}

/* A table directly inside a card sits flush with the card edges so the header row spans the full width */
.card > .table-container {
  margin-left: calc(var(--space-6) * -1);
  margin-right: calc(var(--space-6) * -1);
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
}

th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-weight: 600;
  color: var(--color-text-muted);
  font-size: var(--font-xs);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

td {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: var(--font-sm);
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--color-surface-hover);
}

.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--font-xs);
  font-weight: 600;
  text-transform: uppercase; /* kept: the app's badges are deliberately upper case */
  letter-spacing: 0.025em;
}

.badge.success {
  background: var(--color-success-soft);
  color: var(--color-success-text);
}

.badge.warning {
  background: var(--color-warning-soft);
  color: var(--color-warning-text);
}

.badge.danger {
  background: var(--color-danger-soft);
  color: var(--color-danger-text);
}

.badge.info {
  background: var(--color-info-soft);
  color: var(--color-info-text);
}

.badge.increasing {
  background: var(--color-success-soft);
  color: var(--color-success-text);
}

.badge.decreasing {
  background: var(--color-danger-soft);
  color: var(--color-danger-text);
}

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.badge.high {
  background: var(--color-danger-soft);
  color: var(--color-danger-text);
}

.badge.medium {
  background: var(--color-warning-soft);
  color: var(--color-warning-text);
}

.badge.low {
  background: var(--color-info-soft);
  color: var(--color-info-text);
}

.loading {
  text-align: center;
  padding: var(--space-12);
  color: var(--color-text-muted);
  font-size: var(--font-sm);
}

.error {
  background: #fef2f2;
  border: 1px solid var(--color-danger-soft);
  color: var(--color-danger-text);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--font-sm);
}
</style>
