<template>
  <div class="data-list-container project-data-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ pageTitle }}</span>
          <div class="header-actions">
            <el-button type="primary" @click="fetchProjectVersions" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-dropdown trigger="click" style="margin-left: 10px;">
              <el-button type="info" :disabled="selectedVersions.length === 0">
                批量操作<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleBatchDelete">
                    <el-icon><Delete /></el-icon>批量删除
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleBatchFormat">
                    <el-icon><MagicStick /></el-icon>批量格式化
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleBatchRollbackToPrevious">
                    <el-icon><RefreshLeft /></el-icon>批量回滚到上一版本
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </template>

      <div v-if="projectId" class="project-context-info">
        <el-tag type="info">项目ID: {{ projectId }}</el-tag>
      </div>

      <!-- 筛选部分 -->
      <div class="filter-section">
        <el-row :gutter="20" align="middle">
          <el-col :span="8">
            <el-input
              v-model="filterEntityId"
              placeholder="按数据实体ID筛选"
              clearable
              @input="handleFilterChange"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="8">
            <el-input
              v-model="filterNotes"
              placeholder="按备注筛选"
              clearable
              @input="handleFilterChange"
            >
              <template #prefix>
                <el-icon><EditPen /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="8">
            <el-date-picker
              v-model="filterCreatedAtRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              @change="handleFilterChange"
              value-format="YYYY-MM-DDTHH:mm:ss"
            />
          </el-col>
        </el-row>
        <el-row :gutter="20" align="middle" style="margin-top: 15px;">
          <el-col :span="8">
            <el-input-number
              v-model="filterVersionMin"
              :min="0"
              placeholder="最小版本"
              @change="handleFilterChange"
              controls-position="right"
              style="width: 120px;"
            />
            <span style="margin: 0 5px;">-</span>
            <el-input-number
              v-model="filterVersionMax"
              :min="0"
              placeholder="最大版本"
              @change="handleFilterChange"
              controls-position="right"
              style="width: 120px;"
            />
          </el-col>
          <el-col :span="8">
            <el-select v-model="filterEntityType" placeholder="按实体类型筛选" clearable @change="handleFilterChange">
              <el-option label="数据" value="data"></el-option>
              <el-option label="清洗数据" value="cleaned_data"></el-option>
              <el-option label="特征" value="features"></el-option>
              <el-option label="模型" value="model"></el-option>
            </el-select>
          </el-col>
          <el-col :span="8">
            <el-switch
              v-model="showLatestVersionsOnly"
              active-text="仅显示最新版本"
              inactive-text="显示所有版本"
              @change="handleFilterChange"
            />
          </el-col>
        </el-row>
      </div>

      <!-- 数据版本表格 -->
      <el-table :data="paginatedFilteredVersions" v-loading="loading" style="width: 100%" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <!-- <el-table-column prop="id" label="版本ID" width="100" /> --> <!-- Removed as per user request -->
        <el-table-column label="名称" width="300">
          <template #default="{ row }">
            <el-input
              v-model="row.display_name"
              type="text"
              :rows="1"
              placeholder="添加名称"
              @blur="saveDisplayNameDirectly(row)"
              @keyup.enter="saveDisplayNameDirectly(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本号" width="100" />
        <el-table-column prop="entity_type" label="实体类型" width="120">
            <template #default="{ row }">
                <el-tag :type="row.entity_type === 'data' ? 'success' : (row.entity_type === 'model' ? 'primary' : 'info')">
                    {{ row.entity_type === 'data' ? '数据' : (row.entity_type === 'cleaned_data' ? '清洗数据' : (row.entity_type === 'features' ? '特征' : '模型')) }}
                </el-tag>
            </template>
        </el-table-column>
        <el-table-column label="备注/描述">
          <template #default="{ row }">
            <el-input
              v-model="row.notes"
              type="textarea"
              :rows="1"
              placeholder="添加备注"
              @blur="saveNotesDirectly(row)"
              @keyup.enter="saveNotesDirectly(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="版本日期" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button 
              size="small" 
              type="primary" 
              @click="viewDataVersion(row)"
              v-if="row.entity_type === 'data' || row.entity_type === 'cleaned_data' || row.entity_type === 'features'">
              查看数据
            </el-button>
            <el-button 
              size="small" 
              type="warning" 
              @click="rollbackData(row.entity_id, row.version)"
              v-if="row.entity_type === 'data' || row.entity_type === 'cleaned_data'">
              回滚
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container" v-if="totalVersions > 0">
        <el-pagination
          :current-page="currentPage"
          @update:current-page="handleCurrentChange"
          :page-size="pageSize"
          @update:page-size="handleSizeChange"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalVersions"
          layout="total, sizes, prev, pager, next, jumper"
        />
      </div>

      <div v-if="error" class="error-message">
        <el-alert type="error" :title="error" show-icon :closable="false"></el-alert>
      </div>
       <div v-if="!loading && versions.length === 0 && !error" class="empty-state">
        <el-empty description="此项目暂无数据版本。"></el-empty>
      </div>
    </el-card>

    <!-- 数据详情/查看对话框 -->
    <el-dialog v-model="showDetailDialog" title="查看数据版本" width="80%" top="5vh">
      <div v-if="selectedVersionData">
        <p><strong>项目ID:</strong> {{ selectedVersionData.project_id }}</p>
        <p><strong>数据实体ID:</strong> {{ selectedVersionData.entity_id }}</p>
        <p><strong>文件名:</strong> {{ selectedVersionData.file_identifier }}</p>
        <p><strong>版本号:</strong> {{ selectedVersionData.version }}</p>
        <p><strong>备注:</strong> {{ selectedVersionData.notes || '无' }}</p>
        <p><strong>创建日期:</strong> {{ formatDate(selectedVersionData.created_at) }}</p>
        <p v-if="(selectedVersionData.rows !== null && selectedVersionData.columns !== null) || (selectedVersionData.version_metadata && selectedVersionData.version_metadata.shape)">
          <strong>文件维度:</strong> 
          {{ selectedVersionData.rows !== null ? selectedVersionData.rows : (selectedVersionData.version_metadata && selectedVersionData.version_metadata.shape ? selectedVersionData.version_metadata.shape[0] : 'N/A') }} 行 × 
          {{ selectedVersionData.columns !== null ? selectedVersionData.columns : (selectedVersionData.version_metadata && selectedVersionData.version_metadata.shape ? selectedVersionData.version_metadata.shape[1] : 'N/A') }} 列
        </p>
        <p v-if="selectedVersionData.size_bytes !== null || (selectedVersionData.version_metadata && selectedVersionData.version_metadata.size_bytes !== null)">
          <strong>文件大小:</strong> {{ formatBytes(selectedVersionData.size_bytes !== null ? selectedVersionData.size_bytes : selectedVersionData.version_metadata.size_bytes) }}
        </p>
        
        <el-divider>数据预览</el-divider>
        <div v-loading="previewLoading">
          <el-alert v-if="previewError" type="error" :title="previewError" show-icon :closable="false"></el-alert>
          <div v-else>
            <p v-if="previewData.data.length > 0" class="data-dimensions">
              <strong>预览数据维度:</strong> {{ previewData.data.length }} 行 × {{ previewData.columns.length }} 列
            </p>
            <el-table :data="previewData.data" style="width: 100%;" max-height="300">
              <el-table-column v-for="column in previewData.columns" :key="column" :prop="column" :label="column" />
              <template v-if="previewData.data.length === 0 && !previewLoading">
                <el-empty description="无数据可预览"></el-empty>
              </template>
            </el-table>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 项目数据格式化对话框 -->
    <ProjectDataFormatDialog
      :visible="showFormatDialog"
      :project-id="Number(projectId)"
      :selected-versions="selectedVersions"
      @update:visible="showFormatDialog = $event"
      @formattedSuccess="fetchProjectVersions"
    />

    <!-- 回滚对话框 -->
    <el-dialog v-model="showRollbackDialog" title="回滚数据" width="60%">
      <p>您确定要将数据实体 <strong>{{ rollbackTarget.entityId }}</strong> 回滚到版本 <strong>{{ rollbackTarget.version }}</strong> 吗？</p>
      <el-alert type="info" title="回滚功能增强提示" description="此回滚对话框将更新以显示所有可用版本供选择。" :closable="false"></el-alert>
      <!-- Placeholder for future version list for rollback -->
      <div class="rollback-versions-list">
        <h4>可用版本:</h4>
        <el-table :data="entityVersionsForRollback" style="width: 100%;" max-height="250">
          <el-table-column prop="version" label="版本号" width="80"></el-table-column>
          <el-table-column prop="file_identifier" label="文件名"></el-table-column>
          <el-table-column prop="notes" label="备注"></el-table-column>
          <el-table-column label="创建日期" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="选择" width="80">
            <template #default="{ row }">
              <el-radio v-model="selectedRollbackVersion" :label="row.version">选择</el-radio>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="entityVersionsForRollback.length === 0 && !previewLoading" class="empty-state">
          <el-empty description="无可用版本"></el-empty>
        </div>
      </div>
      <el-form :model="rollbackForm" label-width="80px" style="margin-top: 20px;">
        <el-form-item label="备注">
          <el-input type="textarea" v-model="rollbackForm.notes"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showRollbackDialog = false">取消</el-button>
          <el-button type="primary" @click="confirmRollback" :disabled="!selectedRollbackVersion">回滚</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑备注对话框 -->
    <!-- Removed as notes are now directly editable -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, reactive } from 'vue';
