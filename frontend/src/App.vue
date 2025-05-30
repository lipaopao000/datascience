<template>
  <div id="app">
    <el-container class="layout-container">
      <!-- 侧边栏 -->
      <el-aside :width="!isMobile ? (isSidebarOpen ? '250px' : '64px') : undefined" class="sidebar" :class="{ 'is-open': isSidebarOpen }">
        <div class="logo">
          <h2 v-if="isSidebarOpen">{{ $t('app.title') }}</h2>
          <h2 v-else>{{ $t('app.shortTitle') }}</h2>
        </div>
        <el-menu
          :default-active="$route.path"
          router
          class="sidebar-menu"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          :collapse="!isSidebarOpen"
          :collapse-transition="false"
        >
          <el-menu-item index="/dashboard">
            <el-icon><House /></el-icon>
            <span>{{ $t('app.dashboard') }}</span>
          </el-menu-item>

          <el-menu-item index="/projects">
            <el-icon><Folder /></el-icon>
            <span>{{ $t('app.projectManagement') }}</span>
          </el-menu-item>
          
          <el-sub-menu index="data-management">
            <template #title>
              <el-icon><Document /></el-icon>
              <span>{{ $t('app.dataManagement') }}</span>
            </template>
            <el-menu-item :index="getProjectScopedPath('ProjectDataUpload')" @click="navigateToProjectScopedPage('ProjectDataUpload')">{{ $t('app.dataImport') }}</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectDataList')" @click="navigateToProjectScopedPage('ProjectDataList')">{{ $t('app.dataList') }}</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectSchemas')" @click="navigateToProjectScopedPage('ProjectSchemas')">{{ $t('app.dataSchemaManagement') }}</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectDataClean')" @click="navigateToProjectScopedPage('ProjectDataClean')">{{ $t('app.dataClean') }}</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="data-analysis">
            <template #title>
              <el-icon><TrendCharts /></el-icon>
              <span>{{ $t('app.dataAnalysis') }}</span>
            </template>
            <el-menu-item :index="getProjectScopedPath('ProjectDataExplorer')" @click="navigateToProjectScopedPage('ProjectDataExplorer')">{{ $t('app.dataExplorerLab') }}</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectDataVisualization')" @click="navigateToProjectScopedPage('ProjectDataVisualization')">{{ $t('app.dataVisualization') }}</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectFeatureEngineering')" @click="navigateToProjectScopedPage('ProjectFeatureEngineering')">{{ $t('app.featureEngineering') }}</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectStatisticsAnalysis')" @click="navigateToProjectScopedPage('ProjectStatisticsAnalysis')">{{ $t('app.statisticsAnalysis') }}</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="machine-learning">
            <template #title>
              <el-icon><DataAnalysis /></el-icon>
              <span>{{ $t('app.machineLearning') }}</span>
            </template>
            <el-menu-item :index="getProjectScopedPath('ProjectModelManagement')" @click="navigateToProjectScopedPage('ProjectModelManagement')">{{ $t('app.modelManagement') }}</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectModelTraining')" @click="navigateToProjectScopedPage('ProjectModelTraining')">{{ $t('app.modelTraining') }}</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectModelPrediction')" @click="navigateToProjectScopedPage('ProjectModelPrediction')">{{ $t('app.modelPrediction') }}</el-menu-item>
            <el-menu-item :index="getProjectScopedPath('ProjectModelEvaluation')" @click="navigateToProjectScopedPage('ProjectModelEvaluation')">{{ $t('app.modelEvaluation') }}</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>
      
      <!-- Overlay for mobile -->
      <div v-if="isSidebarOpen && isMobile" class="sidebar-overlay" @click="toggleSidebar"></div>

      <!-- 主内容区 -->
      <el-container>
        <!-- 顶部导航 -->
        <el-header class="header">
          <div class="header-content">
            <el-button 
              class="sidebar-toggle-button" 
              :icon="isSidebarOpen ? Fold : Expand" 
              @click="toggleSidebar" 
              text 
              bg 
              size="large"
            />
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/dashboard' }">{{ $t('app.home') }}</el-breadcrumb-item>
              <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path" :to="{ path: item.path }">
                {{ item.name }}
              </el-breadcrumb-item>
            </el-breadcrumb>
            
            <div class="header-actions">
              <el-button type="primary" @click="refreshData" v-if="isAuthenticated">
                <el-icon><Refresh /></el-icon>
                {{ $t('app.refresh') }}
              </el-button>
              <el-button type="danger" @click="handleLogout" v-if="isAuthenticated">
                <el-icon><SwitchButton /></el-icon>
                {{ $t('app.logout') }}
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
import { computed, ref, watchEffect, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { authAPI } from '@/api';
import { Expand, Fold } from '@element-plus/icons-vue';
import { useI18n } from 'vue-i18n'; // Import useI18n

const route = useRoute();
const router = useRouter();
const { t } = useI18n(); // Initialize useI18n

const isAuthenticated = ref(!!localStorage.getItem('authToken'));
const isSidebarOpen = ref(true);
const isMobile = ref(false); // New ref to track mobile state

const checkScreenSize = () => {
  isMobile.value = window.innerWidth < 768;
  if (isMobile.value) {
    isSidebarOpen.value = false; // Hidden by default on mobile
  } else {
    isSidebarOpen.value = true; // Open by default on desktop
  }
  console.log('checkScreenSize: isMobile =', isMobile.value, 'isSidebarOpen =', isSidebarOpen.value, 'innerWidth =', window.innerWidth);
};

onMounted(() => {
  checkScreenSize();
  window.addEventListener('resize', checkScreenSize);
});

onUnmounted(() => {
  window.removeEventListener('resize', checkScreenSize);
});

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value;
  console.log('toggleSidebar: isSidebarOpen =', isSidebarOpen.value);
};

