<template>
  <div class="data-visualization">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据可视化</span>
          <div class="header-actions">
            <el-button @click="exportChart">
              <el-icon><Download /></el-icon>
              导出图表
            </el-button>
            <el-button type="primary" @click="generateChart">
              <el-icon><TrendCharts /></el-icon>
              生成图表
            </el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="20">
        <!-- 控制面板 -->
        <el-col :span="6">
          <div class="control-panel">
            <h3>可视化配置</h3>
            
            <el-form :model="chartConfig" label-width="100px">
              <el-form-item label="选择数据">
                <el-select v-model="selectedDataId" placeholder="请选择数据集" @change="loadDataDetails">
                  <el-option
                    v-for="dataItem in dataIds"
                    :key="dataItem.data_id"
                    :label="dataItem.data_id"
                    :value="dataItem.data_id"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="图表类型">
                <el-select v-model="chartConfig.chartType">
                  <el-option label="时间序列图" value="timeseries" />
                  <el-option label="散点图" value="scatter" />
                  <!-- 暂时移除其他图表类型，因为需要后端提供相应的数据或更复杂的处理 -->
                  <!-- <el-option label="箱线图" value="boxplot" />
                  <el-option label="直方图" value="histogram" />
                  <el-option label="热力图" value="heatmap" />
                  <el-option label="相关性矩阵" value="correlation" /> -->
                </el-select>
              </el-form-item>

              <el-form-item label="X轴字段" v-if="needsXAxis">
                <el-select v-model="chartConfig.xAxis" clearable>
                  <el-option
                    v-for="col in availableColumns"
                    :key="col"
                    :label="col"
                    :value="col"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="Y轴字段" v-if="needsYAxis">
                <el-select v-model="chartConfig.yAxis" multiple clearable>
                  <el-option
                    v-for="col in availableColumns"
                    :key="col"
                    :label="col"
                    :value="col"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="颜色字段" v-if="needsColorField">
                <el-select v-model="chartConfig.colorField" clearable>
                  <el-option
                    v-for="col in availableColumns"
                    :key="col"
                    :label="col"
                    :value="col"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="数据范围">
                <el-slider
                  v-model="chartConfig.dataRange"
                  range
                  :min="0"
                  :max="maxDataPoints"
                  :step="1"
                  show-stops
                />
                <div class="range-info">
                  显示第 {{ chartConfig.dataRange[0] }} - {{ chartConfig.dataRange[1] }} 个数据点
                </div>
              </el-form-item>

              <el-form-item label="图表标题">
                <el-input v-model="chartConfig.title" placeholder="输入图表标题" />
              </el-form-item>

              <el-form-item label="显示网格">
                <el-switch v-model="chartConfig.showGrid" />
              </el-form-item>

              <el-form-item label="显示图例">
                <el-switch v-model="chartConfig.showLegend" />
              </el-form-item>
            </el-form>
          </div>
        </el-col>

        <!-- 图表显示区域 -->
        <el-col :span="18">
          <div class="chart-container">
            <div v-if="!chartData || chartData.data.length === 0" class="empty-chart">
              <el-empty description="请选择数据和配置参数生成图表" />
            </div>
            <div v-else>
              <div ref="chartRef" class="chart" style="height: 500px;"></div>
              
              <!-- 图表信息 -->
              <div class="chart-info">
                <el-descriptions title="图表信息" :column="3" size="small" border>
                  <el-descriptions-item label="数据点数">
                    {{ chartData.data.length }}
                  </el-descriptions-item>
                  <el-descriptions-item label="时间范围">
                    {{ chartConfig.dataRange[0] }} - {{ chartConfig.dataRange[1] }}
                  </el-descriptions-item>
                  <el-descriptions-item label="更新时间">
                    {{ new Date().toLocaleString() }}
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 多图表对比 (暂时移除) -->
    <!-- <el-card style="margin-top: 20px;" v-if="comparisonCharts.length > 0">
      <template #header>
        <div class="card-header">
          <span>图表对比</span>
          <el-button @click="clearComparison">
            <el-icon><Delete /></el-icon>
            清空对比
          </el-button>
        </div>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="12" v-for="(chart, index) in comparisonCharts" :key="index">
          <div class="comparison-chart">
            <h4>{{ chart.title }}</h4>
            <div :ref="el => comparisonRefs[index] = el" style="height: 300px;"></div>
          </div>
        </el-col>
      </el-row>
    </el-card> -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { dataAPI } from '@/api'

