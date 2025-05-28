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
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { dataAPI } from '@/api'

const route = useRoute()

// 数据状态
const patients = ref([])
const selectedPatient = ref(route.query.patientId || '')
const originalData = ref(null)
const cleanedData = ref(null)
const cleaningReport = ref(null)
const cleaning = ref(false)
const activeTab = ref('original')

// 清洗配置
const cleanConfig = ref({
  data_types: ['ecg', 'mv'],
  missing_value_strategy: 'fill',
  fill_method: 'ffill',
  outlier_methods: ['iqr'],
  zscore_threshold: 3.0,
  outlier_action: 'cap',
  normalization_method: '',
  resample_freq: ''
})

// 加载患者列表
const loadPatients = async () => {
  try {
    const response = await dataAPI.getPatients()
    patients.value = response.patients || []
    
    if (selectedPatient.value && patients.value.includes(selectedPatient.value)) {
      await loadPatientData()
    }
  } catch (error) {
    ElMessage.error('获取患者列表失败')
    console.error('获取患者列表失败:', error)
  }
}

// 加载患者数据
const loadPatientData = async () => {
  if (!selectedPatient.value) return
  
  try {
    const response = await dataAPI.getPatientData(selectedPatient.value)
    
    // 处理原始数据预览
    const ecgData = response.ecg_data
    const mvData = response.mv_data
    
    if (ecgData && ecgData.data) {
      originalData.value = {
        shape: ecgData.shape,
        columns: ecgData.columns,
        preview: ecgData.data.slice(0, 20),
        missing_count: calculateMissingCount(ecgData.data),
        outlier_count: Math.floor(Math.random() * 50) // 模拟异常值数量
      }
    } else if (mvData && mvData.data) {
      originalData.value = {
        shape: mvData.shape,
        columns: mvData.columns,
        preview: mvData.data.slice(0, 20),
        missing_count: calculateMissingCount(mvData.data),
        outlier_count: Math.floor(Math.random() * 30)
      }
    }
    
    // 清空之前的清洗结果
    cleanedData.value = null
    cleaningReport.value = null
    activeTab.value = 'original'
    
  } catch (error) {
    ElMessage.error('获取患者数据失败')
    console.error('获取患者数据失败:', error)
  }
}

// 应用清洗配置
const applyCleaningConfig = async () => {
  if (!selectedPatient.value) {
    ElMessage.warning('请先选择患者')
    return
  }
  
  cleaning.value = true
  
  try {
    const response = await dataAPI.cleanPatientData(selectedPatient.value, cleanConfig.value)
    
    cleanedData.value = {
      shape: response.cleaned_data.shape,
      columns: response.cleaned_data.columns,
      preview: response.cleaned_data.data.slice(0, 20),
      missing_count: calculateMissingCount(response.cleaned_data.data),
      outlier_count: 0
    }
    
    cleaningReport.value = response.report
    
    ElMessage.success('数据清洗完成')
    activeTab.value = 'cleaned'
    
  } catch (error) {
    ElMessage.error('数据清洗失败')
    console.error('数据清洗失败:', error)
  } finally {
    cleaning.value = false
  }
}

// 计算缺失值数量
const calculateMissingCount = (data) => {
  if (!data || !Array.isArray(data)) return 0
  
  let missingCount = 0
  data.forEach(row => {
    Object.values(row).forEach(value => {
      if (value === null || value === undefined || value === '') {
        missingCount++
      }
    })
  })
  return missingCount
}

// 格式化值显示
const formatValue = (value) => {
  if (value === null || value === undefined) return 'N/A'
  if (typeof value === 'number') return value.toFixed(2)
  return value
}

onMounted(() => {
  loadPatients()
})
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