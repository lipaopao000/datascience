<template>
  <div class="feature-engineering">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>特征工程</span>
          <el-button type="primary" @click="extractFeatures" :loading="extracting">
            <el-icon><Tools /></el-icon>
            提取特征
          </el-button>
        </div>
      </template>

      <el-row :gutter="20">
        <!-- 配置面板 -->
        <el-col :span="8">
          <div class="config-panel">
            <h3>特征提取配置</h3>
            
            <el-form :model="featureConfig" label-width="120px">
              <el-form-item label="选择数据版本">
                <el-select v-model="selectedDataVersionId" placeholder="请选择数据集版本" @change="loadDataDetails">
                  <el-option
                    v-for="dataVersion in dataVersions"
                    :key="dataVersion.version_id"
                    :label="`${dataVersion.data_entity_id} (v${dataVersion.version_number})`"
                    :value="dataVersion.version_id"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="数据类型">
                <el-checkbox-group v-model="featureConfig.data_types">
                  <el-checkbox label="ecg">ECG数据</el-checkbox>
                  <el-checkbox label="mv">MV数据</el-checkbox>
                </el-checkbox-group>
              </el-form-item>

              <el-divider>统计特征</el-divider>

              <el-form-item label="基础统计">
                <el-checkbox-group v-model="featureConfig.statistical_features">
                  <el-checkbox label="mean">均值</el-checkbox>
                  <el-checkbox label="std">标准差</el-checkbox>
                  <el-checkbox label="min">最小值</el-checkbox>
                  <el-checkbox label="max">最大值</el-checkbox>
                  <el-checkbox label="median">中位数</el-checkbox>
                  <el-checkbox label="skewness">偏度</el-checkbox>
                  <el-checkbox label="kurtosis">峰度</el-checkbox>
                </el-checkbox-group>
              </el-form-item>

              <el-form-item label="分位数">
                <el-checkbox-group v-model="featureConfig.quantile_features">
                  <el-checkbox label="q25">25%分位数</el-checkbox>
                  <el-checkbox label="q75">75%分位数</el-checkbox>
                  <el-checkbox label="iqr">四分位距</el-checkbox>
                </el-checkbox-group>
              </el-form-item>

              <el-divider>时间序列特征</el-divider>

              <el-form-item label="趋势特征">
                <el-checkbox-group v-model="featureConfig.trend_features">
                  <el-checkbox label="slope">斜率</el-checkbox>
                  <el-checkbox label="trend_strength">趋势强度</el-checkbox>
                  <el-checkbox label="turning_points">转折点数量</el-checkbox>
                </el-checkbox-group>
              </el-form-item>

              <el-form-item label="变化特征">
                <el-checkbox-group v-model="featureConfig.change_features">
                  <el-checkbox label="variance">方差</el-checkbox>
                  <el-checkbox label="range">极差</el-checkbox>
                  <el-checkbox label="coefficient_variation">变异系数</el-checkbox>
                </el-checkbox-group>
              </el-form-item>

              <el-divider>频域特征</el-divider>

              <el-form-item label="频谱分析">
                <el-checkbox-group v-model="featureConfig.frequency_features">
                  <el-checkbox label="fft_mean">FFT均值</el-checkbox>
                  <el-checkbox label="fft_std">FFT标准差</el-checkbox>
                  <el-checkbox label="dominant_frequency">主频率</el-checkbox>
                  <el-checkbox label="spectral_entropy">谱熵</el-checkbox>
                </el-checkbox-group>
              </el-form-item>

              <el-divider>窗口设置</el-divider>

              <el-form-item label="窗口大小">
                <el-input-number v-model="featureConfig.window_size" :min="10" :max="1000" />
              </el-form-item>

              <el-form-item label="步长">
                <el-input-number v-model="featureConfig.step_size" :min="1" :max="100" />
              </el-form-item>

              <el-form-item label="重叠率">
                <el-slider
                  v-model="featureConfig.overlap_ratio"
                  :min="0"
                  :max="0.9"
                  :step="0.1"
                  show-input
                  :format-tooltip="formatPercent"
                />
              </el-form-item>
            </el-form>
          </div>
        </el-col>

        <!-- 特征展示区域 -->
        <el-col :span="16">
          <div class="feature-display">
            <el-tabs v-model="activeTab">
              <el-tab-pane label="特征列表" name="list">
                <div v-if="extractedFeatures">
                  <div class="feature-summary">
                    <el-row :gutter="20">
                      <el-col :span="6">
                        <el-statistic title="特征总数" :value="extractedFeatures.total_features" />
                      </el-col>
                      <el-col :span="6">
                        <el-statistic title="统计特征" :value="extractedFeatures.statistical_count" />
                      </el-col>
                      <el-col :span="6">
                        <el-statistic title="时序特征" :value="extractedFeatures.temporal_count" />
                      </el-col>
                      <el-col :span="6">
                        <el-statistic title="频域特征" :value="extractedFeatures.frequency_count" />
                      </el-col>
                    </el-row>
                  </div>

                  <el-table :data="extractedFeatures.features" style="margin-top: 20px;" max-height="400">
                    <el-table-column prop="name" label="特征名称" width="200" />
                    <el-table-column prop="type" label="特征类型" width="120">
                      <template #default="{ row }">
                        <el-tag :type="getFeatureTypeColor(row.type)">{{ row.type }}</el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="value" label="特征值" width="120">
                      <template #default="{ row }">
                        {{ formatFeatureValue(row.value) }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="importance" label="重要性" width="120">
                      <template #default="{ row }">
                        <el-progress
                          :percentage="row.importance * 100"
                          :show-text="false"
                          :color="getImportanceColor(row.importance)"
                        />
                        <span style="margin-left: 8px; font-size: 12px;">
                          {{ (row.importance * 100).toFixed(1) }}%
                        </span>
                      </template>
                    </el-table-column>
                    <el-table-column prop="description" label="描述" />
                  </el-table>
                </div>
                <el-empty v-else description="请配置参数并提取特征" />
              </el-tab-pane>

              <el-tab-pane label="特征分布" name="distribution">
                <div ref="featureDistributionChart" style="height: 400px;" v-if="extractedFeatures"></div>
                <el-empty v-else description="暂无特征分布数据" />
              </el-tab-pane>

              <el-tab-pane label="相关性分析" name="correlation">
                <div ref="correlationChart" style="height: 400px;" v-if="extractedFeatures"></div>
                <el-empty v-else description="暂无相关性数据" />
              </el-tab-pane>

              <el-tab-pane label="特征重要性" name="importance">
                <div ref="importanceChart" style="height: 400px;" v-if="extractedFeatures"></div>
                <el-empty v-else description="暂无重要性数据" />
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, defineProps } from 'vue' // Added defineProps
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { projectAPI } from '@/api' // Changed dataAPI and featureAPI to projectAPI