import { ElMessage, ElMessageBox, ElEmpty, ElRadio, ElDivider, ElDropdown, ElDropdownMenu, ElDropdownItem } from 'element-plus'; // Added ElDropdown, ElDropdownMenu, ElDropdownItem
import { projectAPI } from '@/api';
import { Refresh, Delete, Search, EditPen, MagicStick, ArrowDown, RefreshLeft } from '@element-plus/icons-vue'; // Added ArrowDown, RefreshLeft
import ProjectDataFormatDialog from '@/components/ProjectDataFormatDialog.vue';

const props = defineProps({
  projectId: {
    type: [String, Number],
    required: true 
  }
});

const versions = ref([]);
const loading = ref(true);
const error = ref(null);
const currentPage = ref(1);
const pageSize = ref(10);
const totalVersions = ref(0);
const selectedVersions = ref([]);

const filterEntityId = ref('');
const filterNotes = ref('');
const filterCreatedAtRange = ref(null);
const filterVersionMin = ref(null);
const filterVersionMax = ref(null);
const filterEntityType = ref(null);
const showLatestVersionsOnly = ref(true); // Default to true to show only latest versions

const showDetailDialog = ref(false);
const selectedVersionData = ref(null);
const previewData = ref({ columns: [], data: [] }); // To hold the data for preview
const previewLoading = ref(false);
const previewError = ref(null);

