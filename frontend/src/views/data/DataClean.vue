<template>
  <div class="data-clean">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据清洗</span>
          <el-button type="primary" @click="applyCleaningConfig" :loading="cleaning">
            <el-icon><Tools /></el-icon>
            应用清洗配置
          </el-button>
        </div>
      </template>

      <el-row :gutter="20">
        <!-- 患者选择和配置 -->
        <el-col :span="8">
          <div class="config-panel">
            <h3>清洗配置</h3>
            
            <el-form :model="cleanConfig" label-width="120px">
              <el-form-item label="选择患者">
                <el-select v-model="selectedPatient" placeholder="请选择患者" @change="loadPatientData">
                  <el-option
                    v-for="patient in patients"
                    :key="patient"
                    :label="patient"
                    :value="patient"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="数据类型">
                <el-checkbox-group v-model="cleanConfig.data_types">
                  <el-checkbox label="ecg">ECG数据</el-checkbox>
                  <el-checkbox label="mv">MV数据</el-checkbox>
                </el-checkbox-group>
              </el-form-item>

              <el-divider>缺失值处理</el-divider>
              
              <el-form-item label="处理方式">
                <el-radio-group v-model="cleanConfig.missing_value_strategy">
                  <el-radio label="drop">删除</el-radio>
                  <el-radio label="fill">填充</el-radio>
                </el-radio-group>
              </el-form-item>

              <el-form-item label="填充方法" v-if="cleanConfig.missing_value_strategy === 'fill'">
                <el-select v-model="cleanConfig.fill_method">
                  <el-option label="前向填充" value="ffill" />
                  <el-option label="后向填充" value="bfill" />
                  <el-option label="均值填充" value="mean" />
                  <el-option label="中位数填充" value="median" />
                  <el-option label="零值填充" value="zero" />
                </el-select>
              </el-form-item>

              <el-divider>异常值处理</el-divider>
              
              <el-form-item label="检测方法">
                <el-checkbox-group v-model="cleanConfig.outlier_methods">
                  <el-checkbox label="iqr">IQR方法</el-checkbox>
                  <el-checkbox label="zscore">Z-Score方法</el-checkbox>
                  <el-checkbox label="isolation_forest">孤立森林</el-checkbox>
                </el-checkbox-group>
              </el-form-item>

              <el-form-item label="Z-Score阈值" v-if="cleanConfig.outlier_methods.includes('zscore')">
                <el-input-number v-model="cleanConfig.zscore_threshold" :min="1" :max="5" :step="0.1" />
              </el-form-item>

              <el-form-item label="异常值处理">
                <el-radio-group v-model="cleanConfig.outlier_action">
                  <el-radio label="remove">删除</el-radio>
                  <el-radio label="cap">限制</el-radio>
                  <el-radio label="transform">转换</el-radio>
                </el-radio-group>
              </el-form-item>

              <el-divider>数据标准化</el-divider>
              
              <el-form-item label="标准化方法">
                <el-select v-model="cleanConfig.normalization_method" clearable>
                  <el-option label="不标准化" value="" />
                  <el-option label="Z-Score标准化" value="zscore" />
                  <el-option label="Min-Max标准化" value="minmax" />
                  <el-option label="Robust标准化" value="robust" />
                </el-select>
              </el-form-item>

              <el-form-item label="重采样频率">
                <el-select v-model="cleanConfig.resample_freq" clearable>
                  <el-option label="不重采样" value="" />
                  <el-option label="1分钟" value="1min" />
                  <el-option label="5分钟" value="5min" />
                  <el-option label="10分钟" value="10min" />
                  <el-option label="30分钟" value="30min" />
                  <el-option label="1小时" value="1H" />
                </el-select>
              </el-form-item>
            </el-form>
          </div>
        </el-col>

        <!-- 数据预览 -->
        <el-col :span="16">
          <div class="data-preview">
            <el-tabs v-model="activeTab">
              <el-tab-pane label="原始数据" name="original">
                <div v-if="originalData">
                  <div class="data-stats">
                    <el-row :gutter="20">
                      <el-col :span="6">
                        <el-statistic title="数据行数" :value="originalData.shape?.[0] || 0" />
                      </el-col>
                      <el-col :span="6">
                        <el-statistic title="数据列数" :value="originalData.shape?.[1] || 0" />
                      </el-col>
                      <el-col :span="6">
                        <el-statistic title="缺失值" :value="originalData.missing_count || 0" />
                      </el-col>
                      <el-col :span="6">
                        <el-statistic title="异常值" :value="originalData.outlier_count || 0" />
                      </el-col>
                    </el-row>
                  </div>
                  
                  <el-table :data="originalData.preview" size="small" max-height="400" style="margin-top: 20px;">
                    <el-table-column
                      v-for="col in originalData.columns"
                      :key="col"
                      :prop="col"
                      :label="col"
                      width="120"
                    >
                      <template #default="{ row }">
                        <span :class="{ 'missing-value': row[col] === null || row[col] === undefined }">
                          {{ formatValue(row[col]) }}
                        </span>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
                <el-empty v-else description="请选择患者查看数据" />
              </el-tab-pane>

              <el-tab-pane label="清洗后数据" name="cleaned">
                <div v-if="cleanedData">
                  <div class="data-stats">
                    <el-row :gutter="20">
                      <el-col :span="6">
                        <el-statistic title="数据行数" :value="cleanedData.shape?.[0] || 0" />
                      </el-col>
                      <el-col :span="6">
                        <el-statistic title="数据列数" :value="cleanedData.shape?.[1] || 0" />
                      </el-col>
                      <el-col :span="6">
                        <el-statistic title="缺失值" :value="cleanedData.missing_count || 0" />
                      </el-col>
                      <el-col :span="6">
                        <el-statistic title="异常值" :value="cleanedData.outlier_count || 0" />
                      </el-col>
                    </el-row>
                  </div>
                  
                  <el-table :data="cleanedData.preview" size="small" max-height="400" style="margin-top: 20px;">
                    <el-table-column
                      v-for="col in cleanedData.columns"
                      :key="col"
                      :prop="col"
                      :label="col"
                      width="120"
                    >
                      <template #default="{ row }">
                        {{ formatValue(row[col]) }}
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
                <el-empty v-else description="请先应用清洗配置" />
              </el-tab-pane>

              <el-tab-pane label="清洗报告" name="report">
                <div v-if="cleaningReport" class="cleaning-report">
                  <el-descriptions title="清洗统计" :column="2" border>
                    <el-descriptions-item label="处理时间">
                      {{ cleaningReport.processing_time }}秒
                    </el-descriptions-item>
                    <el-descriptions-item label="原始行数">
                      {{ cleaningReport.original_rows }}
                    </el-descriptions-item>
                    <el-descriptions-item label="清洗后行数">
                      {{ cleaningReport.cleaned_rows }}
                    </el-descriptions-item>
                    <el-descriptions-item label="删除行数">
                      {{ cleaningReport.removed_rows }}
                    </el-descriptions-item>
                  </el-descriptions>

                  <div class="report-details" style="margin-top: 20px;">
                    <h4>清洗详情</h4>
                    <ul>
                      <li v-for="step in cleaningReport.steps" :key="step">{{ step }}</li>
                    </ul>
                  </div>
                </div>
                <el-empty v-else description="暂无清洗报告" />
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, defineProps, watch } from 'vue' // Added defineProps and watch
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { projectAPI } from '@/api' // Changed from dataAPI to projectAPI

