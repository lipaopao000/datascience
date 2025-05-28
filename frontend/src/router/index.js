import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/data/upload',
    name: 'DataUpload',
    component: () => import('@/views/data/DataUpload.vue')
  },
  {
    path: '/data/list',
    name: 'DataList',
    component: () => import('@/views/data/DataList.vue')
  },
  {
    path: '/data/clean',
    name: 'DataClean',
    component: () => import('@/views/data/DataClean.vue')
  },
  {
    path: '/data/schemas',
    name: 'DataSchemaManagement',
    component: () => import('@/views/data/DataSchemaManagement.vue')
  },
  {
    path: '/analysis/visualization',
    name: 'DataVisualization',
    component: () => import('@/views/analysis/DataVisualization.vue')
  },
  {
    path: '/analysis/explorer',
    name: 'DataExplorer',
    component: () => import('@/views/analysis/DataExplorer.vue')
  },
  {
    path: '/analysis/features',
    name: 'FeatureEngineering',
    component: () => import('@/views/analysis/FeatureEngineering.vue')
  },
  {
    path: '/analysis/statistics',
    name: 'StatisticsAnalysis',
    component: () => import('@/views/analysis/StatisticsAnalysis.vue')
  },
  {
    path: '/ml/models',
    name: 'ModelManagement',
    component: () => import('@/views/ml/ModelManagement.vue')
  },
  {
    path: '/ml/train',
    name: 'ModelTraining',
    component: () => import('@/views/ml/ModelTraining.vue')
  },
  {
    path: '/ml/predict',
    name: 'ModelPrediction',
    component: () => import('@/views/ml/ModelPrediction.vue')
  },
  {
    path: '/ml/evaluation',
    name: 'ModelEvaluation',
    component: () => import('@/views/ml/ModelEvaluation.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