const showFormatDialog = ref(false);
const showRollbackDialog = ref(false);
const rollbackTarget = reactive({
  entityId: null,
  version: null // This will be the version from which rollback was initiated, not necessarily the target
});
const rollbackForm = reactive({
  notes: ""
});
const selectedRollbackVersion = ref(null); // To hold the version selected for rollback
const entityVersionsForRollback = ref([]); // To hold versions for the specific entity being rolled back

// Removed showEditNotesDialog and editNotesForm as notes are now directly editable

const pageTitle = computed(() => `Data Versions for Project ID: ${props.projectId}`);

// New computed property to get only the latest versions for each entity_id
const latestVersions = computed(() => {
  const latestMap = new Map(); // Map to store the latest version for each entity_id

  // Iterate through all versions to find the latest for each entity
  versions.value.forEach(v => {
    if (!latestMap.has(v.entity_id) || v.version > latestMap.get(v.entity_id).version) {
      latestMap.set(v.entity_id, v);
    }
  });

  // Convert map values back to an array
  return Array.from(latestMap.values());
});

const filteredVersions = computed(() => {
  let sourceList = showLatestVersionsOnly.value ? latestVersions.value : versions.value;
  let filtered = sourceList;

  if (filterEntityId.value) {
    filtered = filtered.filter(v => v.entity_id.toLowerCase().includes(filterEntityId.value.toLowerCase()));
  }
  if (filterNotes.value) {
    filtered = filtered.filter(v => v.notes && v.notes.toLowerCase().includes(filterNotes.value.toLowerCase()));
  }
  if (filterCreatedAtRange.value && filterCreatedAtRange.value.length === 2) {
    const [startDate, endDate] = filterCreatedAtRange.value.map(date => new Date(date));
    filtered = filtered.filter(v => {
      const createdAt = new Date(v.created_at);
      return createdAt >= startDate && createdAt <= endDate;
    });
  }
  // Apply version filters only if not showing latest versions only
  if (!showLatestVersionsOnly.value) {
    if (filterVersionMin.value !== null) {
      filtered = filtered.filter(v => v.version >= filterVersionMin.value);
    }
    if (filterVersionMax.value !== null) {
      filtered = filtered.filter(v => v.version <= filterVersionMax.value);
    }
  } else {
    // If showing latest versions only, clear version filters as they don't apply meaningfully
    // This prevents unexpected filtering if user toggles back and forth
    if (filterVersionMin.value !== null || filterVersionMax.value !== null) {
      filterVersionMin.value = null;
      filterVersionMax.value = null;
    }
  }

  if (filterEntityType.value) {
    filtered = filtered.filter(v => v.entity_type === filterEntityType.value);
  }

  return filtered;
});

