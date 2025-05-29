import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/auth/Login.vue'; 
import ProjectList from '@/views/project/ProjectList.vue'; // Import ProjectList

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login 
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
    path: '/projects', // Add projects route
    name: 'Projects',
    component: ProjectList,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/data',
    name: 'ProjectDataUpload', 
    component: () => import('@/views/data/DataUpload.vue'), // Assuming DataUpload.vue is in @/views/data/
    props: true, 
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/data-list',
    name: 'ProjectDataList',
    component: () => import('@/views/data/DataList.vue'), // Assuming DataList.vue is in @/views/data/
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/data/upload', // Keep the generic upload if it's still used, or remove if all uploads are project-specific
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
