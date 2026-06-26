<template>
  <div class="admin-layout">
    <Sidebar />
    <div class="admin-main">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import Sidebar from "@/components/Sidebar.vue"
</script>

<style scoped>
.admin-layout { display: flex; min-height: 100vh; }
.admin-main {
  flex: 1;
  margin-left: 240px;
  padding: 0;
  min-height: 100vh;
  background: var(--admin-bg);
}
</style>
