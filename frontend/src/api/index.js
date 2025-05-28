import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 可以在这里添加token等认证信息
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// API接口定义
export const dataAPI = {
  // 上传数据
  uploadData: (files, groupName) => {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file) // Append each file with the key 'files'
    })
    
    let url = '/api/upload'
    const params = new URLSearchParams();
    if (groupName) {
      params.append('group_name', groupName);
    }
    
    const queryString = params.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
    
    return api.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 获取数据列表 (原 getPatients)
  getDataList: () => api.get('/api/data'),
  
  // 获取数据详情 (原 getPatientData)
  getDataDetails: (dataId) => api.get(`/api/data/${dataId}`),
  
  // 清洗数据 (原 cleanPatientData)
  cleanData: (dataId, config) => api.post(`/api/clean/${dataId}`, config),
  
  // 获取可视化数据 (原 getVisualizationData)
  getVisualizationData: (dataId) => api.get(`/api/visualize/${dataId}`),

  // 确认数据
  confirmData: (data) => api.post('/api/data/confirm', data),

  // 格式化数据
  formatData: (data) => api.post('/api/data/process-format', data),

  // 批量删除数据
  deleteDataBatch: (data) => api.post('/api/data/delete-batch', data)
}

export const featureAPI = {
  // 提取特征
  extractFeatures: (data) => api.post('/api/features/extract', data),
  
  // 获取所有特征 (原 getFeatures)
  getAllFeatures: () => api.get('/api/features'),

  // 获取特定数据ID的特征
  getFeaturesForDataId: (dataId) => api.get(`/api/features/${dataId}`)
}

export const mlAPI = {
  // 训练模型
  trainModel: (data) => api.post('/api/ml/train', data),
  
  // 预测
  predict: (data) => api.post('/api/ml/predict', data),
  
  // 获取模型列表
  getModels: () => api.get('/api/ml/models'),

  // 获取模型训练历史
  getTrainingHistory: (modelId) => api.get(`/api/ml/models/${modelId}/history`)
}

export const schemaAPI = {
  // 创建数据模式
  createSchema: (data) => api.post('/api/schemas', data),
  
  // 获取所有数据模式
  getSchemas: () => api.get('/api/schemas'),
  
  // 获取特定数据模式
  getSchema: (schemaId) => api.get(`/api/schemas/${schemaId}`),
  
  // 更新数据模式
  updateSchema: (schemaId, data) => api.put(`/api/schemas/${schemaId}`, data),
  
  // 删除数据模式
  deleteSchema: (schemaId) => api.delete(`/api/schemas/${schemaId}`)
}

export default api
