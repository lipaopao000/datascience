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
    props: route => ({ projectId: Number(route.params.projectId) }),
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/data',
    name: 'ProjectDataList',
    component: () => import('@/components/ProjectDataList.vue'),
    props: route => ({ projectId: Number(route.params.projectId) }),
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/data/upload',
    name: 'ProjectDataUpload',
    component: () => import('@/views/data/DataUpload.vue'),
    props: route => ({ projectId: Number(route.params.projectId) }),
    meta: { requiresAuth: true }
  },
  // Removed ProjectDataList route as it's now a component
  {
    path: '/projects/:projectId/schemas',
    name: 'ProjectSchemas',
    component: () => import('@/views/data/DataSchemaManagement.vue'), // Re-using DataSchemaManagement.vue
    props: route => ({ projectId: Number(route.params.projectId) }),
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/data/clean',
    name: 'ProjectDataClean',
    component: () => import('@/views/data/DataClean.vue'), // Re-using DataClean.vue
    props: route => ({ projectId: Number(route.params.projectId) }),
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/analysis/explorer',
    name: 'ProjectDataExplorer',
    component: () => import('@/views/analysis/DataExplorer.vue'),
    props: route => ({ projectId: Number(route.params.projectId) }),
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/analysis/visualization',
    name: 'ProjectDataVisualization',
    component: () => import('@/views/analysis/DataVisualization.vue'),
    props: route => ({ projectId: Number(route.params.projectId) }),
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/analysis/features',
    name: 'ProjectFeatureEngineering',
    component: () => import('@/views/analysis/FeatureEngineering.vue'),
    props: route => ({ projectId: Number(route.params.projectId) }),
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/analysis/statistics',
    name: 'ProjectStatisticsAnalysis',
    component: () => import('@/views/analysis/StatisticsAnalysis.vue'),
    props: route => ({ projectId: Number(route.params.projectId) }),
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/models',
    name: 'ProjectModelManagement',
    component: () => import('@/views/ml/ModelManagement.vue'), // Re-using ModelManagement.vue
    props: route => ({ projectId: Number(route.params.projectId) }),
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/ml/train',
    name: 'ProjectModelTraining',
    component: () => import('@/views/ml/ModelTraining.vue'),
    props: route => ({ projectId: Number(route.params.projectId) }),
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/ml/predict',
    name: 'ProjectModelPrediction',
    component: () => import('@/views/ml/ModelPrediction.vue'),
    props: route => ({ projectId: Number(route.params.projectId) }),
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/ml/evaluation',
    name: 'ProjectModelEvaluation',
    component: () => import('@/views/ml/ModelEvaluation.vue'),
    props: route => ({ projectId: Number(route.params.projectId) }),
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/experiments',
    name: 'ProjectExperimentList',
    component: () => import('@/views/analysis/ExperimentRuns.vue'), // Re-using ExperimentRuns.vue
    props: route => ({ projectId: Number(route.params.projectId) }),
    meta: { requiresAuth: true }
  },
  {
    path: '/experiments/:experimentId/runs',
    name: 'ExperimentRuns',
    component: () => import('@/views/analysis/ExperimentRuns.vue'),
    props: route => ({ experimentId: Number(route.params.experimentId) }),
    meta: { requiresAuth: true }
  },
  {
    path: '/registered-models/:modelId/versions',
    name: 'ModelVersions',
    component: () => import('@/views/ml/ModelVersions.vue'),
    props: route => ({ modelId: Number(route.params.modelId) }),
    meta: { requiresAuth: true }
  },
  // Removed generic data routes as data is now project-specific
  // If these functionalities are needed globally, they should be adapted to select a project first.
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