const paginatedFilteredVersions = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return filteredVersions.value.slice(start, end);
});

const fetchProjectVersions = async () => {
  loading.value = true;
  error.value = null;
  const currentProjectId = Number(props.projectId);

  if (isNaN(currentProjectId) || currentProjectId <= 0) {
    error.value = "Invalid Project ID. Cannot load data versions.";
    versions.value = [];
    totalVersions.value = 0;
    loading.value = false;
    return;
  }

  try {
    // Fetch all versions from the backend, then filter in frontend
    // This simplifies backend pagination and allows frontend to handle "latest only" view
    const response = await projectAPI.getProjectVersions(currentProjectId, 0, 1000); // Fetch a large enough limit or implement proper backend pagination for all versions
    if (response && typeof response === 'object' && Array.isArray(response.items)) {
        versions.value = response.items;
        // totalVersions is now based on the filtered list, not the raw fetched list
        // It will be updated by the watch on filteredVersions
    } else {
        versions.value = [];
        console.warn("Unexpected response structure for project versions:", response);
    }

  } catch (err) {
    console.error(`Failed to fetch versions for project ${currentProjectId}:`, err);
    error.value = `Failed to load data versions for project ${currentProjectId}. Please try again later.`;
    versions.value = [];
  } finally {
    loading.value = false;
  }
};

// Watch filteredVersions to update totalVersions for pagination
watch(filteredVersions, (newFilteredVersions) => {
  totalVersions.value = newFilteredVersions.length;
}, { immediate: true });

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' };
  return new Date(dateString).toLocaleString(undefined, options);
};

