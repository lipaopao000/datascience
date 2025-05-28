<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <!-- 统计卡片 -->
      <el-col :span="6" v-for="stat in stats" :key="stat.title">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" :style="{ backgroundColor: stat.color }">
              <el-icon :size="24">
                <component :is="stat.icon" />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-title">{{ stat.title }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 数据概览图表 (暂时移除，因为后端不再提供特定数据类型分布) -->
      <!-- <el-col :span="12">
        <el-card title="数据概览">
          <template #header>
            <span>数据概览</span>
          </template>
          <div ref="dataOverviewChart" style="height: 300px;"></div>
        </el-card>
      </el-col> -->

      <!-- 模型性能图表 -->
      <el-col :span="24"> <!-- Changed span to 24 as data overview chart is removed -->
        <el-card title="模型性能">
          <template #header>
            <span>模型性能</span>
          </template>
          <div ref="modelPerformanceChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 最近活动 -->
      <el-col :span="8">
        <el-card title="最近活动">
          <template #header>
            <span>最近活动</span>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="activity in recentActivities"
              :key="activity.id"
              :timestamp="activity.timestamp"
              :color="activity.color"
            >
              {{ activity.content }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>

      <!-- 快速操作 -->
      <el-col :span="8">
        <el-card title="快速操作">
          <template #header>
            <span>快速操作</span>
          </template>
          <div class="quick-actions">
            <el-button
              v-for="action in quickActions"
              :key="action.name"
              :type="action.type"
              :icon="action.icon"
              @click="handleQuickAction(action.route)"
              style="margin-bottom: 10px; width: 100%;"
            >
              {{ action.name }}
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 系统状态 -->
      <el-col :span="8">
        <el-card title="系统状态">
          <template #header>
            <span>系统状态</span>
          </template>
          <div class="system-status">
            <div class="status-item" v-for="status in systemStatus" :key="status.name">
              <span class="status-label">{{ status.name }}</span>
              <el-tag :type="status.type" size="small">{{ status.value }}</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { dataAPI, mlAPI, featureAPI } from '@/api' // Import featureAPI for feature count

const router = useRouter()

// 统计数据
const stats = ref([
  {
    title: '数据集数量', // Renamed from 患者数量
    value: '0',
    icon: 'User',
    color: '#409EFF'
  },
  {
    title: '数据文件', // Renamed from 数据文件
    value: '0',
    icon: 'Document',
    color: '#67C23A'
  },
  {
    title: '训练模型',
    value: '0',
    icon: 'DataAnalysis',
    color: '#E6A23C'
  },
  {
    title: '特征数量', // Renamed from 特征数量
    value: '0',
    icon: 'TrendCharts',
    color: '#F56C6C'
  }
])

// 最近活动
const recentActivities = ref([
  {
    id: 1,
    content: '系统启动完成',
    timestamp: new Date().toLocaleString(),
    color: '#67C23A'
  }
])

// 快速操作
const quickActions = ref([
  {
    name: '上传数据',
    type: 'primary',
    icon: 'Upload',
    route: '/data/upload'
  },
  {
    name: '数据可视化',
    type: 'success',
    icon: 'TrendCharts',
    route: '/analysis/visualization'
  },
  {
    name: '训练模型',
    type: 'warning',
    icon: 'DataAnalysis',
    route: '/ml/train'
  },
  {
    name: '模型预测',
    type: 'info',
    icon: 'Aim',
    route: '/ml/predict'
  }
])

// 系统状态
const systemStatus = ref([
  {
    name: 'API服务',
    value: '正常',
    type: 'success'
  },
  {
    name: '数据库',
    value: '正常',
    type: 'success'
  },
  {
    name: '存储空间',
    value: '充足',
    type: 'success'
  },
  {
    name: '内存使用',
    value: '正常',
    type: 'success'
  }
])

// 图表引用
// const dataOverviewChart = ref(null) // Removed
const modelPerformanceChart = ref(null)

// 处理快速操作
const handleQuickAction = (route) => {
  router.push(route)
}

// 初始化数据概览图表 (Removed as it's hardcoded)
// const initDataOverviewChart = () => {
//   const chart = echarts.init(dataOverviewChart.value)
//   const option = {
//     title: {
//       text: '数据类型分布',
//       left: 'center',
//       textStyle: {
//         fontSize: 14
//       }
//     },
//     tooltip: {
//       trigger: 'item'
//     },
//     series: [
//       {
//         type: 'pie',
//         radius: '60%',
//         data: [
//           { value: 40, name: 'ECG数据' },
//           { value: 35, name: 'MV数据' },
//           { value: 25, name: '其他数据' }
//         ],
//         emphasis: {
//           itemStyle: {
//             shadowBlur: 10,
//             shadowOffsetX: 0,
//             shadowColor: 'rgba(0, 0, 0, 0.5)'
//           }
//         }
//       }
//     ]
//   }
//   chart.setOption(option)
// }

// 初始化模型性能图表
const initModelPerformanceChart = async () => {
  const chart = echarts.init(modelPerformanceChart.value)
  
  try {
    const modelsResponse = await mlAPI.getModels()
    const models = modelsResponse.models || []

    const modelNames = []
    const accuracies = []

    models.forEach(model => {
      modelNames.push(model.model_id.substring(0, 8)); // Use model ID or a truncated version
      // Assuming 'accuracy' is the key for classification models, 'r2' for regression
      if (model.task_type === 'classification' && model.metrics?.accuracy !== undefined) {
        accuracies.push(model.metrics.accuracy);
      } else if (model.task_type === 'regression' && model.metrics?.r2 !== undefined) {
        accuracies.push(model.metrics.r2);
      } else {
        accuracies.push(0); // Default if metric not found
      }
    });

    const option = {
      title: {
        text: '模型性能对比',
        left: 'center',
        textStyle: {
          fontSize: 14
        }
      },
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: modelNames
      },
      yAxis: {
        type: 'value',
        max: 1, // Max accuracy/R2 is 1
        axisLabel: {
          formatter: '{value}'
        }
      },
      series: [
        {
          data: accuracies,
          type: 'bar',
          itemStyle: {
            color: '#409EFF'
          }
        }
      ]
    }
    chart.setOption(option)
  } catch (error) {
    console.error('初始化模型性能图表失败:', error);
    // Fallback to a default chart or empty state if API fails
    chart.setOption({
      title: { text: '模型性能对比 (加载失败)', left: 'center' },
      xAxis: { type: 'category', data: [] },
      yAxis: { type: 'value' },
      series: [{ type: 'bar', data: [] }]
    });
  }
}

