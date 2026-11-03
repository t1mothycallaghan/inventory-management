<template>
  <div class="layout">
    <div class="toolbar">
      <input v-model="q" class="search" placeholder="Search projects" />
      <button class="btn primary" @click="showModal = true">New project</button>
    </div>
    <div class="split">
      <aside class="filters">
        <h3>Status</h3>
        <label v-for="s in statuses" :key="s"><input type="checkbox" /> {{ s }}</label>
      </aside>
      <div class="panel results">
        <table>
          <thead><tr><th>Name</th><th>Owner</th><th>Status</th></tr></thead>
          <tbody>
            <tr v-for="p in filtered" :key="p.id">
              <td>{{ p.name }}</td>
              <td>{{ p.owner }}</td>
              <td><span class="tag" :class="p.status">{{ p.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <ConfirmModal v-if="showModal" @close="showModal = false" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ConfirmModal from '../components/ConfirmModal.vue'

const q = ref('')
const showModal = ref(false)
const statuses = ['active', 'done', 'blocked']
const projects = [
  { id: 'p1', name: 'Website relaunch', owner: 'Ana', status: 'active' },
  { id: 'p2', name: 'Mobile app v2', owner: 'Raj', status: 'blocked' },
  { id: 'p3', name: 'Billing migration', owner: 'Mei', status: 'done' }
]
const filtered = computed(() =>
  projects.filter(p => p.name.toLowerCase().includes(q.value.toLowerCase()))
)
</script>

<style scoped>
.toolbar { position: sticky; top: 64px; z-index: 5; display: flex; gap: 10px; padding: 14px 0; background: #f9fafb; }
.search { flex: 1; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; }
.split { display: flex; gap: 18px; }
.filters { width: 200px; height: calc(100vh - 64px); position: sticky; top: 64px; padding: 14px; }
.filters h3 { font-size: 13px; text-transform: uppercase; color: #6b7280; margin: 0 0 10px; }
.filters label { display: block; padding: 5px 0; font-size: 14px; }
.results { flex: 1; }
</style>
