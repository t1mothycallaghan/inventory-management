<template>
  <h1>Good morning</h1>
  <p class="lead">Here is what is happening across your projects.</p>
  <div class="stats">
    <div v-for="s in stats" :key="s.label" class="stat">
      <div class="stat-label">{{ s.label }}</div>
      <div class="stat-value">{{ s.value }}</div>
    </div>
  </div>
  <div class="panel">
    <h2>Recent activity</h2>
    <ul class="activity">
      <li v-for="a in activity" :key="a.id"><strong>{{ a.who }}</strong> {{ a.what }}</li>
    </ul>
  </div>
</template>

<script setup>
const stats = [
  { label: 'Open tasks', value: 42 },
  { label: 'Completed this week', value: 17 },
  { label: 'Blocked', value: 3 }
]
const activity = [
  { id: 1, who: 'Ana', what: 'closed "Fix login redirect"' },
  { id: 2, who: 'Raj', what: 'moved "Billing page" to Review' },
  { id: 3, who: 'Mei', what: 'commented on "Q3 roadmap"' }
]
</script>

<style scoped>
.stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px; }
.stat { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 17px; }
.stat-label { font-size: 13px; color: #6b7280; margin-bottom: 7px; }
.stat-value { font-size: 29px; font-weight: 700; }
.activity { margin: 0; padding-left: 17px; }
.activity li { padding: 5px 0; font-size: 14px; color: #374151; }
</style>