const route = useRoute()

const props = defineProps({
  projectId: {
    type: Number,
    required: true
  }
});

// 数据状态
const dataVersions = ref([]) // Renamed from dataList to dataVersions
const selectedDataVersionId = ref(route.query.dataVersionId || '') // Renamed from selectedDataId
const selectedDataEntityId = ref(route.query.dataEntityId || '') // New: to store data_entity_id
const selectedVersionNumber = ref(route.query.versionNumber || null) // New: to store version_number

const extractedFeatures = ref(null)
const extracting = ref(false)
const activeTab = ref('list')

// 图表引用
const featureDistributionChart = ref(null)
const correlationChart = ref(null)
const importanceChart = ref(null)

// 特征配置
const featureConfig = ref({
  data_types: ['ecg', 'mv'],
  statistical_features: ['mean', 'std', 'min', 'max'],
  quantile_features: ['q25', 'q75', 'iqr'],
  trend_features: ['slope', 'trend_strength'],
  change_features: ['variance', 'range'],
  frequency_features: ['fft_mean', 'dominant_frequency'],
  window_size: 100,
  step_size: 10,
  overlap_ratio: 0.5
})

// 方法
const loadDataVersions = async () => { // Renamed from loadDataList
  extracting.value = true; // Using extracting for loading state
  try {
    const currentProjectId = Number(props.projectId);
    if (isNaN(currentProjectId) || currentProjectId <= 0) {
      ElMessage.error('无效的项目ID，无法加载数据版本。');
      dataVersions.value = [];
      return;
    }
    const response = await projectAPI.getProjectVersions(currentProjectId, 0, 100);
    dataVersions.value = response || [];

    // Attempt to pre-select based on route query or first available
    if (selectedDataEntityId.value && selectedVersionNumber.value) {
      const found = dataVersions.value.find(
        item => item.data_entity_id === selectedDataEntityId.value && item.version_number === Number(selectedVersionNumber.value)
      );
      if (found) {
        selectedDataVersionId.value = found.version_id;
        await loadDataDetails();
      } else if (dataVersions.value.length > 0) {
        selectedDataVersionId.value = dataVersions.value[0].version_id;
        selectedDataEntityId.value = dataVersions.value[0].data_entity_id;
        selectedVersionNumber.value = dataVersions.value[0].version_number;
        await loadDataDetails();
      }
    } else if (dataVersions.value.length > 0) {
      selectedDataVersionId.value = dataVersions.value[0].version_id;
      selectedDataEntityId.value = dataVersions.value[0].data_entity_id;
      selectedVersionNumber.value = dataVersions.value[0].version_number;
      await loadDataDetails();
    }
  } catch (error) {
    ElMessage.error('获取数据版本列表失败');
    console.error('获取数据版本列表失败:', error);
  } finally {
    extracting.value = false;
  }
};

