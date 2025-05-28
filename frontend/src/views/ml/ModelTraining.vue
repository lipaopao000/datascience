<template>
  <div class="model-training">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>模型训练</span>
          <el-button type="primary" @click="startTraining" :loading="training">
            <el-icon><VideoPlay /></el-icon>
            开始训练
          </el-button>
        </div>
      </template>

      <el-row :gutter="20">
        <!-- 训练配置 -->
        <el-col :span="8">
          <div class="config-panel">
            <h3>训练配置</h3>
            
            <el-form :model="trainingConfig" label-width="120px">
              <el-form-item label="模型名称">
                <el-input v-model="trainingConfig.model_name" placeholder="输入模型名称" />
              </el-form-item>

              <el-form-item label="选择数据">
                <el-select v-model="trainingConfig.data_id" placeholder="选择数据集" @change="handleDataIdChange">
                  <el-option
                    v-for="id in availableDataIds"
                    :key="id"
                    :label="id"
                    :value="id"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="算法类型">
                <el-select v-model="trainingConfig.algorithm" @change="updateAlgorithmConfig">
                  <el-option label="随机森林" value="random_forest" />
                  <el-option label="逻辑回归" value="logistic_regression" />
                  <el-option label="支持向量机" value="svm" />
                </el-select>
              </el-form-item>

              <el-form-item label="任务类型">
                <el-radio-group v-model="trainingConfig.task_type">
                  <el-radio label="classification">分类</el-radio>
                  <el-radio label="regression">回归</el-radio>
                </el-radio-group>
              </el-form-item>

              <el-form-item label="目标变量">
                <el-select v-model="trainingConfig.target_column" placeholder="选择目标变量">
                  <el-option
                    v-for="col in availableColumns"
                    :key="col"
                    :label="col"
                    :value="col"
                  />
                </el-select>
              </el-form-item>

              <el-divider>特征工程配置</el-divider>
              <el-form-item label="选择特征列">
                 <el-select v-model="columnsToAdd" multiple placeholder="添加列到特征配置表" style="width:100%">
                   <el-option
                    v-for="col in availableColumns.filter(c => c !== trainingConfig.target_column && !featureConfigTableData.find(fc => fc.columnName === c))"
                    :key="col"
                    :label="col"
                    :value="col"
                  />
                </el-select>
                <el-button @click="addSelectedColumnsToFeatureTable" style="margin-top: 5px;">添加到配置表</el-button>
              </el-form-item>

              <el-table :data="featureConfigTableData" style="width: 100%; margin-bottom: 20px;">
                <el-table-column prop="columnName" label="特征列名" />
                <el-table-column label="提取的特征类型">
                  <template #default="{ row }">
                    <el-select v-model="row.selectedFeatureTypes" multiple placeholder="选择特征类型">
                      <el-option label="基本统计" value="basic_stats" />
                      <el-option label="时域特征" value="time_domain" />
                      <el-option label="频域特征" value="frequency_domain" />
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80">
                  <template #default="{ $index }">
                    <el-button type="danger" size="small" @click="removeColumnFromFeatureTable($index)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>


              <el-divider>数据分割</el-divider>
              <el-form-item label="训练集比例">
                <el-slider
                  v-model="trainingConfig.train_ratio"
                  :min="0.5"
                  :max="0.9"
                  :step="0.05"
                  show-input
                  :format-tooltip="formatPercent"
                />
              </el-form-item>
              <el-form-item label="随机种子">
                <el-input-number v-model="trainingConfig.random_state" :min="0" :max="9999" />
              </el-form-item>

              <el-divider>算法参数</el-divider>
              <!-- Algorithm params sections remain the same -->
              <div v-if="trainingConfig.algorithm === 'random_forest'">
                <el-form-item label="树的数量">
                  <el-input-number v-model="trainingConfig.params.n_estimators" :min="10" :max="1000" />
                </el-form-item>
                <el-form-item label="最大深度">
                  <el-input-number v-model="trainingConfig.params.max_depth" :min="1" :max="50" />
                </el-form-item>
                <el-form-item label="最小分割样本">
                  <el-input-number v-model="trainingConfig.params.min_samples_split" :min="2" :max="20" />
                </el-form-item>
              </div>
              <div v-if="trainingConfig.algorithm === 'logistic_regression'">
                <el-form-item label="正则化强度">
                  <el-input-number v-model="trainingConfig.params.C" :min="0.01" :max="100" :step="0.01" />
                </el-form-item>
                <el-form-item label="最大迭代次数">
                  <el-input-number v-model="trainingConfig.params.max_iter" :min="100" :max="10000" />
                </el-form-item>
              </div>
              <div v-if="trainingConfig.algorithm === 'svm'">
                <el-form-item label="正则化参数">
                  <el-input-number v-model="trainingConfig.params.C" :min="0.01" :max="100" :step="0.01" />
                </el-form-item>
                <el-form-item label="核函数">
                  <el-select v-model="trainingConfig.params.kernel">
                    <el-option label="RBF" value="rbf" />
                    <el-option label="线性" value="linear" />
                    <el-option label="多项式" value="poly" />
                  </el-select>
                </el-form-item>
              </div>

              <el-divider>交叉验证</el-divider>
              <el-form-item label="启用交叉验证">
                <el-switch v-model="trainingConfig.cross_validation" />
              </el-form-item>
              <el-form-item label="折数" v-if="trainingConfig.cross_validation">
                <el-input-number v-model="trainingConfig.cv_folds" :min="3" :max="10" />
              </el-form-item>
            </el-form>
          </div>
        </el-col>

        <!-- Training area and results remain the same -->
        <el-col :span="16">
          <div class="training-area">
            <div v-if="training" class="training-progress">
              <h3>训练进行中...</h3>
              <el-progress :percentage="trainingProgress" :status="progressStatus" />
              <div class="progress-info">
                <p>{{ progressText }}</p>
                <p>预计剩余时间: {{ estimatedTime }}</p>
              </div>
            </div>
            <div v-if="trainingResult" class="training-result">
              <h3>训练结果</h3>
              <el-tabs v-model="activeTab">
                <el-tab-pane label="模型性能" name="performance">
                  <div class="performance-metrics">
                    <el-row :gutter="20">
                      <el-col :span="12">
                        <el-card title="训练指标">
                          <el-descriptions :column="1" border>
                            <el-descriptions-item 
                              v-for="(value, key) in trainingResult.metrics" 
                              :key="key" 
                              :label="formatMetricName(key)"
                            >
                              {{ formatMetricValue(value) }}
                            </el-descriptions-item>
                          </el-descriptions>
                        </el-card>
                      </el-col>
                    </el-row>
                  </div>
                </el-tab-pane>
                <el-tab-pane label="训练曲线" name="curves" v-if="trainingResult.training_history && trainingResult.training_history.length > 0">
                  <div ref="trainingCurveChart" style="height: 400px;"></div>
                </el-tab-pane>
                <el-tab-pane label="特征重要性" name="features" v-if="trainingResult.feature_importance">
                  <div ref="featureImportanceChart" style="height: 400px;"></div>
                </el-tab-pane>
                <el-tab-pane label="混淆矩阵" name="confusion" v-if="trainingResult.confusion_matrix">
                  <div ref="confusionMatrixChart" style="height: 400px;"></div>
                </el-tab-pane>
                <el-tab-pane label="模型信息" name="info">
                  <el-descriptions title="模型详情" :column="2" border>
                    <el-descriptions-item label="模型ID">{{ trainingResult.model_id }}</el-descriptions-item>
                    <el-descriptions-item label="算法类型">{{ trainingResult.model_type }}</el-descriptions-item>
                    <el-descriptions-item label="任务类型">{{ trainingResult.task_type }}</el-descriptions-item>
                    <el-descriptions-item label="目标变量">{{ trainingResult.target }}</el-descriptions-item>
                    <el-descriptions-item label="特征数量">{{ trainingResult.features?.length }}</el-descriptions-item>
                    <el-descriptions-item label="创建时间">{{ trainingResult.created_at }}</el-descriptions-item>
                    <el-descriptions-item label="数据形状">{{ trainingResult.data_shape?.[0] }} 行 × {{ trainingResult.data_shape?.[1] }} 列</el-descriptions-item>
                  </el-descriptions>
                </el-tab-pane>
              </el-tabs>
            </div>
            <div v-if="!training && !trainingResult" class="empty-state">
              <el-empty description="配置参数后开始训练模型" />
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { mlAPI, dataAPI, featureAPI } from '@/api'