const viewDataVersion = async (versionEntry) => {
  selectedVersionData.value = versionEntry;
  previewData.value = { columns: [], data: [] }; // Reset preview data
  previewError.value = null;
  previewLoading.value = true;
  showDetailDialog.value = true;

  try {
    const response = await projectAPI.viewProjectDataVersion(
      Number(versionEntry.project_id),
      versionEntry.entity_id,
      versionEntry.version
    );
    if (response && response.data && response.columns) {
      previewData.value.columns = response.columns;
      previewData.value.data = response.data;
      ElMessage.success(`成功加载数据预览。`);
    } else {
      previewError.value = '数据预览响应结构异常。';
      ElMessage.error('数据预览加载失败：响应结构异常。');
    }
  } catch (err) {
    previewError.value = `加载数据预览失败: ${err.response?.data?.detail || err.message}`;
    ElMessage.error(`加载数据预览失败: ${err.response?.data?.detail || err.message}`);
    console.error('加载数据预览失败:', err);
  } finally {
    previewLoading.value = false;
  }
};

const handleSelectionChange = (selection) => {
  selectedVersions.value = selection;
};

const handleFilterChange = () => {
  currentPage.value = 1;
};

const handleBatchDelete = async () => {
  if (selectedVersions.value.length === 0) {
    ElMessage.warning('请选择至少一个数据版本进行删除。');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `您确定要删除选定的 ${selectedVersions.value.length} 个数据版本吗？此操作不可撤销。`,
      '警告',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    loading.value = true;
    const currentProjectId = Number(props.projectId);
    if (isNaN(currentProjectId) || currentProjectId <= 0) {
      ElMessage.error('项目ID无效。无法删除数据版本。');
      loading.value = false;
      return;
    }

    const deletePayload = {
      data_ids: selectedVersions.value.map(v => v.entity_id) // Send only entity_ids for batch deletion
    };

    const response = await projectAPI.deleteProjectDataVersions(currentProjectId, deletePayload);

    let successCount = 0;
    let failCount = 0;
    const failedEntities = [];

    for (const entityId in response) {
      if (response[entityId]) {
        successCount++;
      } else {
        failCount++;
        failedEntities.push(entityId);
      }
    }

    if (successCount > 0) {
      ElMessage.success(`成功删除 ${successCount} 个数据实体。`);
    }
    if (failCount > 0) {
      ElMessage.error(`删除失败 ${failCount} 个数据实体: ${failedEntities.join(', ')}。`);
    }

    fetchProjectVersions();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败: ' + (error.response?.data?.detail || error.message));
      console.error('批量删除失败:', error);
    }
  } finally {
    loading.value = false;
  }
};

const handleBatchFormat = () => {
  if (selectedVersions.value.length === 0) {
    ElMessage.warning('请选择至少一个数据版本进行格式化。');
    return;
  }
  const formatableVersions = selectedVersions.value.filter(v => v.entity_type === 'data' || v.entity_type === 'cleaned_data');
  if (formatableVersions.length === 0) {
    ElMessage.warning('所选版本不可格式化（只有“数据”或“清洗数据”可以格式化）。');
    return;
  }
  showFormatDialog.value = true;
};