const route = useRoute()

// 数据状态
const dataIds = ref([]) // Renamed from patients
const selectedDataId = ref(route.query.dataId || '') // Renamed from selectedPatient
const dataDetails = ref(null) // Renamed from patientData, stores full data details
const chartData = ref(null) // Stores data specifically for charting (limited rows)
const chartRef = ref(null)
const chartInstance = ref(null)

// 对比图表 (暂时移除相关变量)
// const comparisonCharts = ref([])
// const comparisonRefs = ref([])

// 图表配置
const chartConfig = ref({
  chartType: 'timeseries',
  xAxis: '',
  yAxis: [],
  colorField: '',
  dataRange: [0, 100],
  title: '',
  showGrid: true,
  showLegend: true
})

// 计算属性
const availableColumns = computed(() => {
  return dataDetails.value?.columns || []
})

const maxDataPoints = computed(() => {
  return dataDetails.value?.records || 100
})

const needsXAxis = computed(() => {
  return ['timeseries', 'scatter'].includes(chartConfig.value.chartType)
})

const needsYAxis = computed(() => {
  return ['timeseries', 'scatter'].includes(chartConfig.value.chartType)
})

const needsColorField = computed(() => {
  return ['scatter'].includes(chartConfig.value.chartType)
})

// 方法
const loadDataIds = async () => { // Renamed from loadPatients
  try {
    const response = await dataAPI.getDataList()
    dataIds.value = response.data_ids || []
    
    if (selectedDataId.value && dataIds.value.some(item => item.data_id === selectedDataId.value)) { // Updated logic
      await loadDataDetails()
    } else if (dataIds.value.length > 0) {
      selectedDataId.value = dataIds.value[0].data_id // Auto-select first if no query param, access data_id
      await loadDataDetails()
    }
  } catch (error) {
    ElMessage.error('获取数据列表失败')
    console.error('获取数据列表失败:', error)
  }
}

const loadDataDetails = async () => { // Renamed from loadPatientData
  if (!selectedDataId.value) return
  
  try {
    const response = await dataAPI.getDataDetails(selectedDataId.value)
    dataDetails.value = response // Store full data details
    
    // Update data range max based on actual records
    chartConfig.value.dataRange = [0, Math.min(1000, maxDataPoints.value)] // Default to first 1000 points or max
    
    // Auto-select default X/Y axis if available
    if (availableColumns.value.length > 0) {
      if (needsXAxis.value && !chartConfig.value.xAxis) {
        chartConfig.value.xAxis = availableColumns.value[0]
      }
      if (needsYAxis.value && chartConfig.value.yAxis.length === 0 && availableColumns.value.length > 1) {
        chartConfig.value.yAxis = [availableColumns.value[1]]
      }
    }
    
  } catch (error) {
    ElMessage.error('获取数据详情失败')
    console.error('获取数据详情失败:', error)
  }
}

const generateChart = async () => {
  if (!selectedDataId.value) {
    ElMessage.warning('请先选择数据集')
    return
  }
  if (chartConfig.value.chartType === 'timeseries' && (!chartConfig.value.xAxis || chartConfig.value.yAxis.length === 0)) {
    ElMessage.warning('时间序列图需要选择X轴和至少一个Y轴字段')
    return
  }
  if (chartConfig.value.chartType === 'scatter' && (!chartConfig.value.xAxis || chartConfig.value.yAxis.length === 0)) {
    ElMessage.warning('散点图需要选择X轴和至少一个Y轴字段')
    return
  }
  
  try {
    // getVisualizationData already limits data to 1000 rows by default
    const response = await dataAPI.getVisualizationData(selectedDataId.value)
    
    // Filter data based on dataRange
    const startIndex = chartConfig.value.dataRange[0]
    const endIndex = chartConfig.value.dataRange[1]
    
    chartData.value = {
      data_id: response.data_id,
      columns: response.columns,
      data: response.data.slice(startIndex, endIndex)
    }
    
    await nextTick()
    renderChart()
    
    ElMessage.success('图表生成成功')
    
  } catch (error) {
    ElMessage.error('生成图表失败')
    console.error('生成图表失败:', error)
  }
}

