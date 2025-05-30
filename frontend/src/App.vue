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
          
          <el-sub-menu index="data-management">
            <template #title>
              <el-icon><Document /></el-icon>
              <span>数据管理</span>
            </template>
            <el-menu-item :index="getProjectScopedPath('ProjectDataUpload')" @click="navigateToProjectScopedPage('ProjectDataUpload')">数据导入</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectDataList')" @click="navigateToProjectScopedPage('ProjectDataList')">数据列表</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectSchemas')" @click="navigateToProjectScopedPage('ProjectSchemas')">数据模式管理</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectDataClean')" @click="navigateToProjectScopedPage('ProjectDataClean')">数据清洗</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="data-analysis">
            <template #title>
              <el-icon><TrendCharts /></el-icon>
              <span>数据分析</span>
            </template>
            <el-menu-item :index="getProjectScopedPath('ProjectDataExplorer')" @click="navigateToProjectScopedPage('ProjectDataExplorer')">数据探索实验室</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectDataVisualization')" @click="navigateToProjectScopedPage('ProjectDataVisualization')">数据可视化</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectFeatureEngineering')" @click="navigateToProjectScopedPage('ProjectFeatureEngineering')">特征工程</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectStatisticsAnalysis')" @click="navigateToProjectScopedPage('ProjectStatisticsAnalysis')">统计分析</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="machine-learning">
            <template #title>
              <el-icon><DataAnalysis /></el-icon>
              <span>机器学习</span>
            </template>
            <el-menu-item :index="getProjectScopedPath('ProjectModelManagement')" @click="navigateToProjectScopedPage('ProjectModelManagement')">模型管理</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectModelTraining')" @click="navigateToProjectScopedPage('ProjectModelTraining')">模型训练</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectModelPrediction')" @click="navigateToProjectScopedPage('ProjectModelPrediction')">模型预测</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectModelEvaluation')" @click="navigateToProjectScopedPage('ProjectModelEvaluation')">模型评估</el-menu-item>
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

const getProjectScopedPath = (routeName) => {
  const activeProjectId = parseInt(localStorage.getItem('activeProjectId')); // Parse to integer
  console.log('getProjectScopedPath - activeProjectId:', activeProjectId, 'routeName:', routeName);

  if (activeProjectId && !isNaN(activeProjectId) && activeProjectId > 0) {
    // Use router.resolve to get the full path for active highlighting
    const resolvedRoute = router.resolve({ name: routeName, params: { projectId: activeProjectId } });
    return resolvedRoute.path;
  }
  // Return a generic path or empty string if no active project,
  // so the menu item doesn't try to navigate to an invalid path for active state.
  // The @click handler will prevent actual navigation if no project is selected.
  switch (routeName) {
    case 'ProjectDataUpload': return `/projects/:projectId/data/upload`;
    case 'ProjectDataList': return `/projects/:projectId/data`; // Corrected path
    case 'ProjectSchemas': return `/projects/:projectId/schemas`;
    case 'ProjectDataClean': return `/projects/:projectId/data/clean`;
    case 'ProjectDataExplorer': return `/projects/:projectId/analysis/explorer`;
    case 'ProjectDataVisualization': return `/projects/:projectId/analysis/visualization`;
    case 'ProjectFeatureEngineering': return `/projects/:projectId/analysis/features`;
    case 'ProjectStatisticsAnalysis': return `/projects/:projectId/analysis/statistics`;
    case 'ProjectModelManagement': return `/projects/:projectId/models`;
    case 'ProjectModelTraining': return `/projects/:projectId/ml/train`;
    case 'ProjectModelPrediction': return `/projects/:projectId/ml/predict`;
    case 'ProjectModelEvaluation': return `/projects/:projectId/ml/evaluation`;
    default: return '';
  }
};