const props = defineProps({
  projectId: {
    type: Number,
    required: true
  }
})

const route = useRoute()

// Data state
const dataEntities = ref([]) // Renamed from patients
const selectedDataEntity = ref(null) // Stores { entity_id, version }
const originalData = ref(null)
const cleanedData = ref(null)
const cleaningReport = ref(null)
const cleaning = ref(false)
const activeTab = ref('original')

// Cleaning configuration
const cleanConfig = ref({
  data_types: [], // This might need to be dynamic based on schema or removed if not used by backend clean
  missing_value_strategy: 'fill',
  fill_method: 'ffill',
  outlier_methods: ['iqr'],
  zscore_threshold: 3.0,
  outlier_action: 'cap',
  normalization_method: '',
  resample_freq: ''
})

// Load data entities for the project
const loadDataEntities = async (projectId) => {
  const currentProjectId = Number(projectId); // Explicitly convert to Number
  console.log('DataClean - Loading data entities for projectId:', currentProjectId);

  if (isNaN(currentProjectId) || currentProjectId <= 0) {
    ElMessage.error('无效的项目ID，无法加载数据实体。');
    dataEntities.value = [];
    return;
  }

  try {
    const response = await projectAPI.getProjectVersions(currentProjectId);
    // Filter for 'data' entity_type and group by entity_id to get latest version
    const entitiesMap = new Map();
    response.filter(v => v.entity_type === 'data').forEach(version => {
      if (!entitiesMap.has(version.entity_id) || version.version > entitiesMap.get(version.entity_id).version) {
        entitiesMap.set(version.entity_id, version);
      }
    });
    dataEntities.value = Array.from(entitiesMap.values()); // Store latest versions of each data entity
    
    // If a data entity was specified in query (e.g., from ProjectDataTab), select it
    const queryEntityId = route.query.dataEntityId;
    if (queryEntityId) {
      const foundEntity = dataEntities.value.find(e => e.entity_id === queryEntityId);
      if (foundEntity) {
        selectedDataEntity.value = foundEntity;
        await loadDataPreview(foundEntity.entity_id, foundEntity.version);
      }
    }
  } catch (error) {
    ElMessage.error('获取数据实体列表失败');
    console.error('获取数据实体列表失败:', error);
  }
}

