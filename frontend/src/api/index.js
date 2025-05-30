import axios from 'axios';
import { ElMessage } from 'element-plus';

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  response => {
    console.log('API Response (Success):', response);
    return response.data;
  },
  async error => {
    console.error('API Response (Error):', error);
    const originalRequest = error.config;

    // If the error is 401 and not already trying to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If token is already refreshing, queue the failed request
        return new Promise(resolve => {
          failedQueue.push({ resolve, reject: error => Promise.reject(error) });
        }).then(token => {
          originalRequest.headers['Authorization'] = 'Bearer ' + token;
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = localStorage.getItem('refreshToken'); // Assuming you store a refresh token
        if (!refreshToken) {
          // No refresh token, redirect to login
          ElMessage.error('会话过期，请重新登录。');
          authAPI.logoutUser(); // Clear token and redirect
          return Promise.reject(error);
        }

        // Call refresh token API
        const refreshResponse = await authAPI.refreshAuthToken(refreshToken);
        const newAuthToken = refreshResponse.access_token;
        const newRefreshToken = refreshResponse.refresh_token; // If refresh token also updates

        localStorage.setItem('authToken', newAuthToken);
        if (newRefreshToken) {
          localStorage.setItem('refreshToken', newRefreshToken);
        }

        api.defaults.headers.common['Authorization'] = 'Bearer ' + newAuthToken;
        processQueue(null, newAuthToken); // Resolve all queued requests
        
        originalRequest.headers['Authorization'] = 'Bearer ' + newAuthToken;
        return api(originalRequest); // Retry the original request
      } catch (refreshError) {
        processQueue(refreshError, null); // Reject all queued requests
        ElMessage.error('会话过期，请重新登录。');
        authAPI.logoutUser(); // Clear token and redirect
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    const message = error.response?.data?.detail || error.message || '请求失败';
    ElMessage.error(message);
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  loginUser: async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post('/api/v1/users/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    if (response && response.access_token) {
      localStorage.setItem('authToken', response.access_token);
      if (response.refresh_token) { // Assuming refresh_token is also returned
        localStorage.setItem('refreshToken', response.refresh_token);
      }
    } else {
      console.error('Login response did not contain access_token:', response);
      throw new Error('Login failed: No access token received.');
    }
    return response;
  },
  registerUser: (userData) => api.post('/api/v1/users/', userData),
  getCurrentUser: () => api.get('/api/v1/users/me'),
  logoutUser: () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('refreshToken'); // Clear refresh token too
    // Optionally redirect to login page
    // router.push('/login'); 
  },
  refreshAuthToken: (refreshToken) => {
    // This endpoint needs to exist on the backend
    return api.post('/api/v1/users/refresh_token', { refresh_token: refreshToken });
  }
};


// API接口定义 (Generic/Legacy APIs - most functionality moved to projectAPI, experimentAPI, modelRegistryAPI)
// These might be removed or re-implemented with /api/v1 prefixes if still needed for non-project-scoped operations.
export const dataAPI = {
  // Generic data upload - consider if this is still needed or if all uploads are project-scoped
  // uploadData: (files, groupName) => { /* ... */ },
  
  // Generic data list - replaced by projectAPI.getProjectVersions
  // getDataList: () => api.get('/api/v1/data'), // Example if a generic /v1/data endpoint existed
  
  // Generic data details - replaced by projectAPI.viewProjectDataVersion
  // getDataDetails: (dataId) => api.get(`/api/v1/data/${dataId}`),
  
  // Generic clean data - replaced by projectAPI.cleanProjectDataVersion
  // cleanData: (dataId, config) => api.post(`/api/v1/clean/${dataId}`, config),
  
  // Generic visualization data - needs backend /api/v1 endpoint if still used
  // getVisualizationData: (dataId) => api.get(`/api/v1/visualize/${dataId}`),

  // Generic confirm data - needs backend /api/v1 endpoint if still used
  // confirmData: (data) => api.post('/api/v1/data/confirm', data),

  // Generic format data - needs backend /api/v1 endpoint if still used
  // formatData: (data) => api.post('/api/v1/data/process-format', data),

  // Generic batch delete data - needs backend /api/v1 endpoint if still used
  // deleteDataBatch: (data) => api.post('/api/v1/data/delete-batch', data)
}

