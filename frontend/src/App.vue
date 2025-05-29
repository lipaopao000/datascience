<template>
  <div id="app">
    <el-container class="layout-container">
      <!-- 侧边栏 -->
      <el-aside width="250px" class="sidebar">
        <div class="logo">
          <h2>医疗数据分析平台</h2>
        </div>
        <el-menu
          :default-active="$route.path"
          router
          class="sidebar-menu"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/dashboard">
            <el-icon><House /></el-icon>
            <span>仪表板</span>
          </el-menu-item>

          <el-menu-item index="/projects">
            <el-icon><Folder /></el-icon>
            <span>项目管理</span>
          </el-menu-item>
          
          <el-sub-menu index="data">
            <template #title>
              <el-icon><Document /></el-icon>
              <span>数据管理</span>
            </template>
            <el-menu-item index="/data/upload">数据导入</el-menu-item>
            <el-menu-item index="/data/list">数据列表</el-menu-item>
            <el-menu-item index="/data/schemas">数据模式管理</el-menu-item>
            <el-menu-item index="/data/clean">数据清洗</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="analysis">
            <template #title>
              <el-icon><TrendCharts /></el-icon>
              <span>数据分析</span>
            </template>
            <el-menu-item index="/analysis/explorer">数据探索实验室</el-menu-item>
            <el-menu-item index="/analysis/visualization">数据可视化</el-menu-item>
            <el-menu-item index="/analysis/features">特征工程</el-menu-item>
            <el-menu-item index="/analysis/statistics">统计分析</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="ml">
            <template #title>
              <el-icon><DataAnalysis /></el-icon>
              <span>机器学习</span>
            </template>
            <el-menu-item index="/ml/models">模型管理</el-menu-item>
            <el-menu-item index="/ml/train">模型训练</el-menu-item>
            <el-menu-item index="/ml/predict">模型预测</el-menu-item>
            <el-menu-item index="/ml/evaluation">模型评估</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-container>
        <!-- 顶部导航 -->
        <el-header class="header">
          <div class="header-content">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path" :to="{ path: item.path }">
                {{ item.name }}
              </el-breadcrumb-item>
            </el-breadcrumb>
            
            <div class="header-actions">
              <el-button type="primary" @click="refreshData" v-if="isAuthenticated">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
              <el-button type="danger" @click="handleLogout" v-if="isAuthenticated">
                <el-icon><SwitchButton /></el-icon>
                Logout
              </el-button>
            </div>
          </div>
        </el-header>
        
        <!-- 主要内容 -->
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed, ref, watchEffect } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { authAPI } from '@/api'; // Assuming your api/index.js is aliased as @/api

const route = useRoute();
const router = useRouter();

// Authentication state
const isAuthenticated = ref(!!localStorage.getItem('authToken'));

watchEffect(() => {
  // This effect will re-run whenever the route changes or localStorage might change.
  // More robust solutions might use a global state manager (Pinia/Vuex)
  // or custom events after login/logout.
  isAuthenticated.value = !!localStorage.getItem('authToken');
});

const handleLogout = () => {
  authAPI.logoutUser();
  isAuthenticated.value = false; // Update local state
  router.push('/login');
  ElMessage.success('Logged out successfully!');
};

// 面包屑导航
const breadcrumbs = computed(() => {
  const pathMap = {
    '/dashboard': '仪表板',
    '/projects': '项目管理',
    '/data/upload': '数据导入',
    '/data/list': '数据列表',
    '/data/clean': '数据清洗',
    '/analysis/visualization': '数据可视化',
    '/analysis/features': '特征工程',
    '/analysis/statistics': '统计分析',
    '/ml/models': '模型管理',
    '/ml/train': '模型训练',
    '/ml/predict': '模型预测',
    '/ml/evaluation': '模型评估'
  }
  
  const pathSegments = route.path.split('/').filter(Boolean)
  const breadcrumbItems = []
  
  let currentPath = ''
  for (const segment of pathSegments) {
    currentPath += `/${segment}`
    // Ensure not to create breadcrumb for login page itself
    if (pathMap[currentPath] && currentPath !== '/dashboard' && route.path !== '/login') {
      breadcrumbItems.push({
        path: currentPath,
        name: pathMap[currentPath]
      })
    }
  }
  
  return breadcrumbItems
})

const refreshData = () => {
  ElMessage.success('数据已刷新')
  // 这里可以添加刷新逻辑
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  overflow: hidden;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #434a50;
}

.logo h2 {
  color: #fff;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.sidebar-menu {
  border: none;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
  display: flex;
  align-items: center;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.main-content {
  background-color: #f5f5f5;
  padding: 20px;
  overflow-y: auto;
}

/* 全局样式 */
:deep(.el-menu-item) {
  height: 50px;
  line-height: 50px;
}

:deep(.el-sub-menu .el-menu-item) {
  height: 45px;
  line-height: 45px;
  padding-left: 60px !important;
}
</style>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

#app {
  height: 100vh;
}
</style>