const renderChart = () => {
  if (!chartRef.value || !chartData.value || chartData.value.data.length === 0) return
  
  if (chartInstance.value) {
    chartInstance.value.dispose()
  }
  
  chartInstance.value = echarts.init(chartRef.value)
  
  const option = generateChartOption()
  chartInstance.value.setOption(option)
  
  // 响应式调整
  window.addEventListener('resize', () => {
    chartInstance.value?.resize()
  })
}

const generateChartOption = () => {
  const baseOption = {
    title: {
      text: chartConfig.value.title || `${selectedDataId.value} - ${chartConfig.value.chartType}图`,
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    grid: {
      show: chartConfig.value.showGrid,
      left: '10%',
      right: '10%',
      bottom: '15%'
    },
    legend: {
      show: chartConfig.value.showLegend,
      bottom: 0
    }
  }
  
  const data = chartData.value.data
  const columns = chartData.value.columns

  switch (chartConfig.value.chartType) {
    case 'timeseries':
      const xAxisData = data.map((row, index) => row[chartConfig.value.xAxis] || index) // Use X-axis field or index
      const series = chartConfig.value.yAxis.map(field => ({
        name: field,
        type: 'line',
        data: data.map(row => row[field]),
        smooth: true
      }))
      return {
        ...baseOption,
        xAxis: {
          type: 'category',
          data: xAxisData
        },
        yAxis: {
          type: 'value'
        },
        series: series
      }
      
    case 'scatter':
      const scatterSeries = chartConfig.value.yAxis.map(yField => {
        return {
          name: yField,
          type: 'scatter',
          data: data.map(row => [row[chartConfig.value.xAxis], row[yField]]),
          // Optional: color by another field
          // itemStyle: chartConfig.value.colorField ? {
          //   color: (params) => {
          //     const colorValue = data[params.dataIndex][chartConfig.value.colorField];
          //     // Map colorValue to a color scale
          //     return colorValue > 50 ? 'red' : 'blue'; // Example
          //   }
          // } : {}
        }
      })
      return {
        ...baseOption,
        xAxis: {
          type: 'value',
          name: chartConfig.value.xAxis
        },
        yAxis: {
          type: 'value',
          name: chartConfig.value.yAxis[0] // Only first Y-axis for scatter plot label
        },
        series: scatterSeries
      }
      
    default:
      return baseOption
  }
}

const exportChart = () => {
  if (!chartInstance.value) {
    ElMessage.warning('请先生成图表')
    return
  }
  
  const url = chartInstance.value.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: '#fff'
  })
  
  const link = document.createElement('a')
  link.download = `${selectedDataId.value}_${chartConfig.value.chartType}_${Date.now()}.png`
  link.href = url
  link.click()
  
  ElMessage.success('图表导出成功')
}

// 监听配置变化
watch(() => chartConfig.value.dataRange, () => {
  if (chartData.value) {
    generateChart() // Regenerate chart when data range changes
  }
}, { deep: true })

watch(() => chartConfig.value.chartType, () => {
  // Reset Y-axis selection when chart type changes, as scatter only uses one Y-axis for label
  if (chartConfig.value.chartType === 'scatter' && chartConfig.value.yAxis.length > 1) {
    chartConfig.value.yAxis = [chartConfig.value.yAxis[0]];
  }
});

watch(availableColumns, (newCols) => {
  // Auto-select default X/Y axis if available
  if (newCols.length > 0) {
    if (needsXAxis.value && !chartConfig.value.xAxis) {
      chartConfig.value.xAxis = newCols[0]
    }
    if (needsYAxis.value && chartConfig.value.yAxis.length === 0 && newCols.length > 1) {
      chartConfig.value.yAxis = [newCols[1]]
    }
  } else {
    chartConfig.value.xAxis = ''
    chartConfig.value.yAxis = []
    chartConfig.value.colorField = ''
  }
});


onMounted(() => {
  loadDataIds()
})
</script>

<style scoped>
.data-visualization {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.control-panel {
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  height: fit-content;
}

.control-panel h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #409EFF;
}

.chart-container {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  min-height: 500px;
}

.empty-chart {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
}

.chart {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.chart-info {
  margin-top: 20px;
}

.range-info {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.comparison-chart {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
}

.comparison-chart h4 {
  margin: 0 0 15px 0;
  color: #409EFF;
  font-size: 16px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-slider__runway) {
  margin: 16px 0;
}
</style>
