<template>
  <div class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <h3 v-if="!isCollapsed" class="sidebar-title">Ionic Liquids</h3>
      <el-button
        :icon="isCollapsed ? Expand : Fold"
        circle
        size="small"
        @click="toggleSidebar"
        class="collapse-btn"
      />
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
      >
        <el-icon class="nav-icon" :size="24">
          <component :is="item.icon" />
        </el-icon>
        <span v-if="!isCollapsed" class="nav-text">{{ item.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  Coin,
  Search,
  Grid,
  TrendCharts,
  Fold,
  Expand
} from '@element-plus/icons-vue'

const route = useRoute()
const isCollapsed = ref(false)

const menuItems = [
  {
    path: '/database',
    label: 'Database',
    icon: Coin
  },
  {
    path: '/search',
    label: 'Search',
    icon: Search
  },
  {
    path: '/generation',
    label: 'Generation',
    icon: Grid
  },
  {
    path: '/prediction',
    label: 'Prediction',
    icon: TrendCharts
  }
]

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

const isActive = (path) => {
  return route.path === path || route.path.startsWith(path + '/')
}
</script>

<script>
export default {
  name: 'Sidebar'
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 64px;
  bottom: 0;
  width: 240px;
  background: linear-gradient(180deg, #2d3748 0%, #1a202c 100%);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  transition: width 0.3s ease;
  z-index: 1000;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 80px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #f97316;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.collapse-btn {
  flex-shrink: 0;
  background-color: rgba(255, 255, 255, 0.1);
  border-color: transparent;
  color: #e2e8f0;
}

.collapse-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
  color: #ffffff;
}

.sidebar-nav {
  padding: 1rem 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 1rem 1.5rem;
  color: #e2e8f0;
  text-decoration: none;
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
  border-left: 3px solid transparent;
}

.collapsed .nav-item {
  padding: 1rem 1.75rem;
  justify-content: center;
}

.nav-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, #f97316 0%, #ea580c 100%);
  transform: scaleY(0);
  transition: transform 0.3s ease;
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: #ffffff;
}

.nav-item:hover::before {
  transform: scaleY(1);
}

.nav-item.active {
  background-color: rgba(249, 115, 22, 0.1);
  color: #f97316;
  font-weight: 500;
}

.nav-item.active::before {
  transform: scaleY(1);
}

.nav-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
}

.nav-text {
  margin-left: 1rem;
  font-size: 1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}


.sidebar:not(.collapsed) .nav-text {
  opacity: 1;
  transition: opacity 0.3s ease 0.1s;
}

.sidebar.collapsed .nav-text {
  opacity: 0;
  transition: opacity 0.1s ease;
}


@media (max-width: 768px) {
  .sidebar {
    width: 80px;
  }

  .sidebar.collapsed {
    width: 0;
  }

  .sidebar-title {
    display: none;
  }

  .nav-item {
    padding: 1rem;
    justify-content: center;
  }

  .nav-text {
    display: none;
  }
}
</style>