const handleBatchRollbackToPrevious = async () => {
  if (selectedVersions.value.length === 0) {
    ElMessage.warning('请选择至少一个数据版本进行批量回滚。');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `您确定要将选定的 ${selectedVersions.value.length} 个数据实体回滚到各自的上一版本吗？这将为每个实体创建一个新版本。`,
      '确认批量回滚',
      {
        confirmButtonText: '批量回滚',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true,
      }
    );

    loading.value = true;
    const currentProjectId = Number(props.projectId);
    if (isNaN(currentProjectId) || currentProjectId <= 0) {
      ElMessage.error('项目ID无效。无法执行批量回滚。');
      loading.value = false;
      return;
    }

    const rollbackPromises = selectedVersions.value.map(async (versionEntry) => {
      // Fetch all versions for this specific entity to find the previous one
      const entityVersions = await projectAPI.getVersionsForEntity(currentProjectId, versionEntry.entity_id);
      const sortedVersions = entityVersions.sort((a, b) => b.version - a.version); // Descending
      
      const currentIndex = sortedVersions.findIndex(v => v.id === versionEntry.id);
      if (currentIndex === -1 || currentIndex === sortedVersions.length - 1) {
        // If it's the oldest version or not found, cannot rollback to previous
        ElMessage.warning(`实体 ${versionEntry.entity_id} 版本 ${versionEntry.version} 没有更早的版本可回滚。`);
        return Promise.resolve(null); // Resolve with null to indicate no action
      }
      
      const previousVersion = sortedVersions[currentIndex + 1]; // The next one in descending order is the previous
      
      const notes = `批量回滚到版本 ${previousVersion.version} (从版本 ${versionEntry.version} 回滚)`;
      return projectAPI.rollbackProjectDataVersion(
        currentProjectId,
        versionEntry.entity_id,
        previousVersion.version, // Rollback to the previous version
        { notes: notes }
      );
    });

    const results = await Promise.allSettled(rollbackPromises);
    let successCount = 0;
    let failCount = 0;

    results.forEach(result => {
      if (result.status === 'fulfilled' && result.value !== null) {
        successCount++;
      } else {
        failCount++;
      }
    });

    if (successCount > 0) {
      ElMessage.success(`成功批量回滚 ${successCount} 个数据实体。`);
    }
    if (failCount > 0) {
      ElMessage.error(`批量回滚失败 ${failCount} 个数据实体。请查看控制台了解详情。`);
    }
    
    fetchProjectVersions(); // Refresh the main list after batch operations
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量回滚失败: ' + (error.response?.data?.detail || error.message));
      console.error('批量回滚失败:', error);
    }
  } finally {
    loading.value = false;
  }
};

const fetchEntityVersionsForRollback = async (projectId, entityId) => {
  try {
    const response = await projectAPI.getVersionsForEntity(projectId, entityId);
    if (response && Array.isArray(response)) {
      entityVersionsForRollback.value = response.sort((a, b) => b.version - a.version);
    } else {
      entityVersionsForRollback.value = [];
      console.warn("Unexpected response structure for entity versions for rollback:", response);
    }
  } catch (err) {
    console.error(`Failed to fetch versions for entity ${entityId}:`, err);
    ElMessage.error(`无法加载实体 ${entityId} 的版本。`);
    entityVersionsForRollback.value = [];
  }
};

const rollbackData = async (entityId, version) => {
  rollbackTarget.entityId = entityId;
  rollbackTarget.version = version;
  selectedRollbackVersion.value = null;
  rollbackForm.notes = "";

  await fetchEntityVersionsForRollback(Number(props.projectId), entityId);

  showRollbackDialog.value = true;
};

const confirmRollback = async () => {
  if (!selectedRollbackVersion.value) {
    ElMessage.warning('请选择一个要回滚到的版本。');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `您确定要将数据实体 <strong>${rollbackTarget.entityId}</strong> 回滚到版本 <strong>${selectedRollbackVersion.value}</strong> 吗？这将在当前版本的基础上创建一个与所选版本相同的新版本。`,
      '确认回滚',
      {
        confirmButtonText: '回滚',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true,
      }
    );

    loading.value = true;
    const currentProjectId = Number(props.projectId);
    if (isNaN(currentProjectId) || currentProjectId <= 0) {
      ElMessage.error('项目ID无效。无法回滚数据。');
      loading.value = false;
      return;
    }

    const response = await projectAPI.rollbackProjectDataVersion(
      currentProjectId,
      rollbackTarget.entityId,
      selectedRollbackVersion.value,
      { notes: rollbackForm.notes || `回滚到版本 ${selectedRollbackVersion.value}` }
    );

    if (response) {
      ElMessage.success(`数据实体 ${rollbackTarget.entityId} 已成功回滚到版本 ${selectedRollbackVersion.value}。`);
      showRollbackDialog.value = false;
      fetchProjectVersions();
    } else {
      ElMessage.error('数据回滚失败。');
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('数据回滚失败: ' + (error.response?.data?.detail || error.message));
      console.error('数据回滚失败:', error);
    }
  } finally {
    loading.value = false;
  }
};