// 加载统计数据
const loadStats = async () => {
  try {
    // 获取数据集数量
    const dataListResponse = await dataAPI.getDataList()
    const dataCount = dataListResponse.data_ids?.length || 0
    stats.value[0].value = dataCount
    stats.value[1].value = dataCount // Assuming each dataset is one file for simplicity

    // 获取模型数量
    const modelsResponse = await mlAPI.getModels()
    const modelCount = modelsResponse.models?.length || 0
    stats.value[2].value = modelCount

    // 获取特征数量 (需要遍历所有特征文件并汇总，暂时设为0)
    // This would require a new backend API to get total feature count across all data_ids
    // For now, we'll keep it as 0 or a placeholder.
    stats.value[3].value = 0; // Placeholder

    // 添加活动记录
    recentActivities.value.unshift({
      id: Date.now(),
      content: `加载了 ${dataCount} 个数据集`, // Updated activity text
      timestamp: new Date().toLocaleString(),
      color: '#409EFF'
    })
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

onMounted(async () => {
  await nextTick()
  // initDataOverviewChart() // Removed
  await initModelPerformanceChart() // Ensure this is awaited
  await loadStats()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stat-title {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
}

.system-status {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-label {
  font-size: 14px;
  color: #606266;
}

:deep(.el-card__header) {
  padding: 18px 20px;
  border-bottom: 1px solid #ebeef5;
  font-weight: 600;
}

:deep(.el-card__body) {
  padding: 20px;
}
</style>
