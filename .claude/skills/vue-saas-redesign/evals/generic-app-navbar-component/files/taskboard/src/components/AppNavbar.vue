<template>
  <header class="navbar">
    <div class="brand">Taskboard <small>Team workspace</small></div>
    <nav class="links">
      <router-link to="/" exact-active-class="current">Home</router-link>
      <router-link to="/projects" active-class="current">Projects</router-link>
      <router-link to="/team" active-class="current">Team</router-link>
      <router-link to="/settings" active-class="current">Settings</router-link>
    </nav>
    <div class="user" @click="open = !open">
      <span class="avatar">JD</span>
      <ul v-if="open" class="menu">
        <li>Profile</li>
        <li>Sign out</li>
      </ul>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
const open = ref(false)
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 28px;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  z-index: 10;
}
.brand { font-weight: 700; font-size: 19px; color: #111827; }
.brand small { font-weight: 400; font-size: 13px; color: #6b7280; margin-left: 6px; }
.links { display: flex; gap: 6px; margin-left: 40px; }
.links a { padding: 9px 14px; color: #6b7280; text-decoration: none; border-radius: 5px; font-size: 15px; }
.links a:hover { background: #f3f4f6; color: #111827; }
.links a.current { color: #4f46e5; background: #eef2ff; }
.user { margin-left: auto; position: relative; cursor: pointer; }
.avatar { display: inline-grid; place-items: center; width: 34px; height: 34px; border-radius: 50%; background: #4f46e5; color: #fff; font-size: 13px; }
.menu { position: absolute; right: 0; top: 44px; list-style: none; margin: 0; padding: 6px; background: #fff; border: 1px solid #e5e7eb; border-radius: 7px; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1); min-width: 140px; }
.menu li { padding: 7px 11px; font-size: 14px; border-radius: 4px; }
.menu li:hover { background: #f3f4f6; }
</style>