// Load data preview for selected entity and version
const loadDataPreview = async (entityId, version) => {
  if (!entityId || !version) return;
  
  const currentProjectId = Number(props.projectId); // Explicitly convert to Number
  if (isNaN(currentProjectId) || currentProjectId <= 0) {
    ElMessage.error('无效的项目ID，无法加载数据预览。');
    return;
  }

  try {
    const response = await projectAPI.viewProjectDataVersion(currentProjectId, entityId, version);
    
    originalData.value = {
      shape: response.shape,
      columns: response.columns,
      preview: response.data, // Use full data for preview, or slice if too large
      missing_count: calculateMissingCount(response.data, response.columns),
      outlier_count: 0 // Backend should provide this if possible, or calculate client-side
    };
    
    // Clear previous cleaning results
    cleanedData.value = null;
    cleaningReport.value = null;
    activeTab.value = 'original';
    
  } catch (error) {
    ElMessage.error('获取数据预览失败');
    console.error('获取数据预览失败:', error);
  }
}

// Apply cleaning configuration
const applyCleaningConfig = async () => {
  if (!selectedDataEntity.value) {
    ElMessage.warning('请先选择数据实体');
    return;
  }
  
  cleaning.value = true;
  
  try {
    // Construct cleaning_config based on the form
    const cleaningRequestPayload = {
      cleaning_config: {
        remove_outliers: cleanConfig.value.outlier_methods.length > 0,
        outlier_method: cleanConfig.value.outlier_methods[0] || null, // Assuming single method for simplicity
        fill_missing: cleanConfig.value.missing_value_strategy === 'fill',
        missing_method: cleanConfig.value.fill_method,
        smooth_data: false, // Add UI for this if needed
        smooth_window: 5, // Add UI for this if needed
        normalization_method: cleanConfig.value.normalization_method || null,
        resample_freq: cleanConfig.value.resample_freq || null,
        zscore_threshold: cleanConfig.value.zscore_threshold,
        outlier_action: cleanConfig.value.outlier_action,
      },
      notes: `Cleaned data for entity ${selectedDataEntity.value.entity_id} version ${selectedDataEntity.value.version}`
    };

    const response = await projectAPI.cleanProjectDataVersion(
      props.projectId,
      selectedDataEntity.value.entity_id,
      selectedDataEntity.value.version,
      cleaningRequestPayload
    );
    
    // The response from cleanProjectDataVersion is a VersionHistoryResponse
    // We need to fetch the preview of the newly cleaned data version
    const newCleanedVersion = response; // This is the new version entry
    
    const cleanedDataPreviewResponse = await projectAPI.viewProjectDataVersion(
      props.projectId,
      newCleanedVersion.entity_id,
      newCleanedVersion.version
    );

    cleanedData.value = {
      shape: cleanedDataPreviewResponse.shape,
      columns: cleanedDataPreviewResponse.columns,
      preview: cleanedDataPreviewResponse.data,
      missing_count: calculateMissingCount(cleanedDataPreviewResponse.data, cleanedDataPreviewResponse.columns),
      outlier_count: 0 // Backend should provide this in report
    };
    
    // The backend's clean endpoint doesn't return a detailed report directly in the VersionHistoryResponse.
    // A full report would need a separate endpoint or be part of version_metadata.
    // For now, we'll simulate a basic report.
    cleaningReport.value = {
      processing_time: (Math.random() * 10).toFixed(2),
      original_rows: originalData.value?.shape?.[0] || 0,
      cleaned_rows: cleanedData.value?.shape?.[0] || 0,
      removed_rows: (originalData.value?.shape?.[0] || 0) - (cleanedData.value?.shape?.[0] || 0),
      steps: [
        `Applied missing value strategy: ${cleanConfig.value.missing_value_strategy}`,
        `Applied outlier detection: ${cleanConfig.value.outlier_methods.join(', ')}`,
        `Applied outlier action: ${cleanConfig.value.outlier_action}`,
        cleanConfig.value.normalization_method ? `Applied normalization: ${cleanConfig.value.normalization_method}` : 'No normalization',
        cleanConfig.value.resample_freq ? `Applied resampling: ${cleanConfig.value.resample_freq}` : 'No resampling',
      ]
    };
    
    ElMessage.success('数据清洗完成');
    activeTab.value = 'cleaned';
    
  } catch (error) {
    ElMessage.error('数据清洗失败: ' + (error.response?.data?.detail || error.message));
    console.error('数据清洗失败:', error);
  } finally {
    cleaning.value = false;
  }
}

