<template>
  <h1>Team</h1>
  <p class="lead">People with access to this workspace.</p>
  <div class="grid">
    <div v-for="m in members" :key="m.email" class="member panel">
      <div class="initials">{{ m.name[0] }}</div>
      <div>
        <div class="name">{{ m.name }}</div>
        <div class="email">{{ m.email }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
const members = [
  { name: 'Ana Lima', email: 'ana@example.com' },
  { name: 'Raj Patel', email: 'raj@example.com' },
  { name: 'Mei Chen', email: 'mei@example.com' }
]
</script>

<style scoped>
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
.member { display: flex; gap: 13px; align-items: center; margin: 0; }
.initials { width: 40px; height: 40px; border-radius: 50%; background: #eef2ff; color: #4f46e5; display: grid; place-items: center; font-weight: 700; }
.name { font-weight: 600; font-size: 15px; }
.email { color: #6b7280; font-size: 13px; }
</style>
