<template>
  <div class="data-explorer">
    <el-card class="header-card">
      <h2>数据探索与清洗实验室</h2>
      <p>可视化原始数据，试验不同清洗方法，实时查看效果</p>
    </el-card>

    <!-- 数据选择 -->
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card title="数据选择">
          <el-form :model="dataSelection" label-width="100px">
            <el-form-item label="数据ID">
              <el-select v-model="dataSelection.data_id" placeholder="选择数据" @change="loadDataDetails">
                <el-option
                  v-for="dataItem in dataList"
                  :key="dataItem.data_id"
                  :label="dataItem.data_id"
                  :value="dataItem.data_id">
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="数据列">
              <el-select v-model="dataSelection.column" placeholder="选择要分析的列" @change="analyzeColumn">
                <el-option
                  v-for="column in availableColumns"
                  :key="column"
                  :label="column"
                  :value="column">
                </el-option>
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card title="数据质量分析">
          <div v-if="qualityReport" class="quality-metrics">
            <el-row :gutter="10">
              <el-col :span="6">
                <el-statistic title="质量评分" :value="qualityReport.quality_score" suffix="/100">
                  <template #prefix>
                    <el-icon :color="getScoreColor(qualityReport.quality_score)">
                      <TrendCharts />
                    </el-icon>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="6">
                <el-statistic title="缺失值" :value="qualityReport.basic_stats.missing_count">
                  <template #prefix>
                    <el-icon color="#f56c6c"><Warning /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="6">
                <el-statistic title="异常值" :value="qualityReport.outlier_stats.zscore_outliers">
                  <template #prefix>
                    <el-icon color="#e6a23c"><Warning /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="6">
                <el-statistic title="变异系数" :value="qualityReport.distribution_stats.coefficient_of_variation" :precision="3">
                  <template #prefix>
                    <el-icon color="#909399"><DataAnalysis /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 原始数据可视化 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card title="原始数据可视化">
          <div ref="originalChart" style="height: 400px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 清洗配置 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card title="清洗配置">
          <el-form :model="cleaningConfig" label-width="120px">
            <!-- 缺失值处理 -->
            <el-divider content-position="left">缺失值处理</el-divider>
            <el-form-item label="处理策略">
              <el-radio-group v-model="cleaningConfig.missing_value_strategy">
                <el-radio label="fill">填充</el-radio>
                <el-radio label="drop">删除</el-radio>
                <el-radio label="none">不处理</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="填充方法" v-if="cleaningConfig.missing_value_strategy === 'fill'">
              <el-select v-model="cleaningConfig.fill_method">
                <el-option label="前向填充" value="ffill"></el-option>
                <el-option label="后向填充" value="bfill"></el-option>
                <el-option label="均值填充" value="mean"></el-option>
                <el-option label="中位数填充" value="median"></el-option>
                <el-option label="线性插值" value="interpolate"></el-option>
                <el-option label="样条插值" value="spline"></el-option>
              </el-select>
            </el-form-item>

            <!-- 滤波处理 -->
            <el-divider content-position="left">信号滤波</el-divider>
            <el-form-item label="应用滤波">
              <el-switch v-model="cleaningConfig.apply_filter"></el-switch>
            </el-form-item>
            <el-form-item label="滤波类型" v-if="cleaningConfig.apply_filter">
              <el-select v-model="cleaningConfig.filter_type">
                <el-option label="低通滤波" value="lowpass"></el-option>
                <el-option label="高通滤波" value="highpass"></el-option>
                <el-option label="带通滤波" value="bandpass"></el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="截止频率" v-if="cleaningConfig.apply_filter">
              <el-slider v-model="cleaningConfig.cutoff_frequency" :min="0.01" :max="1" :step="0.01"></el-slider>
            </el-form-item>

            <!-- 平滑处理 -->
            <el-divider content-position="left">平滑处理</el-divider>
            <el-form-item label="应用平滑">
              <el-switch v-model="cleaningConfig.apply_smoothing"></el-switch>
            </el-form-item>
            <el-form-item label="平滑方法" v-if="cleaningConfig.apply_smoothing">
              <el-select v-model="cleaningConfig.smoothing_method">
                <el-option label="滑动平均" value="rolling_mean"></el-option>
                <el-option label="滑动中位数" value="rolling_median"></el-option>
                <el-option label="Savitzky-Golay" value="savgol"></el-option>
                <el-option label="指数平滑" value="exponential"></el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="窗口大小" v-if="cleaningConfig.apply_smoothing">
              <el-slider v-model="cleaningConfig.smoothing_window" :min="3" :max="21" :step="2"></el-slider>
            </el-form-item>

            <!-- 异常值处理 -->
            <el-divider content-position="left">异常值处理</el-divider>
            <el-form-item label="检测方法">
              <el-checkbox-group v-model="cleaningConfig.outlier_methods">
                <el-checkbox label="iqr">IQR方法</el-checkbox>
                <el-checkbox label="zscore">Z-Score方法</el-checkbox>
                <el-checkbox label="isolation_forest">孤立森林</el-checkbox>
                <el-checkbox label="percentile">百分位数</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            <el-form-item label="Z-Score阈值" v-if="cleaningConfig.outlier_methods.includes('zscore')">
              <el-slider v-model="cleaningConfig.zscore_threshold" :min="1" :max="5" :step="0.1"></el-slider>
            </el-form-item>
            <el-form-item label="IQR因子" v-if="cleaningConfig.outlier_methods.includes('iqr')">
              <el-slider v-model="cleaningConfig.iqr_factor" :min="1" :max="3" :step="0.1"></el-slider>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="previewCleaning" :loading="previewLoading">
                预览效果
              </el-button>
              <el-button type="success" @click="applyCleaning" :loading="cleaningLoading">
                应用清洗
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card title="清洗效果对比">
          <div v-if="previewResult">
            <el-row :gutter="10">
              <el-col :span="8">
                <el-statistic title="标准差减少" :value="previewResult.improvement.std_reduction" suffix="%" :precision="2">
                  <template #prefix>
                    <el-icon :color="previewResult.improvement.std_reduction > 0 ? '#67c23a' : '#f56c6c'">
                      <TrendCharts />
                    </el-icon>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="8">
                <el-statistic title="异常值减少" :value="previewResult.improvement.outlier_reduction">
                  <template #prefix>
                    <el-icon color="#67c23a"><Check /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="8">
                <el-statistic title="缺失值减少" :value="previewResult.improvement.missing_reduction">
                  <template #prefix>
                    <el-icon color="#67c23a"><Check /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
            </el-row>
            <div ref="comparisonChart" style="height: 300px; margin-top: 20px;"></div>
          </div>
          <div v-else class="no-preview">
            <el-empty description="点击预览效果查看清洗结果"></el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 清洗历史 -->
    <el-row style="margin-top: 20px;">
      <el-col :span="24">
        <el-card title="清洗历史">
          <el-table :data="cleaningHistory" style="width: 100%">
            <el-table-column prop="timestamp" label="时间" width="180"></el-table-column>
            <el-table-column prop="column" label="数据列" width="120"></el-table-column>
            <el-table-column prop="methods" label="清洗方法" width="200"></el-table-column>
            <el-table-column prop="improvement" label="改善效果" width="150">
              <template #default="scope">
                <el-tag :type="scope.row.improvement > 10 ? 'success' : scope.row.improvement > 0 ? 'warning' : 'danger'">
                  {{ scope.row.improvement.toFixed(1) }}%
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作">
              <template #default="scope">
                <el-button size="small" @click="reapplyConfig(scope.row)">重新应用</el-button>
                <el-button size="small" type="danger" @click="deleteHistory(scope.$index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, reactive, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { TrendCharts, Warning, DataAnalysis, Check } from '@element-plus/icons-vue'