export const featureAPI = {
  // Generic feature extraction - replaced by projectAPI.extractProjectFeatures
  // extractFeatures: (data) => api.post('/api/v1/features/extract', data),
  
  // Generic get all features - needs backend /api/v1 endpoint if still used
  // getAllFeatures: () => api.get('/api/v1/features'),

  // Generic get features for data ID - needs backend /api/v1 endpoint if still used
  // getFeaturesForDataId: (dataId) => api.get(`/api/v1/features/${dataId}`)
}

export const mlAPI = {
  // Generic train model - replaced by projectAPI.trainProjectModel
  // trainModel: (data) => api.post('/api/v1/ml/train', data),
  
  // Generic predict - replaced by projectAPI.predictWithProjectModel
  // predict: (data) => api.post('/api/v1/ml/predict', data),
  
  // Generic get models list - replaced by modelRegistryAPI.getRegisteredModels
  // getModels: () => api.get('/api/v1/ml/models'),

  // Generic get training history - replaced by experimentAPI.getRunsByExperiment or modelRegistryAPI.getModelVersionsByRegisteredModel
  // getTrainingHistory: (modelId) => api.get(`/api/v1/ml/models/${modelId}/history`)
}

export const schemaAPI = {
  // 创建数据模式 (project-scoped)
  createSchema: (projectId, schemaData) => api.post(`/api/v1/projects/${projectId}/schemas`, schemaData),
  
  // 获取所有数据模式 (project-scoped)
  getSchemas: (projectId, skip = 0, limit = 100) => api.get(`/api/v1/projects/${projectId}/schemas?skip=${skip}&limit=${limit}`),
  
  // 获取特定数据模式 (project-scoped)
  getSchema: (projectId, schemaId) => api.get(`/api/v1/projects/${projectId}/schemas/${schemaId}`),
  
  // 更新数据模式 (project-scoped)
  updateSchema: (projectId, schemaId, schemaData) => api.put(`/api/v1/projects/${projectId}/schemas/${schemaId}`, schemaData),
  
  // 删除数据模式 (project-scoped)
  deleteSchema: (projectId, schemaId) => api.delete(`/api/v1/projects/${projectId}/schemas/${schemaId}`)
}

