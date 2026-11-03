<template>
  <div class="overlay" @click.self="$emit('close')">
    <div class="dialog">
      <h2>New project</h2>
      <p>Project creation is not wired up in this demo.</p>
      <button class="btn" @click="$emit('close')">Close</button>
    </div>
  </div>
</template>

<script setup>
defineEmits(['close'])
</script>

<style scoped>
.overlay { position: fixed; inset: 0; background: rgba(17, 24, 39, 0.45); display: grid; place-items: center; z-index: 20; }
.dialog { background: #fff; border-radius: 11px; padding: 26px; width: 420px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2); }
.dialog h2 { margin: 0 0 8px; font-size: 19px; }
.dialog p { color: #6b7280; font-size: 14px; margin: 0 0 18px; }
</style>
