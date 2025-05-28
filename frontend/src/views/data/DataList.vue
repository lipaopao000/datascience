<template>
  <div class="data-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据列表</span>
          <div class="header-actions">
            <el-button type="primary" @click="refreshData">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button type="success" @click="handleConfirmData" :disabled="selectedDataForConfirmation.length === 0">
              <el-icon><CircleCheck /></el-icon>
              确认数据
            </el-button>
            <el-button type="info" @click="handleFormatData" :disabled="selectedDataForConfirmation.length === 0">
              <el-icon><MagicStick /></el-icon>
              格式化
            </el-button>
            <el-button type="danger" @click="handleBatchDelete" :disabled="selectedDataForConfirmation.length === 0">
              <el-icon><Delete /></el-icon>
              批量删除
            </el-button>
          </div>
        </div>
      </template>

      <!-- 搜索和过滤 -->
      <div class="search-section">
        <el-row :gutter="20" align="middle">
          <el-col :span="8">
            <el-input
              v-model="searchText"
              placeholder="搜索数据ID"
              clearable
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="6">
            <el-switch
              v-model="showHighFrequencyHeaderless"
              active-text="显示高频无表头数据"
              inactive-text="显示所有数据"
              @change="handleFilterChange"
            />
          </el-col>
        </el-row>
        <el-row :gutter="20" align="middle" style="margin-top: 15px;">
          <el-col :span="8">
            <el-input
              v-model="filterGroupName"
              placeholder="按分组名称筛选"
              clearable
              @input="handleFilterChange"
            >
              <template #prefix>
                <el-icon><FolderOpened /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="8">
            <el-date-picker
              v-model="filterUploadTimeRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始上传时间"
              end-placeholder="结束上传时间"
              @change="handleFilterChange"
              value-format="YYYY-MM-DDTHH:mm:ss"
            />
          </el-col>
          <el-col :span="8">
            <el-input-number
              v-model="filterColumnsCountMin"
              :min="0"
              placeholder="最小列数"
              @change="handleFilterChange"
              controls-position="right"
              style="width: 120px;"
            />
            <span style="margin: 0 5px;">-</span>
            <el-input-number
              v-model="filterColumnsCountMax"
              :min="0"
              placeholder="最大列数"
              @change="handleFilterChange"
              controls-position="right"
              style="width: 120px;"
            />
          </el-col>
        </el-row>
      </div>

      <!-- 数据表格 -->
      <el-table
        :data="paginatedDataList"
        v-loading="loading"
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="data_id" label="数据ID" width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="viewDataDetail(row.data_id)">
              {{ row.data_id }}
            </el-link>
          </template>
        </el-table-column>
        
        <el-table-column prop="records" label="记录数" width="120">
          <template #default="{ row }">
            {{ row.records || 0 }}
          </template>
        </el-table-column>

        <el-table-column prop="columns_count" label="列数" width="100">
          <template #default="{ row }">
            {{ row.columns_count || 0 }}
          </template>
        </el-table-column>

        <el-table-column prop="group_name" label="分组名称" width="150">
          <template #default="{ row }">
            {{ row.group_name || '无' }}
          </template>
        </el-table-column>

        <el-table-column prop="upload_time" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.upload_time) }}
          </template>
        </el-table-column>

        <el-table-column prop="version" label="版本" width="80">
          <template #default="{ row }">
            V{{ row.version || 1 }}
          </template>
        </el-table-column>

        <el-table-column prop="last_modified_at" label="修改日期" width="180">
          <template #default="{ row }">
            {{ formatDate(row.last_modified_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="viewDataDetail(row.data_id)">
              查看
            </el-button>
            <el-button size="small" type="success" @click="visualizeData(row.data_id)">
              可视化
            </el-button>
            <el-button size="small" type="warning" @click="cleanData(row.data_id)">
              清洗
            </el-button>
            <el-button size="small" type="info" @click="extractFeatures(row.data_id)">
              特征提取
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          :current-page="currentPage"
          @update:current-page="currentPage = $event"
          :page-size="pageSize"
          @update:page-size="pageSize = $event"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalData"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 数据详情对话框 -->
    <el-dialog
      v-model="showDataDetail"
      :title="`数据 ${selectedData?.data_id} 详情`"
      width="80%"
      top="5vh"
    >
      <div v-if="selectedData" class="data-detail">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="基本信息" name="basic">
            <el-descriptions title="数据概览" :column="2" border>
              <el-descriptions-item label="数据ID">
                {{ selectedData.data_id }}
              </el-descriptions-item>
              <el-descriptions-item label="记录数">
                {{ selectedData.records }}
              </el-descriptions-item>
              <el-descriptions-item label="列数">
                {{ selectedData.columns_count }}
              </el-descriptions-item>
              <el-descriptions-item label="数据形状">
                {{ selectedData.shape?.[0] }} 行 × {{ selectedData.shape?.[1] }} 列
              </el-descriptions-item>
              <el-descriptions-item label="列名">
                {{ selectedData.columns?.join(', ') }}
              </el-descriptions-item>
            </el-descriptions>
          </el-tab-pane>
          
          <el-tab-pane label="数据预览" name="preview" v-if="dataDetailData?.data?.length">
            <div class="data-preview">
              <h4>数据预览 (前10行)</h4>
              <el-table :data="dataDetailData.data?.slice(0, 10)" size="small" max-height="300">
                <el-table-column
                  v-for="col in dataDetailData.columns"
                  :key="col"
                  :prop="col"
                  :label="col"
                  width="120"
                >
                  <template #default="{ row }">
                    {{ typeof row[col] === 'number' ? row[col].toFixed(2) : row[col] }}
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

    <!-- 数据确认对话框 -->
    <el-dialog
      v-model="showConfirmDialog"
      title="确认数据"
      width="40%"
      top="20vh"
      @close="resetConfirmDialog"
    >
      <el-form :model="confirmForm" label-width="120px">
        <el-form-item label="选中的数据ID">
          <el-tag
            v-for="dataId in selectedDataForConfirmation.map(d => d.data_id)"
            :key="dataId"
            closable
            @close="removeDataFromConfirmation(dataId)"
            style="margin-right: 8px; margin-bottom: 8px;"
          >
            {{ dataId }}
          </el-tag>
        </el-form-item>
        <p style="margin-left: 120px; color: #606266;">您确定要确认这些数据吗？</p>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showConfirmDialog = false">取消</el-button>
          <el-button type="primary" @click="submitConfirmation">
            提交
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 数据格式化对话框 -->
    <data-format-dialog
      :visible="showFormatDialog"
      :selected-data-ids="selectedDataForConfirmation.map(d => d.data_id)"
      @update:visible="showFormatDialog = $event"
      @formattedSuccess="refreshData"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { dataAPI, schemaAPI } from '@/api'
import { Refresh, Search, CircleCheck, InfoFilled, MagicStick, Delete, FolderOpened } from '@element-plus/icons-vue' // Import Delete and FolderOpened icons
import DataFormatDialog from '@/components/DataFormatDialog.vue' // Import the new component

const router = useRouter()

// 数据状态
const dataList = ref([])
const loading = ref(false)
const searchText = ref('')
const showHighFrequencyHeaderless = ref(false)
const filterGroupName = ref('') // New filter state
const filterUploadTimeRange = ref(null) // New filter state (array of two dates)
const filterColumnsCountMin = ref(null) // New filter state
const filterColumnsCountMax = ref(null) // New filter state
const currentPage = ref(1)
const pageSize = ref(20)
const selectedDataForConfirmation = ref([])

// 数据详情
const showDataDetail = ref(false)
const selectedData = ref(null)
const dataDetailData = ref(null)
const activeTab = ref('basic')

// 数据确认对话框状态
const showConfirmDialog = ref(false)
const confirmForm = ref({
  data_ids: [],
})

// 数据格式化对话框状态
const showFormatDialog = ref(false) // New state for format dialog

// 计算属性
const filteredData = computed(() => {
  let filtered = dataList.value

  if (searchText.value) {
    filtered = filtered.filter(dataItem =>
      dataItem.data_id.toLowerCase().includes(searchText.value.toLowerCase())
    )
  }

  if (showHighFrequencyHeaderless.value) {
    filtered = filtered.filter(dataItem =>
      dataItem.schema_applied === '高频宽表模式' // Assuming this is the name for high-frequency headerless
    )
  }

  if (filterGroupName.value) {
    filtered = filtered.filter(dataItem =>
      dataItem.group_name && dataItem.group_name.toLowerCase().includes(filterGroupName.value.toLowerCase())
    )
  }

  if (filterUploadTimeRange.value && filterUploadTimeRange.value.length === 2) {
    const [startTime, endTime] = filterUploadTimeRange.value.map(date => new Date(date));
    filtered = filtered.filter(dataItem => {
      const uploadTime = new Date(dataItem.upload_time);
      return uploadTime >= startTime && uploadTime <= endTime;
    });
  }

  if (filterColumnsCountMin.value !== null) {
    filtered = filtered.filter(dataItem =>
      dataItem.columns_count >= filterColumnsCountMin.value
    )
  }

  if (filterColumnsCountMax.value !== null) {
    filtered = filtered.filter(dataItem =>
      dataItem.columns_count <= filterColumnsCountMax.value
    )
  }

  return filtered
})

const paginatedDataList = computed(() => {
  return filteredData.value.slice((currentPage.value - 1) * pageSize.value, currentPage.value * pageSize.value)
})

const totalData = computed(() => {
  return filteredData.value.length
})

// 监听 selectedDataForConfirmation 变化，更新 confirmForm.data_ids
watch(selectedDataForConfirmation, (newVal) => {
  confirmForm.value.data_ids = newVal.map(d => d.data_id);
}, { deep: true });

// 方法
const refreshData = async () => {
  loading.value = true
  try {
    const response = await dataAPI.getDataList()
    const dataSummaries = response.data_ids || []
    
    dataList.value = dataSummaries.map(summary => ({
      data_id: summary.data_id,
      records: summary.records || 0,
      columns_count: summary.columns_count || 0,
      group_name: summary.group_name,
      upload_time: summary.upload_time,
      columns: summary.columns,
      schema_applied: summary.schema_applied,
      version: summary.version, // Add version
      last_modified_at: summary.last_modified_at, // Add last_modified_at
      ...summary
    }));
    
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('获取数据列表失败')
    console.error('获取数据列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  currentPage.value = 1 // Reset to first page on filter change
}

const handleSearch = () => {
  currentPage.value = 1
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page) => {
  currentPage.value = page
}

const handleRowClick = (row) => {
  viewDataDetail(row.data_id);
};

const viewDataDetail = async (dataId) => {
  try {
    loading.value = true;
    const detail = await dataAPI.getDataDetails(dataId);
    
    selectedData.value = dataList.value.find(d => d.data_id === dataId);
    dataDetailData.value = detail;
    showDataDetail.value = true;
    activeTab.value = 'basic';
  } catch (error) {
    ElMessage.error('获取数据详情失败');
    console.error('获取数据详情失败:', error);
  } finally {
    loading.value = false;
  }
};

const visualizeData = (dataId) => {
  console.log('visualizeData called with dataId:', dataId);
  router.push({
    path: '/analysis/visualization',
    query: { dataId }
  });
};

const cleanData = (dataId) => {
  console.log('cleanData called with dataId:', dataId);
  router.push({
    path: '/data/clean',
    query: { dataId }
  });
};

const extractFeatures = (dataId) => {
  console.log('extractFeatures called with dataId:', dataId);
  router.push({
    path: '/analysis/feature-engineering',
    query: { dataId }
  });
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString('zh-CN');
};

// 处理表格多选
const handleSelectionChange = (selection) => {
  selectedDataForConfirmation.value = selection;
};

// 处理确认数据按钮点击
const handleConfirmData = async () => {
  if (selectedDataForConfirmation.value.length === 0) {
    ElMessage.warning('请选择至少一条数据进行确认。');
    return;
  }

  confirmForm.value.data_ids = selectedDataForConfirmation.value.map(d => d.data_id);
  showConfirmDialog.value = true;
};

// 从确认列表中移除数据
const removeDataFromConfirmation = (dataIdToRemove) => {
  selectedDataForConfirmation.value = selectedDataForConfirmation.value.filter(
    d => d.data_id !== dataIdToRemove
  );
};

// 重置确认对话框
const resetConfirmDialog = () => {
  confirmForm.value = {
    data_ids: [],
  };
};

// 提交确认
const submitConfirmation = async () => {
  if (confirmForm.value.data_ids.length === 0) {
    ElMessage.error('请选择要确认的数据。');
    return;
  }

  loading.value = true;
  try {
    // For simplified confirmation, always send has_header as true and schema_definition as null for now
    const payload = {
      data_ids: confirmForm.value.data_ids,
    };

    const response = await dataAPI.confirmData(payload);
    ElMessage.success(response.message);
    showConfirmDialog.value = false;
    refreshData(); // 刷新数据列表以显示确认状态
  } catch (error) {
    ElMessage.error('数据确认失败: ' + (error.response?.data?.detail || error.message));
    console.error('数据确认失败:', error);
  } finally {
    loading.value = false;
  }
};

const handleFormatData = () => {
  if (selectedDataForConfirmation.value.length === 0) {
    ElMessage.warning('请选择至少一条数据进行格式化。');
    return;
  }
  showFormatDialog.value = true; // Open the format dialog
};

const handleBatchDelete = async () => {
  if (selectedDataForConfirmation.value.length === 0) {
    ElMessage.warning('请选择至少一条数据进行删除。');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedDataForConfirmation.value.length} 条数据吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    loading.value = true;
    const dataIdsToDelete = selectedDataForConfirmation.value.map(d => d.data_id);
    const payload = { data_ids: dataIdsToDelete };
    
    const response = await dataAPI.deleteDataBatch(payload);
    ElMessage.success(response.message);
    console.log('Batch Delete Response:', response);

    refreshData(); // Refresh data list after deletion
  } catch (error) {
    if (error !== 'cancel') { // User clicked cancel, no error
      ElMessage.error('批量删除失败: ' + (error.response?.data?.detail || error.message));
      console.error('批量删除失败:', error);
    }
  } finally {
    loading.value = false;
  }
};


onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.data-list {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-section {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}

.data-detail {
  min-height: 400px;
}

.data-preview h4 {
  color: #409EFF;
  margin: 15px 0 10px 0;
}

.data-preview p {
  margin: 5px 0;
  color: #606266;
  font-size: 14px;
}

:deep(.el-table .el-table__row) {
  cursor: pointer;
}

:deep(.el-table .el-table__row:hover) {
  background-color: #f5f7fa;
}

:deep(.el-dialog__body) {
  padding: 10px 20px 20px;
}

:deep(.el-tabs__content) {
  padding: 20px 0;
}
</style>
