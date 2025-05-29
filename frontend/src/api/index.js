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
    const token = localStorage.getItem('authToken'); // Or however token is stored
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
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

// Auth API
export const authAPI = {
  loginUser: async (username, password) => {
    // FastAPI's default OAuth2PasswordRequestForm expects form data
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    // Grant_type and scope might be needed depending on exact OAuth2 setup, but often not for basic token endpoint.
    // formData.append('grant_type', 'password'); 
    // formData.append('scope', '');

    const response = await api.post('/api/v1/users/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    if (response && response.access_token) {
      localStorage.setItem('authToken', response.access_token);
    }
    return response;
  },
  getCurrentUser: () => api.get('/api/v1/users/me'),
  logoutUser: () => {
    localStorage.removeItem('authToken');
    // Add any other logout logic here, e.g., redirecting or clearing app state
  }
};


// API接口定义
export const dataAPI = {
  // 上传数据
  uploadData: (files, groupName) => {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file) // Append each file with the key 'files'
    })
    
    let url = '/api/upload' // This path seems to be /api/upload, not /api/v1 yet. Assuming it's correct as per original.
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
  getDataList: () => api.get('/api/data'), // Assuming this path is correct as per original.
  
  // 获取数据详情 (原 getPatientData)
  getDataDetails: (dataId) => api.get(`/api/data/${dataId}`), // Assuming this path is correct as per original.
  
  // 清洗数据 (原 cleanPatientData)
  cleanData: (dataId, config) => api.post(`/api/clean/${dataId}`, config), // Assuming this path is correct as per original.
  
  // 获取可视化数据 (原 getVisualizationData)
  getVisualizationData: (dataId) => api.get(`/api/visualize/${dataId}`), // Assuming this path is correct as per original.

  // 确认数据
  confirmData: (data) => api.post('/api/data/confirm', data), // Assuming this path is correct as per original.

  // 格式化数据
  formatData: (data) => api.post('/api/data/process-format', data), // Assuming this path is correct as per original.

  // 批量删除数据
  deleteDataBatch: (data) => api.post('/api/data/delete-batch', data) // Assuming this path is correct as per original.
}

export const featureAPI = {
  // 提取特征
  extractFeatures: (data) => api.post('/api/features/extract', data), // Assuming this path is correct as per original.
  
  // 获取所有特征 (原 getFeatures)
  getAllFeatures: () => api.get('/api/features'), // Assuming this path is correct as per original.

  // 获取特定数据ID的特征
  getFeaturesForDataId: (dataId) => api.get(`/api/features/${dataId}`) // Assuming this path is correct as per original.
}

export const mlAPI = {
  // 训练模型
  trainModel: (data) => api.post('/api/ml/train', data), // Assuming this path is correct as per original.
  
  // 预测
  predict: (data) => api.post('/api/ml/predict', data), // Assuming this path is correct as per original.
  
  // 获取模型列表
  getModels: () => api.get('/api/ml/models'), // Assuming this path is correct as per original.

  // 获取模型训练历史
  getTrainingHistory: (modelId) => api.get(`/api/ml/models/${modelId}/history`) // Assuming this path is correct as per original.
}

export const schemaAPI = {
  // 创建数据模式
  createSchema: (data) => api.post('/api/v1/schemas', data),
  
  // 获取所有数据模式
  getSchemas: () => api.get('/api/v1/schemas'),
  
  // 获取特定数据模式
  getSchema: (schemaId) => api.get(`/api/v1/schemas/${schemaId}`),
  
  // 更新数据模式
  updateSchema: (schemaId, data) => api.put(`/api/v1/schemas/${schemaId}`, data),
  
  // 删除数据模式
  deleteSchema: (schemaId) => api.delete(`/api/v1/schemas/${schemaId}`)
}

export const projectAPI = {
  createProject: (projectData) => api.post('/api/v1/projects/', projectData),
  getProjects: () => api.get('/api/v1/projects/'),
  getProjectDetails: (projectId) => api.get(`/api/v1/projects/${projectId}`),
  updateProject: (projectId, projectUpdateData) => api.put(`/api/v1/projects/${projectId}`, projectUpdateData),
  deleteProject: (projectId) => api.delete(`/api/v1/projects/${projectId}`),

  // Project-specific data and model operations
  uploadProjectData: (projectId, formData) => api.post(`/api/v1/projects/${projectId}/data/upload`, formData, {
    // Axios will set Content-Type to multipart/form-data automatically for FormData
  }),
  viewProjectDataVersion: (projectId, dataEntityId, versionNumber, page = 1, pageSize = 10) => 
    api.get(`/api/v1/projects/${projectId}/data/${dataEntityId}/versions/${versionNumber}/view?page=${page}&page_size=${pageSize}`),
  cleanProjectDataVersion: (projectId, dataEntityId, versionNumber, cleaningRequest) => 
    api.post(`/api/v1/projects/${projectId}/data/${dataEntityId}/versions/${versionNumber}/clean`, cleaningRequest),
  extractProjectFeatures: (projectId, featureRequest) => 
    api.post(`/api/v1/projects/${projectId}/features/extract`, featureRequest),
  trainProjectModel: (projectId, trainRequest) => 
    api.post(`/api/v1/projects/${projectId}/models/train`, trainRequest),
  predictWithProjectModel: (projectId, predictRequest) => 
    api.post(`/api/v1/projects/${projectId}/models/predict`, predictRequest),
  runMLPipeline: (projectId, pipelineRequest) => 
    api.post(`/api/v1/projects/${projectId}/pipeline/run`, pipelineRequest),
  rollbackProjectDataVersion: (projectId, dataEntityId, sourceVersionNumber, rollbackRequest) => 
    api.post(`/api/v1/projects/${projectId}/data/${dataEntityId}/versions/${sourceVersionNumber}/rollback`, rollbackRequest),
  getProjectVersions: (projectId, skip = 0, limit = 100) => 
    api.get(`/api/v1/projects/${projectId}/versions?skip=${skip}&limit=${limit}`),
};

export default api