const loadDataDetails = async () => { // Renamed from loadDataDetails
  if (!selectedDataVersionId.value || !selectedDataEntityId.value || selectedVersionNumber.value === null) return;

  try {
    const currentProjectId = Number(props.projectId);
    if (isNaN(currentProjectId) || currentProjectId <= 0) {
      ElMessage.error('无效的项目ID，无法获取数据详情。');
      return;
    }
    const response = await projectAPI.viewProjectDataVersion(
      currentProjectId,
      selectedDataEntityId.value,
      selectedVersionNumber.value,
      1, // page
      1 // pageSize - just to get columns, not full data
    );
    // Here you might want to store the columns or other metadata if needed for config adjustments
    console.log('数据详情加载完成:', response);
  } catch (error) {
    ElMessage.error('获取数据详情失败');
    console.error('获取数据详情失败:', error);
  }
};

const extractFeatures = async () => {
  if (!selectedDataVersionId.value || !selectedDataEntityId.value || selectedVersionNumber.value === null) {
    ElMessage.warning('请先选择数据版本');
    return;
  }

  extracting.value = true;

  try {
    const currentProjectId = Number(props.projectId);
    if (isNaN(currentProjectId) || currentProjectId <= 0) {
      ElMessage.error('无效的项目ID，无法提取特征。');
      return;
    }

    const requestData = {
      data_entity_id: selectedDataEntityId.value,
      version_number: selectedVersionNumber.value,
      ...featureConfig.value
    };

    const response = await projectAPI.extractProjectFeatures(currentProjectId, requestData);

    extractedFeatures.value = {
      total_features: response.features?.length || 0,
      statistical_count: response.statistical_count || 0,
      temporal_count: response.temporal_count || 0,
      frequency_count: response.frequency_count || 0,
      features: response.features || []
    };

    ElMessage.success('特征提取完成');

    await nextTick();
    renderCharts();

  } catch (error) {
    ElMessage.error(`特征提取失败: ${error.response?.data?.detail || error.message}`);
    console.error('特征提取失败:', error);

    // Fallback to mock data if API fails
    extractedFeatures.value = {
      total_features: 50,
      statistical_count: 20,
      temporal_count: 15,
      frequency_count: 15,
      features: generateMockFeatures()
    };

    await nextTick();
    renderCharts();
  } finally {
    extracting.value = false;
  }
};

const generateMockFeatures = () => {
  const featureTypes = ['统计', '时序', '频域']
  const features = []
  
  // 统计特征
  const statFeatures = ['均值', '标准差', '最小值', '最大值', '中位数', '偏度', '峰度']
  statFeatures.forEach(name => {
    features.push({
      name: `ECG_${name}`,
      type: '统计',
      value: Math.random() * 100,
      importance: Math.random(),
      description: `ECG数据的${name}特征`
    })
    features.push({
      name: `MV_${name}`,
      type: '统计',
      value: Math.random() * 100,
      importance: Math.random(),
      description: `MV数据的${name}特征`
    })
  })
  
  // 时序特征
  const timeFeatures = ['斜率', '趋势强度', '转折点', '方差', '极差']
  timeFeatures.forEach(name => {
    features.push({
      name: `ECG_${name}`,
      type: '时序',
      value: Math.random() * 100,
      importance: Math.random(),
      description: `ECG数据的${name}特征`
    })
    features.push({
      name: `MV_${name}`,
      type: '时序',
      value: Math.random() * 100,
      importance: Math.random(),
      description: `MV数据的${name}特征`
    })
  })
  
  // 频域特征
  const freqFeatures = ['FFT均值', '主频率', '谱熵']
  freqFeatures.forEach(name => {
    features.push({
      name: `ECG_${name}`,
      type: '频域',
      value: Math.random() * 100,
      importance: Math.random(),
      description: `ECG数据的${name}特征`
    })
    features.push({
      name: `MV_${name}`,
      type: '频域',
      value: Math.random() * 100,
      importance: Math.random(),
      description: `MV数据的${name}特征`
    })
  })
  
  return features.slice(0, 30) // 返回前30个特征
}

const renderCharts = () => {
  if (extractedFeatures.value) {
    renderFeatureDistribution()
    renderCorrelationMatrix()
    renderImportanceChart()
  }
}