export const projectAPI = {
  createProject: (projectData) => api.post('/api/v1/projects/', projectData),
  getProjects: () => api.get('/api/v1/projects/'),
  getProject: (projectId) => api.get(`/api/v1/projects/${projectId}`), // Renamed for consistency
  updateProject: (projectId, projectUpdateData) => api.put(`/api/v1/projects/${projectId}`, projectUpdateData),
  deleteProject: (projectId) => api.delete(`/api/v1/projects/${projectId}`),

  // Project-specific data and model operations
  uploadProjectData: (projectId, formData) => api.post(`/api/v1/projects/${projectId}/data/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' } // Explicitly set for FormData
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
  getVersionsForEntity: (projectId, entityId) => 
    api.get(`/api/v1/projects/${projectId}/data/${entityId}/versions`),
  updateVersionNotes: (projectId, versionId, notesUpdate) =>
    api.patch(`/api/v1/projects/${projectId}/versions/${versionId}/notes`, notesUpdate),
  updateVersionDisplayName: (projectId, versionId, displayNameUpdate) =>
    api.patch(`/api/v1/projects/${projectId}/versions/${versionId}/display_name`, displayNameUpdate),
  
  // New API calls for project data management
  deleteProjectDataVersions: (projectId, deleteRequest) => 
    api.post(`/api/v1/projects/${projectId}/data/delete-batch`, deleteRequest),
  formatProjectData: (projectId, formatRequest) => 
    api.post(`/api/v1/projects/${projectId}/data/format`, formatRequest, {
      timeout: 120000   // 2 minutes timeout
    }),
};

export const experimentAPI = {
  createExperiment: (experimentData) => api.post('/api/v1/experiments/', experimentData),
  getExperiments: (skip = 0, limit = 100, projectId = null) => {
    let url = `/api/v1/experiments/?skip=${skip}&limit=${limit}`;
    if (projectId !== null) {
      url += `&project_id=${projectId}`;
    }
    return api.get(url);
  },
  getExperiment: (experimentId) => api.get(`/api/v1/experiments/${experimentId}`),
  startRun: (experimentId, runData) => api.post(`/api/v1/experiments/${experimentId}/runs/`, runData),
  endRun: (runId, status) => api.put(`/api/v1/runs/${runId}/end?status=${status}`),
  getRun: (runId) => api.get(`/api/v1/runs/${runId}`),
  getRunsByExperiment: (experimentId, skip = 0, limit = 100) => 
    api.get(`/api/v1/experiments/${experimentId}/runs?skip=${skip}&limit=${limit}`),
  logParameter: (runId, key, value) => api.post(`/api/v1/runs/${runId}/parameters`, { key, value }),
  getRunParameters: (runId) => api.get(`/api/v1/runs/${runId}/parameters`),
  logMetric: (runId, key, value, step = null) => api.post(`/api/v1/runs/${runId}/metrics`, { key, value, step }),
  getRunMetrics: (runId) => api.get(`/api/v1/runs/${runId}/metrics`),
  logArtifact: (runId, file, artifactPath = "", fileType = "other") => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('artifact_path', artifactPath);
    formData.append('file_type', fileType);
    return api.post(`/api/v1/runs/${runId}/artifacts`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  getRunArtifacts: (runId) => api.get(`/api/v1/runs/${runId}/artifacts`),
  downloadArtifact: (runId, artifactPath) => api.get(`/api/v1/runs/${runId}/artifacts/download?artifact_path=${encodeURIComponent(artifactPath)}`, {
    responseType: 'blob' // Important for file downloads
  }),
};

export const modelRegistryAPI = {
  createRegisteredModel: (modelData) => api.post('/api/v1/registered-models/', modelData),
  getRegisteredModels: (skip = 0, limit = 100, projectId = null) => {
    let url = `/api/v1/registered-models/?skip=${skip}&limit=${limit}`;
    if (projectId !== null) {
      url += `&project_id=${projectId}`;
    }
    return api.get(url);
  },
  getRegisteredModel: (modelId) => api.get(`/api/v1/registered-models/${modelId}`),
  updateRegisteredModel: (modelId, modelUpdateData) => api.put(`/api/v1/registered-models/${modelId}`, modelUpdateData),
  deleteRegisteredModel: (modelId) => api.delete(`/api/v1/registered-models/${modelId}`),
  createModelVersion: (registeredModelId, versionData) => api.post(`/api/v1/registered-models/${registeredModelId}/versions/`, versionData),
  getModelVersionsByRegisteredModel: (registeredModelId, skip = 0, limit = 100) => 
    api.get(`/api/v1/registered-models/${registeredModelId}/versions/?skip=${skip}&limit=${limit}`),
  getModelVersion: (versionId) => api.get(`/api/v1/model-versions/${versionId}`),
  getLatestModelVersionByName: (modelName) => api.get(`/api/v1/registered-models/${modelName}/versions/latest`),
  getSpecificModelVersionByName: (modelName, versionNumber) => api.get(`/api/v1/registered-models/${modelName}/versions/${versionNumber}`),
  transitionModelVersionStage: (versionId, newStage) => api.put(`/api/v1/model-versions/${versionId}/stage?new_stage=${newStage}`),
  deleteModelVersion: (versionId) => api.delete(`/api/v1/model-versions/${versionId}`),
};

export default api
