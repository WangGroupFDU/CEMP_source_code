<template>
  <div id="app">
    <NavBar />
    <Sidebar />
    <div class="main-content with-sidebar">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import NavBar from '@/components/NavBar.vue'
import Sidebar from '@/components/Sidebar.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    sans-serif;
  background-color: #f8fafc;
  color: #1a202c;
}

#app {
  min-height: 100vh;
}

.main-content {
  margin-top: 64px;
  transition: margin-left 0.3s ease;
}

.main-content.with-sidebar {
  margin-left: 240px;
  padding: 24px;
}


@media (max-width: 768px) {
  .main-content.with-sidebar {
    margin-left: 80px;
    padding: 16px;
  }
}


.el-button--primary {
  background-color: #f97316;
  border-color: #f97316;
}

.el-button--primary:hover,
.el-button--primary:focus {
  background-color: #ea580c;
  border-color: #ea580c;
}

.el-button--success {
  background-color: #10b981;
  border-color: #10b981;
}

.el-button--success:hover,
.el-button--success:focus {
  background-color: #059669;
  border-color: #059669;
}
</style>