const availableDataIds = ref([])
const availableColumns = ref([])
const training = ref(false)
const trainingProgress = ref(0)
const progressStatus = ref('')
const progressText = ref('')
const estimatedTime = ref('--')
const trainingResult = ref(null)
const activeTab = ref('performance')

const trainingCurveChart = ref(null)
const featureImportanceChart = ref(null)
const confusionMatrixChart = ref(null)

const featureConfigTableData = ref([]); // New: for feature config table
const columnsToAdd = ref([]); // For selecting columns to add to the table

const trainingConfig = ref({
  model_name: '',
  data_id: '',
  algorithm: 'random_forest',
  task_type: 'classification',
  target_column: '',
  // selected_feature_columns and feature_types_to_extract are replaced by featureConfigTableData
  train_ratio: 0.8,
  random_state: 42,
  cross_validation: true,
  cv_folds: 5,
  params: {
    n_estimators: 100,
    max_depth: 10,
    min_samples_split: 2,
    C: 1.0,
    max_iter: 1000,
    kernel: 'rbf',
  }
})

const loadAvailableDataAndFeatures = async () => {
  try {
    const response = await dataAPI.getDataList()
    availableDataIds.value = response.data_ids.map(item => item.data_id) || [] // Assuming data_ids is an array of objects
    if (availableDataIds.value.length > 0) {
      trainingConfig.value.data_id = availableDataIds.value[0]
      await loadColumnsForData()
    }
  } catch (error) {
    console.error('获取数据列表失败:', error)
    ElMessage.error('获取数据列表失败')
  }
}