const saveNotesDirectly = async (row) => {
  try {
    // Temporarily remove the check to force API call for debugging
    // const originalRow = versions.value.find(v => v.id === row.id);
    // if (originalRow && originalRow.notes === row.notes) {
    //   return;
    // }

    loading.value = true;
    const currentProjectId = Number(props.projectId);
    if (isNaN(currentProjectId) || currentProjectId <= 0) {
      ElMessage.error('项目ID无效。无法保存备注。');
      loading.value = false;
      return;
    }

    const response = await projectAPI.updateVersionNotes(currentProjectId, row.id, { notes: row.notes });

    if (response) {
      ElMessage.success('备注保存成功。');
      const index = versions.value.findIndex(v => v.id === row.id);
      if (index !== -1) {
        versions.value[index].notes = response.notes;
      }
    } else {
      ElMessage.error('备注保存失败。');
    }
  } catch (error) {
    ElMessage.error('备注保存失败: ' + (error.response?.data?.detail || error.message));
    console.error('备注保存失败:', error);
  } finally {
    loading.value = false;
  }
};

const saveDisplayNameDirectly = async (row) => {
  try {
    // Temporarily remove the check to force API call for debugging
    // const originalRow = versions.value.find(v => v.id === row.id);
    // if (originalRow && originalRow.display_name === row.display_name) {
    //   return;
    // }

    loading.value = true;
    const currentProjectId = Number(props.projectId);
    if (isNaN(currentProjectId) || currentProjectId <= 0) {
      ElMessage.error('项目ID无效。无法保存名称。');
      loading.value = false;
      return;
    }

    const response = await projectAPI.updateVersionDisplayName(currentProjectId, row.id, { display_name: row.display_name });

    if (response) {
      ElMessage.success('名称保存成功。');
      const index = versions.value.findIndex(v => v.id === row.id);
      if (index !== -1) {
        versions.value[index].display_name = response.display_name;
      }
    } else {
      ElMessage.error('名称保存失败。');
    }
  } catch (error) {
    ElMessage.error('名称保存失败: ' + (error.response?.data?.detail || error.message));
    console.error('名称保存失败:', error);
  } finally {
    loading.value = false;
  }
};

const handleSizeChange = (newSize) => {
  pageSize.value = newSize;
  currentPage.value = 1;
  fetchProjectVersions();
};

const handleCurrentChange = (newPage) => {
  currentPage.value = newPage;
  fetchProjectVersions();
};

watch(() => props.projectId, (newProjectId) => {
  if (newProjectId) {
    currentPage.value = 1;
    pageSize.value = 10;
    fetchProjectVersions();
  }
}, { immediate: true });

onMounted(() => {
  if (!props.projectId) {
     error.value = "项目ID缺失。无法加载数据版本。";
     loading.value = false;
     ElMessage.error("需要项目ID才能查看数据版本。");
  }
});

const formatBytes = (bytes, decimals = 2) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};
</script>

<style scoped>
.project-data-list {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-actions {
  display: flex;
  gap: 10px;
}
.project-context-info {
  margin-bottom: 20px;
  padding: 10px;
  background-color: #f4f4f5;
  border-radius: 4px;
  text-align: center;
}
.filter-section {
  margin-bottom: 20px;
}
.pagination-container {
  margin-top: 20px;
  text-align: right;
}
.error-message {
  margin-top: 20px;
}
.empty-state {
  margin-top: 20px;
  text-align: right;
}
.error-message {
  margin-top: 20px;
}
.empty-state {
  margin-top: 20px;
  text-align: center;
}
</style>
