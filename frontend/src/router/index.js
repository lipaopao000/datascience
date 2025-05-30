import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/auth/Login.vue'; 
import Register from '@/views/auth/Register.vue'; // Import Register
import ProjectList from '@/views/project/ProjectList.vue'; // Import ProjectList

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login 
  },
  {
    path: '/register', // New registration route
    name: 'Register',
    component: Register
  },
  {
    path: '/',
    redirect: '/projects' 
  },
  {
    path: '/dashboard', 
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'), 
    meta: { requiresAuth: true } 
  },
  {
    path: '/projects',
    name: 'ProjectList',
    component: ProjectList,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId',
    name: 'ProjectDetail',
    component: () => import('@/views/project/ProjectDetail.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/data/upload',
    name: 'ProjectDataUpload',
    component: () => import('@/views/data/DataUpload.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/data-list',
    name: 'ProjectDataList',
    component: () => import('@/views/data/DataList.vue'), // Re-using DataList.vue, it needs projectId
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/schemas',
    name: 'ProjectSchemas',
    component: () => import('@/views/data/DataSchemaManagement.vue'), // Re-using DataSchemaManagement.vue
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/data/clean',
    name: 'ProjectDataClean',
    component: () => import('@/views/data/DataClean.vue'), // Re-using DataClean.vue
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/analysis/explorer',
    name: 'ProjectDataExplorer',
    component: () => import('@/views/analysis/DataExplorer.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/analysis/visualization',
    name: 'ProjectDataVisualization',
    component: () => import('@/views/analysis/DataVisualization.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/analysis/features',
    name: 'ProjectFeatureEngineering',
    component: () => import('@/views/analysis/FeatureEngineering.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/analysis/statistics',
    name: 'ProjectStatisticsAnalysis',
    component: () => import('@/views/analysis/StatisticsAnalysis.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/models',
    name: 'ProjectModelManagement',
    component: () => import('@/views/ml/ModelManagement.vue'), // Re-using ModelManagement.vue
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/ml/train',
    name: 'ProjectModelTraining',
    component: () => import('@/views/ml/ModelTraining.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/ml/predict',
    name: 'ProjectModelPrediction',
    component: () => import('@/views/ml/ModelPrediction.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/ml/evaluation',
    name: 'ProjectModelEvaluation',
    component: () => import('@/views/ml/ModelEvaluation.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/experiments/:experimentId/runs',
    name: 'ExperimentRuns',
    component: () => import('@/views/analysis/ExperimentRuns.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/registered-models/:modelId/versions',
    name: 'ModelVersions',
    component: () => import('@/views/ml/ModelVersions.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  // Keep generic routes if they are still intended to be accessible without project context,
  // but ensure their components can handle missing projectId or redirect.
  // For now, I will keep them but they might need further adjustment if they cause issues.
  {
    path: '/data/upload',
    name: 'DataUpload',
    component: () => import('@/views/data/DataUpload.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/data/list',
    name: 'DataList',
    component: () => import('@/views/data/DataList.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/data/clean',
    name: 'DataClean',
    component: () => import('@/views/data/DataClean.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/data/schemas',
    name: 'DataSchemaManagement',
    component: () => import('@/views/data/DataSchemaManagement.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/analysis/visualization',
    name: 'DataVisualization',
    component: () => import('@/views/analysis/DataVisualization.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/analysis/explorer',
    name: 'DataExplorer',
    component: () => import('@/views/analysis/DataExplorer.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/analysis/features',
    name: 'FeatureEngineering',
    component: () => import('@/views/analysis/FeatureEngineering.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/analysis/statistics',
    name: 'StatisticsAnalysis',
    component: () => import('@/views/analysis/StatisticsAnalysis.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ml/models',
    name: 'ModelManagement',
    component: () => import('@/views/ml/ModelManagement.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ml/train',
    name: 'ModelTraining',
    component: () => import('@/views/ml/ModelTraining.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ml/predict',
    name: 'ModelPrediction',
    component: () => import('@/views/ml/ModelPrediction.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ml/evaluation',
    name: 'ModelEvaluation',
    component: () => import('@/views/ml/ModelEvaluation.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('authToken');
  // Check if 'meta' and 'requiresAuth' are defined on the route
  const authRequired = to.matched.some(record => record.meta.requiresAuth);

  if (authRequired && !isAuthenticated) {
    return next('/login');
  }
  
  // If user is authenticated and tries to access login page, redirect to home/projects
  if (to.path === '/login' && isAuthenticated) {
    return next('/projects'); // Changed from '/' to '/projects'
  }

  next();
});

export default router