const handleDataIdChange = async () => {
  featureConfigTableData.value = []; // Reset feature config when data_id changes
  columnsToAdd.value = [];
  await loadColumnsForData();
};

const loadColumnsForData = async () => {
  if (!trainingConfig.value.data_id) {
    availableColumns.value = []
    return
  }
  try {
    const response = await dataAPI.getDataDetails(trainingConfig.value.data_id)
    availableColumns.value = response.columns || []
    if (!availableColumns.value.includes(trainingConfig.value.target_column)) {
      trainingConfig.value.target_column = ''
    }
  } catch (error) {
    console.error(`获取数据 ${trainingConfig.value.data_id} 的列失败:`, error)
    ElMessage.error(`获取数据 ${trainingConfig.value.data_id} 的列失败`)
    availableColumns.value = []
  }
}

const addSelectedColumnsToFeatureTable = () => {
  columnsToAdd.value.forEach(colName => {
    if (!featureConfigTableData.value.find(fc => fc.columnName === colName)) {
      featureConfigTableData.value.push({ columnName: colName, selectedFeatureTypes: ['basic_stats'] });
    }
  });
  columnsToAdd.value = []; // Clear selection
};

const removeColumnFromFeatureTable = (index) => {
  featureConfigTableData.value.splice(index, 1);
};


const updateAlgorithmConfig = () => {
  const defaultParams = {
    random_forest: { n_estimators: 100, max_depth: 10, min_samples_split: 2 },
    logistic_regression: { C: 1.0, max_iter: 1000 },
    svm: { C: 1.0, kernel: 'rbf' }
  }
  trainingConfig.value.params = { ...trainingConfig.value.params, ...defaultParams[trainingConfig.value.algorithm] }
}

const startTraining = async () => {
  if (!trainingConfig.value.model_name) { ElMessage.warning('请输入模型名称'); return }
  if (!trainingConfig.value.data_id) { ElMessage.warning('请选择数据集'); return }
  if (!trainingConfig.value.target_column) { ElMessage.warning('请选择目标变量'); return }
  if (featureConfigTableData.value.length === 0) { ElMessage.warning('请配置特征列'); return }
  if (featureConfigTableData.value.some(fc => fc.selectedFeatureTypes.length === 0)) {
    ElMessage.warning('请为所有配置的特征列选择至少一种特征类型'); return;
  }
  
  training.value = true
  trainingProgress.value = 0
  progressStatus.value = ''
  progressText.value = '准备训练数据...'
  trainingResult.value = null
  
  const progressInterval = setInterval(() => {
    if (trainingProgress.value < 90) {
      trainingProgress.value += Math.random() * 5
      updateProgressText()
    }
  }, 500)
  
  try {
    progressText.value = '正在提取特征...'
    const feature_config_payload = {}
    featureConfigTableData.value.forEach(fc => {
      feature_config_payload[fc.columnName] = fc.selectedFeatureTypes
    })

    const extractResponse = await featureAPI.extractFeatures({
      data_id: trainingConfig.value.data_id,
      feature_config: feature_config_payload
    })
    
    if (!extractResponse.success) {
      throw new Error(extractResponse.features.message || '特征提取失败')
    }
    
    progressText.value = '正在训练模型...'
    const trainPayload = {
      data_id: trainingConfig.value.data_id, // Add data_id to payload
      model_type: trainingConfig.value.algorithm,
      features: Object.keys(extractResponse.features.extracted_features).filter(f => f !== 'data_id'),
      target: trainingConfig.value.target_column,
      model_params: trainingConfig.value.params
    }
    
    const response = await mlAPI.trainModel(trainPayload)
    
    clearInterval(progressInterval)
    trainingProgress.value = 100
    progressStatus.value = 'success'
    progressText.value = '训练完成'
    trainingResult.value = response
    ElMessage.success('模型训练完成')
    await nextTick()
    renderCharts()
    
  } catch (error) {
    clearInterval(progressInterval)
    trainingProgress.value = 100
    progressStatus.value = 'exception'
    progressText.value = '训练失败'
    ElMessage.error(`模型训练失败: ${error.message || error}`)
    console.error('模型训练失败:', error)
  } finally {
    training.value = false
  }
}