const navigateToProjectScopedPage = (routeName) => {
  const activeProjectId = parseInt(localStorage.getItem('activeProjectId')); // Ensure it's parsed as an integer
  console.log('navigateToProjectScopedPage - activeProjectId:', activeProjectId, 'routeName:', routeName);

  if (activeProjectId && !isNaN(activeProjectId) && activeProjectId > 0) { // Check for valid number
    router.push({ name: routeName, params: { projectId: activeProjectId } });
  } else {
    ElMessage.warning('Please select a project first from "项目管理" (Project Management).');
    router.push({ name: 'ProjectList' }); // Redirect to project list
  }
};

// 面包屑导航
const breadcrumbs = computed(() => {
  const pathMap = {
    '/dashboard': '仪表板',
    '/projects': '项目管理',
    'ProjectDetail': '项目详情',
    'ProjectDataUpload': '数据导入',
    'ProjectDataList': '数据列表',
    'ProjectSchemas': '数据模式管理',
    'ProjectDataClean': '数据清洗',
    'ProjectDataExplorer': '数据探索实验室',
    'ProjectDataVisualization': '数据可视化',
    'ProjectFeatureEngineering': '特征工程',
    'ProjectStatisticsAnalysis': '统计分析',
    'ProjectModelManagement': '模型管理',
    'ProjectModelTraining': '模型训练',
    'ProjectModelPrediction': '模型预测',
    'ProjectModelEvaluation': '模型评估',
    'ExperimentRuns': '实验运行详情',
    'ModelVersions': '模型版本详情',
    'ProjectExperimentList': '项目实验列表' // Add this for the new route
  };
  
  const breadcrumbItems = [];
  const matchedRoutes = router.currentRoute.value.matched;

  // Add '首页' (Home) as the first breadcrumb if the current route is not login/register
  if (route.path !== '/login' && route.path !== '/register') {
    breadcrumbItems.push({ path: '/dashboard', name: '首页' });
  }

  matchedRoutes.forEach(match => {
    // Skip the root redirect and dashboard if it's already handled by the initial '首页' push
    if (match.path === '/' || match.path === '/dashboard') {
      // If the current route is exactly /dashboard, we already added '首页', so skip.
      // If it's a child of dashboard, we still want to process the child.
      if (match.path === '/dashboard' && route.path === '/dashboard') {
        return;
      }
      // If it's the root redirect, skip it.
      if (match.path === '/') {
        return;
      }
    }

    // Only process if the route has a name and it's in our pathMap
    if (match.name && pathMap[match.name]) {
      let breadcrumbName = pathMap[match.name];
      let breadcrumbPath = match.path;

      // Handle dynamic parameters for project-scoped routes
      const params = match.params || {};
      
      if (params.projectId) {
        // For project-specific routes, ensure the path is correctly resolved
        const resolvedRoute = router.resolve({ name: match.name, params: { projectId: params.projectId } });
        breadcrumbPath = resolvedRoute.path;
        // Only append project ID to the name if it's not the ProjectDetail itself
        if (match.name !== 'ProjectDetail') {
          breadcrumbName = `${pathMap[match.name]} (项目: ${params.projectId})`;
        }
      } else if (params.experimentId && match.name === 'ExperimentRuns') {
         const resolvedRoute = router.resolve({ name: match.name, params: { experimentId: params.experimentId } });
         breadcrumbPath = resolvedRoute.path;
         breadcrumbName = `${pathMap[match.name]} (实验: ${params.experimentId})`;
      } else if (params.modelId && match.name === 'ModelVersions') {
         const resolvedRoute = router.resolve({ name: match.name, params: { modelId: params.modelId } });
         breadcrumbPath = resolvedRoute.path;
         breadcrumbName = `${pathMap[match.name]} (模型: ${params.modelId})`;
      }
      
      // Add to breadcrumbs if not a duplicate path
      if (!breadcrumbItems.some(item => item.path === breadcrumbPath)) {
        breadcrumbItems.push({
          path: breadcrumbPath,
          name: breadcrumbName
        });
      }
    }
  });
  
  return breadcrumbItems;
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