watchEffect(() => {
  isAuthenticated.value = !!localStorage.getItem('authToken');
});

const handleLogout = () => {
  authAPI.logoutUser();
  isAuthenticated.value = false; // Update local state
  router.push('/login');
  ElMessage.success(t('app.logoutSuccess'));
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
    ElMessage.warning(t('app.selectProjectWarning'));
    router.push({ name: 'ProjectList' }); // Redirect to project list
  }

  // Close sidebar on mobile after navigation
  if (isMobile.value) {
    isSidebarOpen.value = false;
    console.log('navigateToProjectScopedPage: Closing sidebar on mobile.');
  }
};

// 面包屑导航
const breadcrumbs = computed(() => {
  const pathMap = {
    '/dashboard': t('app.dashboard'),
    '/projects': t('app.projectManagement'),
    'ProjectDetail': t('app.projectDetail'),
    'ProjectDataUpload': t('app.dataImport'),
    'ProjectDataList': t('app.dataList'),
    'ProjectSchemas': t('app.dataSchemaManagement'),
    'ProjectDataClean': t('app.dataClean'),
    'ProjectDataExplorer': t('app.dataExplorerLab'),
    'ProjectDataVisualization': t('app.dataVisualization'),
    'ProjectFeatureEngineering': t('app.featureEngineering'),
    'ProjectStatisticsAnalysis': t('app.statisticsAnalysis'),
    'ProjectModelManagement': t('app.modelManagement'),
    'ProjectModelTraining': t('app.modelTraining'),
    'ProjectModelPrediction': t('app.modelPrediction'),
    'ProjectModelEvaluation': t('app.modelEvaluation'),
    'ExperimentRuns': t('app.experimentRuns'),
    'ModelVersions': t('app.modelVersions'),
    'ProjectExperimentList': t('app.projectExperimentList')
  };
  
  const breadcrumbItems = [];
  const matchedRoutes = router.currentRoute.value.matched;

  matchedRoutes.forEach((match, index) => {
    // Skip login/register routes from breadcrumbs
    if (match.path === '/login' || match.path === '/register') {
      return;
    }

    // Handle the dashboard route specifically to ensure it's the first and correct "Home"
    if (match.path === '/dashboard' && index === 0) {
      breadcrumbItems.push({ path: '/dashboard', name: t('app.home') });
      return;
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
          breadcrumbName = `${pathMap[match.name]} (${t('app.project')}: ${params.projectId})`;
        }
      } else if (params.experimentId && match.name === 'ExperimentRuns') {
         const resolvedRoute = router.resolve({ name: match.name, params: { experimentId: params.experimentId } });
         breadcrumbPath = resolvedRoute.path;
         breadcrumbName = `${pathMap[match.name]} (${t('app.experiment')}: ${params.experimentId})`;
      } else if (params.modelId && match.name === 'ModelVersions') {
         const resolvedRoute = router.resolve({ name: match.name, params: { modelId: params.modelId } });
         breadcrumbPath = resolvedRoute.path;
         breadcrumbName = `${pathMap[match.name]} (${t('app.model')}: ${params.modelId})`;
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
  ElMessage.success(t('app.dataRefreshed'));
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
  z-index: 1001; /* Ensure header is above sidebar and overlay */
  position: relative; /* Needed for z-index to work correctly */
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

.sidebar-toggle-button {
  display: none; /* Hidden by default, shown on small screens */
  margin-right: 15px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100%;
    z-index: 1000;
    transition: transform 0.3s ease-in-out, width 0.3s ease-in-out; /* Add width to transition */
    transform: translateX(-100%); /* Hidden by default on mobile */
    width: 0 !important; /* Start with 0 width on mobile, force it */
  }

  .sidebar.is-open {
    transform: translateX(0); /* Visible when open on mobile */
    width: 250px !important; /* Full width when open on mobile, force it */
  }

  .layout-container {
    flex-direction: column;
  }

  .el-aside {
    /* The width is now controlled by .sidebar.is-open and .sidebar directly */
    /* Remove any explicit width settings here if they conflict */
  }

  .el-container {
    width: 100%;
  }

  .header .header-content {
    justify-content: flex-start; /* Align items to start */
  }

  .header-actions {
    margin-left: auto; /* Push actions to the right */
  }

  .sidebar-toggle-button {
    display: flex; /* Show toggle button on small screens */
    align-items: center;
    justify-content: center;
  }

  .el-breadcrumb {
    display: none; /* Hide breadcrumbs on small screens to save space */
  }

  .main-content {
    padding: 10px; /* Reduce padding on mobile */
  }

  /* Ensure sidebar takes full width when open on mobile */
  .sidebar-menu:not(.el-menu--collapse) {
    width: 250px;
  }

  /* Ensure sidebar is completely hidden when closed on mobile */
  .sidebar-menu.el-menu--collapse {
    width: 0 !important; /* Force width to 0 when collapsed on mobile */
  }

  .logo h2 {
    font-size: 16px; /* Adjust font size for smaller screens */
  }
}

/* New rule for fixed toggle button on mobile */
@media (max-width: 768px) {
  .sidebar-toggle-button {
    position: fixed;
    top: 10px;
    left: 10px;
    z-index: 1002; /* Higher than sidebar and header */
    display: flex !important; /* Ensure it's always displayed */
  }
}

.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5); /* Semi-transparent black */
  z-index: 999; /* Below sidebar, above main content */
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