const updateProgressText = () => {
  const texts = ['加载数据...','特征提取中...','数据预处理...','模型训练中...','参数优化...','交叉验证...','模型评估...']
  const index = Math.floor(trainingProgress.value / (100 / texts.length))
  progressText.value = texts[Math.min(index, texts.length - 1)]
  const remaining = (100 - trainingProgress.value) * 0.5
  estimatedTime.value = `${Math.ceil(remaining)}秒`
}

const renderCharts = () => {
  if (trainingResult.value) {
    renderTrainingCurve()
  }
}

const renderTrainingCurve = () => {
  if (!trainingCurveChart.value || !trainingResult.value.training_history) return
  const chart = echarts.init(trainingCurveChart.value)
  const history = trainingResult.value.training_history
  const epochs = history.map(h => h.epoch)
  const trainLoss = history.map(h => h.loss)
  const valLoss = history.map(h => h.val_loss)
  const option = {
    title: { text: '训练曲线', left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { data: ['训练损失', '验证损失'], bottom: 0 },
    xAxis: { type: 'category', data: epochs },
    yAxis: { type: 'value' },
    series: [
      { name: '训练损失', type: 'line', data: trainLoss, smooth: true },
      { name: '验证损失', type: 'line', data: valLoss, smooth: true }
    ]
  }
  chart.setOption(option)
}

const formatPercent = (value) => `${(value * 100).toFixed(0)}%`
const formatMetricName = (name) => {
  const nameMap = { accuracy: '准确率', precision: '精确率', recall: '召回率', f1_score: 'F1分数', auc: 'AUC', mse: '均方误差', rmse: '均方根误差', mae: '平均绝对误差', r2: 'R²分数', cv_mean: '交叉验证均值', cv_std: '交叉验证标准差'}
  return nameMap[name] || name
}
const formatMetricValue = (value) => (typeof value === 'number' ? value.toFixed(4) : value)

watch(activeTab, async (newTab) => {
  if (trainingResult.value) {
    await nextTick()
    if (newTab === 'curves') renderTrainingCurve()
    // if (newTab === 'features') renderFeatureImportance() // Needs separate API call
    // if (newTab === 'confusion') renderConfusionMatrix() // Needs separate API call
  }
})

onMounted(() => {
  loadAvailableDataAndFeatures()
})
</script>

<style scoped>
.model-training { height: 100%; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.config-panel { background-color: #f8f9fa; padding: 20px; border-radius: 8px; height: fit-content; max-height: 80vh; overflow-y: auto; }
.config-panel h3 { margin-top: 0; margin-bottom: 20px; color: #409EFF; }
.training-area { min-height: 500px; padding: 20px; }
.training-progress { text-align: center; padding: 40px 20px; }
.training-progress h3 { color: #409EFF; margin-bottom: 20px; }
.progress-info { margin-top: 20px; }
.progress-info p { margin: 5px 0; color: #606266; }
.training-result h3 { color: #409EFF; margin-bottom: 20px; }
.performance-metrics { margin-bottom: 20px; }
.empty-state { display: flex; align-items: center; justify-content: center; height: 400px; }
:deep(.el-form-item__label) { font-weight: 500; }
:deep(.el-divider__text) { font-weight: 600; color: #409EFF; }
:deep(.el-progress-bar__outer) { background-color: #e4e7ed; }
:deep(.el-card__header) { padding: 15px 20px; font-weight: 600; }
:deep(.el-descriptions__label) { font-weight: 500; }
</style>