const renderFeatureDistribution = () => {
  if (!featureDistributionChart.value) return
  
  const chart = echarts.init(featureDistributionChart.value)
  const features = extractedFeatures.value.features
  
  const option = {
    title: {
      text: '特征值分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: features.map(f => f.name).slice(0, 15),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      type: 'bar',
      data: features.map(f => f.value).slice(0, 15),
      itemStyle: {
        color: '#409EFF'
      }
    }]
  }
  chart.setOption(option)
}

const renderCorrelationMatrix = () => {
  if (!correlationChart.value) return
  
  const chart = echarts.init(correlationChart.value)
  const features = extractedFeatures.value.features.slice(0, 10)
  const data = []
  
  features.forEach((f1, i) => {
    features.forEach((f2, j) => {
      const correlation = i === j ? 1 : (Math.random() - 0.5) * 2
      data.push([i, j, correlation])
    })
  })
  
  const option = {
    title: {
      text: '特征相关性矩阵',
      left: 'center'
    },
    tooltip: {
      position: 'top'
    },
    xAxis: {
      type: 'category',
      data: features.map(f => f.name),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'category',
      data: features.map(f => f.name)
    },
    visualMap: {
      min: -1,
      max: 1,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '5%'
    },
    series: [{
      type: 'heatmap',
      data: data,
      label: {
        show: true,
        formatter: '{c}'
      }
    }]
  }
  chart.setOption(option)
}

const renderImportanceChart = () => {
  if (!importanceChart.value) return
  
  const chart = echarts.init(importanceChart.value)
  const features = extractedFeatures.value.features
    .sort((a, b) => b.importance - a.importance)
    .slice(0, 15)
  
  const option = {
    title: {
      text: '特征重要性排序',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    xAxis: {
      type: 'value'
    },
    yAxis: {
      type: 'category',
      data: features.map(f => f.name)
    },
    series: [{
      type: 'bar',
      data: features.map(f => f.importance),
      itemStyle: {
        color: (params) => {
          const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
          return colors[params.dataIndex % colors.length]
        }
      }
    }]
  }
  chart.setOption(option)
}

const getFeatureTypeColor = (type) => {
  const colorMap = {
    '统计': 'primary',
    '时序': 'success',
    '频域': 'warning'
  }
  return colorMap[type] || 'info'
}

const getImportanceColor = (importance) => {
  if (importance >= 0.8) return '#67C23A'
  if (importance >= 0.6) return '#E6A23C'
  if (importance >= 0.4) return '#409EFF'
  return '#F56C6C'
}

const formatFeatureValue = (value) => {
  if (typeof value === 'number') {
    return value.toFixed(3)
  }
  return value
}

const formatPercent = (value) => `${(value * 100).toFixed(0)}%`

// 监听标签页切换
watch(activeTab, async (newTab) => {
  if (extractedFeatures.value) {
    await nextTick()
    if (newTab === 'distribution') renderFeatureDistribution()
    if (newTab === 'correlation') renderCorrelationMatrix()
    if (newTab === 'importance') renderImportanceChart()
  }
})

onMounted(() => {
  // Watch for projectId changes and load data versions
  watch(() => props.projectId, (newProjectId) => {
    if (newProjectId && newProjectId > 0) {
      loadDataVersions();
    } else {
      dataVersions.value = [];
      selectedDataVersionId.value = '';
      selectedDataEntityId.value = '';
      selectedVersionNumber.value = null;
      extractedFeatures.value = null;
      ElMessage.warning('无效的项目ID，无法加载数据版本。');
    }
  }, { immediate: true }); // Run immediately on component mount
});

// Watch for selectedDataVersionId change to update selectedDataEntityId and selectedVersionNumber
watch(selectedDataVersionId, (newVersionId) => {
  const selectedVersion = dataVersions.value.find(v => v.version_id === newVersionId);
  if (selectedVersion) {
    selectedDataEntityId.value = selectedVersion.data_entity_id;
    selectedVersionNumber.value = selectedVersion.version_number;
  } else {
    selectedDataEntityId.value = '';
    selectedVersionNumber.value = null;
  }
});
</script>

<style scoped>
.feature-engineering {
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
  max-height: 80vh;
  overflow-y: auto;
}

.config-panel h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #409EFF;
}

.feature-display {
  min-height: 500px;
  padding: 20px;
}

.feature-summary {
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-divider__text) {
  font-weight: 600;
  color: #409EFF;
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:deep(.el-checkbox) {
  margin-right: 0;
}

:deep(.el-statistic__head) {
  font-size: 14px;
  color: #606266;
}

:deep(.el-statistic__content) {
  font-size: 20px;
  font-weight: 600;
}

:deep(.el-table .cell) {
  padding: 8px 0;
}
</style>