import { dataAPI } from '@/api'

export default {
  name: 'DataExplorer',
  components: {
    TrendCharts,
    Warning,
    DataAnalysis,
    Check
  },
  setup() {
    const dataList = ref([])
    const availableColumns = ref([])
    const qualityReport = ref(null)
    const previewResult = ref(null)
    const cleaningHistory = ref([])
    const previewLoading = ref(false)
    const cleaningLoading = ref(false)
    
    const originalChart = ref(null)
    const comparisonChart = ref(null)
    let originalChartInstance = null
    let comparisonChartInstance = null

    const dataSelection = reactive({
      data_id: '',
      column: ''
    })

    const cleaningConfig = reactive({
      missing_value_strategy: 'fill',
      fill_method: 'interpolate',
      apply_filter: false,
      filter_type: 'lowpass',
      cutoff_frequency: 0.1,
      apply_smoothing: false,
      smoothing_method: 'rolling_mean',
      smoothing_window: 5,
      outlier_methods: [],
      zscore_threshold: 3.0,
      iqr_factor: 1.5,
      contamination: 0.1,
      lower_percentile: 1,
      upper_percentile: 99
    })

    const loadDataList = async () => { // Renamed from loadPatients
      try {
        const response = await dataAPI.getDataList()
        dataList.value = response.data_ids || []
      } catch (error) {
        ElMessage.error('加载数据列表失败')
      }
    }

    const loadDataDetails = async () => { // Renamed from loadPatientData
      if (!dataSelection.data_id) return
      
      try {
        const response = await dataAPI.getDataDetails(dataSelection.data_id)
        availableColumns.value = response.columns.filter(col => col !== 'timestamp')
      } catch (error) {
        ElMessage.error('加载数据详情失败')
      }
    }

    const analyzeColumn = async () => {
      if (!dataSelection.data_id || !dataSelection.column) return
      
      try {
        // 分析数据质量
        const qualityResponse = await dataAPI.analyzeDataQuality(dataSelection.data_id)
        qualityReport.value = qualityResponse.quality_report[dataSelection.column]
        
        // 获取原始数据进行可视化
        const dataResponse = await dataAPI.getDataDetails(dataSelection.data_id)
        const data = dataResponse.data
        
        // 绘制原始数据图表
        drawOriginalChart(data)
        
      } catch (error) {
        ElMessage.error('分析数据失败')
      }
    }

    const drawOriginalChart = (data) => {
      if (!originalChartInstance) {
        originalChartInstance = echarts.init(originalChart.value)
      }
      
      const xData = data.map((item, index) => index)
      const yData = data.map(item => item[dataSelection.column])
      
      const option = {
        title: {
          text: `原始数据 - ${dataSelection.column}`,
          left: 'center'
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: xData,
          name: '时间点'
        },
        yAxis: {
          type: 'value',
          name: '数值'
        },
        series: [{
          name: dataSelection.column,
          type: 'line',
          data: yData,
          smooth: false,
          lineStyle: {
            width: 1
          },
          symbol: 'none'
        }]
      }
      
      originalChartInstance.setOption(option)
    }

    const drawComparisonChart = (originalData, cleanedData) => {
      if (!comparisonChartInstance) {
        comparisonChartInstance = echarts.init(comparisonChart.value)
      }
      
      const xData = originalData.map((_, index) => index)
      
      const option = {
        title: {
          text: '清洗前后对比',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: ['原始数据', '清洗后数据'],
          top: 30
        },
        xAxis: {
          type: 'category',
          data: xData,
          name: '时间点'
        },
        yAxis: {
          type: 'value',
          name: '数值'
        },
        series: [
          {
            name: '原始数据',
            type: 'line',
            data: originalData,
            smooth: false,
            lineStyle: {
              width: 1,
              color: '#f56c6c'
            },
            symbol: 'none'
          },
          {
            name: '清洗后数据',
            type: 'line',
            data: cleanedData,
            smooth: false,
            lineStyle: {
              width: 1,
              color: '#67c23a'
            },
            symbol: 'none'
          }
        ]
      }
      
      comparisonChartInstance.setOption(option)
    }

    const previewCleaning = async () => {
      if (!dataSelection.data_id || !dataSelection.column) {
        ElMessage.warning('请先选择数据ID和数据列')
        return
      }
      
      previewLoading.value = true
      try {
        const config = {
          ...cleaningConfig,
          column: dataSelection.column
        }
        
        const response = await dataAPI.previewCleaningEffect(dataSelection.data_id, config)
        previewResult.value = response
        
        // 绘制对比图表
        await nextTick()
        drawComparisonChart(previewResult.value.original_data, previewResult.value.cleaned_data)
        
        ElMessage.success('预览生成成功')
      } catch (error) {
        ElMessage.error('预览失败: ' + error.message)
      } finally {
        previewLoading.value = false
      }
    }

    const applyCleaning = async () => {
      if (!previewResult.value) {
        ElMessage.warning('请先预览清洗效果')
        return
      }
      
      cleaningLoading.value = true
      try {
        const config = {
          ...cleaningConfig,
          column: dataSelection.column
        }
        
        const response = await dataAPI.enhancedCleanData(dataSelection.data_id, config)
        
        // 添加到清洗历史
        cleaningHistory.value.unshift({
          timestamp: new Date().toLocaleString(),
          column: dataSelection.column,
          methods: getMethodsDescription(),
          improvement: previewResult.value.improvement.std_reduction,
          config: { ...cleaningConfig }
        })
        
        ElMessage.success('数据清洗完成')
        
        // 重新分析数据质量
        analyzeColumn()
        
      } catch (error) {
        ElMessage.error('清洗失败: ' + error.message)
      } finally {
        cleaningLoading.value = false
      }
    }

    const getMethodsDescription = () => {
      const methods = []
      if (cleaningConfig.missing_value_strategy !== 'none') {
        methods.push(`缺失值${cleaningConfig.missing_value_strategy}`)
      }
      if (cleaningConfig.apply_filter) {
        methods.push(`${cleaningConfig.filter_type}滤波`)
      }
      if (cleaningConfig.apply_smoothing) {
        methods.push(`${cleaningConfig.smoothing_method}平滑`)
      }
      if (cleaningConfig.outlier_methods.length > 0) {
        methods.push(`异常值处理`)
      }
      return methods.join(', ')
    }

    const reapplyConfig = (historyItem) => {
      Object.assign(cleaningConfig, historyItem.config)
      ElMessage.success('配置已恢复')
    }

    const deleteHistory = (index) => {
      cleaningHistory.value.splice(index, 1)
      ElMessage.success('历史记录已删除')
    }

    const getScoreColor = (score) => {
      if (score >= 80) return '#67c23a'
      if (score >= 60) return '#e6a23c'
      return '#f56c6c'
    }

    onMounted(() => {
      loadDataList()
    })

    return {
      dataList,
      availableColumns,
      qualityReport,
      previewResult,
      cleaningHistory,
      previewLoading,
      cleaningLoading,
      dataSelection,
      cleaningConfig,
      originalChart,
      comparisonChart,
      loadDataDetails,
      analyzeColumn,
      previewCleaning,
      applyCleaning,
      reapplyConfig,
      deleteHistory,
      getScoreColor
    }
  }
}
</script>

<style scoped>
.data-explorer {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
  text-align: center;
}

.quality-metrics {
  padding: 20px 0;
}

.no-preview {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.el-divider {
  margin: 15px 0;
}

.el-statistic {
  text-align: center;
}
</style>
