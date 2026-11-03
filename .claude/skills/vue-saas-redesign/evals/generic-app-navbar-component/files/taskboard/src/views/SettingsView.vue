<template>
  <h1>Settings</h1>
  <p class="lead">Workspace preferences.</p>
  <form class="panel form" @submit.prevent>
    <label>Workspace name <input value="Acme Product" /></label>
    <label>Default view
      <select><option>Board</option><option>List</option></select>
    </label>
    <label class="check"><input type="checkbox" checked /> Email me a weekly summary</label>
    <button class="btn primary">Save changes</button>
  </form>
</template>

<style scoped>
.form { display: flex; flex-direction: column; gap: 16px; max-width: 480px; }
.form label { display: flex; flex-direction: column; gap: 5px; font-size: 14px; font-weight: 500; }
.form input:not([type="checkbox"]), .form select { padding: 9px 11px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; }
.form .check { flex-direction: row; align-items: center; gap: 8px; font-weight: 400; }
.form .btn { align-self: flex-start; }
</style>