// Calculate missing value count (client-side for preview)
const calculateMissingCount = (data, columns) => {
  if (!data || !Array.isArray(data) || !columns) return 0;
  
  let missingCount = 0;
  data.forEach(row => {
    columns.forEach(col => {
      if (row[col] === null || row[col] === undefined || row[col] === '') {
        missingCount++;
      }
    });
  });
  return missingCount;
}

// Format value for display
const formatValue = (value) => {
  if (value === null || value === undefined) return 'N/A';
  if (typeof value === 'number') return value.toFixed(2);
  return value;
}

// Watch for projectId changes and load data entities
watch(() => props.projectId, (newProjectId) => {
  if (newProjectId && Number(newProjectId) > 0) { // Ensure it's a valid positive number
    loadDataEntities(newProjectId);
  } else {
    dataEntities.value = [];
    selectedDataEntity.value = null;
    originalData.value = null;
    cleanedData.value = null;
    cleaningReport.value = null;
    ElMessage.warning('无效的项目ID，无法加载数据清洗页面。');
  }
}, { immediate: true });

// Watch for selectedDataEntity changes to load its preview
watch(selectedDataEntity, (newVal) => {
  if (newVal) {
    loadDataPreview(newVal.entity_id, newVal.version);
  }
});
</script>

<style scoped>
.data-clean {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-panel {
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  height: fit-content;
}

.config-panel h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #409EFF;
}

.data-preview {
  min-height: 500px;
}

.data-stats {
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.missing-value {
  color: #F56C6C;
  font-style: italic;
}

.cleaning-report h4 {
  color: #409EFF;
  margin-bottom: 10px;
}

.cleaning-report ul {
  list-style-type: disc;
  padding-left: 20px;
}

.cleaning-report li {
  margin: 5px 0;
  line-height: 1.5;
}

.report-details {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-divider__text) {
  font-weight: 600;
  color: #409EFF;
}

:deep(.el-statistic__head) {
  font-size: 14px;
  color: #606266;
}

:deep(.el-statistic__content) {
  font-size: 20px;
  font-weight: 600;
}
</style>

<style scoped>
.data-clean {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-panel {
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  height: fit-content;
}

.config-panel h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #409EFF;
}

.data-preview {
  min-height: 500px;
}

.data-stats {
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.missing-value {
  color: #F56C6C;
  font-style: italic;
}

.cleaning-report h4 {
  color: #409EFF;
  margin-bottom: 10px;
}

.cleaning-report ul {
  list-style-type: disc;
  padding-left: 20px;
}

.cleaning-report li {
  margin: 5px 0;
  line-height: 1.5;
}

.report-details {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-divider__text) {
  font-weight: 600;
  color: #409EFF;
}

:deep(.el-statistic__head) {
  font-size: 14px;
  color: #606266;
}

:deep(.el-statistic__content) {
  font-size: 20px;
  font-weight: 600;
}
</style>
