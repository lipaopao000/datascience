<template>
  <div class="data-schema-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据模式管理</span>
          <el-button type="primary" @click="handleAddSchema">
            <el-icon><Plus /></el-icon>
            新建模式
          </el-button>
        </div>
      </template>

      <el-table :data="schemas" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="模式名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="schema_type" label="模式类型" width="150">
          <template #default="{ row }">
            {{ row.schema_type === 'high_frequency_wide' ? '高频宽表' : '标准表' }}
          </template>
        </el-table-column>
        <el-table-column prop="columns" label="列数 (标准)" width="100">
          <template #default="{ row }">
            {{ row.schema_type === 'standard' ? (row.columns?.length || 0) : 'N/A' }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
           <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="handleEditSchema(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDeleteSchema(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-dialog v-model="dialogVisible" :title="dialogTitle" width="70%">
        <el-form :model="currentSchema" label-width="150px">
          <el-form-item label="模式名称">
            <el-input v-model="currentSchema.name" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="currentSchema.description" type="textarea" />
          </el-form-item>
          <el-form-item label="模式类型">
            <el-radio-group v-model="currentSchema.schema_type">
              <el-radio label="standard">标准表</el-radio>
              <el-radio label="high_frequency_wide">高频宽表</el-radio>
            </el-radio-group>
          </el-form-item>
          
          <div v-if="currentSchema.schema_type === 'standard'">
            <h4>列定义 (标准表)</h4>
            <el-table :data="currentSchema.columns" style="width: 100%">
              <el-table-column prop="name" label="列名">
                <template #default="{ row }">
                  <el-input v-model="row.name" placeholder="列名" />
                </template>
              </el-table-column>
              <el-table-column prop="type" label="数据类型">
                <template #default="{ row }">
                  <el-select v-model="row.type" placeholder="选择类型">
                    <el-option label="文本" value="string" />
                    <el-option label="数字" value="number" />
                    <el-option label="日期时间" value="datetime" />
                    <el-option label="布尔" value="boolean" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80">
                <template #default="{ $index }">
                  <el-button type="danger" size="small" @click="removeColumn($index)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-button @click="addColumn" style="margin-top: 10px;">添加列</el-button>
          </div>

          <div v-if="currentSchema.schema_type === 'high_frequency_wide'">
            <h4>列定义 (高频宽表)</h4>
            <el-form-item label="时间列索引">
              <el-input-number v-model="currentSchema.time_column_index" :min="0" placeholder="例如: 0" />
            </el-form-item>
            <el-form-item label="数据起始列索引">
              <el-input-number v-model="currentSchema.data_start_column_index" :min="0" placeholder="例如: 1" />
            </el-form-item>
            <el-form-item label="数据列数量">
              <el-input-number v-model="currentSchema.num_data_columns" :min="1" placeholder="例如: 50" />
            </el-form-item>
            <el-form-item label="数据列基础名称">
              <el-input v-model="currentSchema.data_column_base_name" placeholder="例如: value (将生成 value_1, value_2...)" />
            </el-form-item>
            <el-form-item label="采样率 (Hz)">
              <el-input-number v-model="currentSchema.sampling_rate_hz" :min="0.1" :step="0.1" placeholder="例如: 50.0" />
            </el-form-item>
          </div>

        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveSchema" :loading="saving">保存</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, defineProps } from 'vue'; // Import defineProps
import { ElMessage, ElMessageBox } from 'element-plus';
import { schemaAPI } from '@/api'; 

const props = defineProps({
  projectId: {
    type: Number,
    required: true
  }
});

const schemas = ref([]);
const loading = ref(false);
const saving = ref(false);

const dialogVisible = ref(false);
const dialogTitle = ref('');

const defaultStandardSchema = () => ({
  id: null,
  name: '',
  description: '',
  schema_type: 'standard',
  columns: [{ name: '', type: 'string' }],
  time_column_index: null,
  data_start_column_index: null,
  num_data_columns: null,
  data_column_base_name: null,
  sampling_rate_hz: null
});

const defaultHighFreqSchema = () => ({
  id: null,
  name: '',
  description: '',
  schema_type: 'high_frequency_wide',
  columns: null, // No individual columns for this type
  time_column_index: 0,
  data_start_column_index: 1,
  num_data_columns: 50,
  data_column_base_name: 'value',
  sampling_rate_hz: 50.0
});


const currentSchema = ref(defaultStandardSchema());

const isEditing = computed(() => !!currentSchema.value.id);

const loadSchemas = async () => {
  loading.value = true;
  try {
    // Explicitly convert projectId to Number
    const currentProjectId = Number(props.projectId);
    if (isNaN(currentProjectId) || currentProjectId <= 0) {
      ElMessage.error('无效的项目ID，无法加载数据模式。');
      schemas.value = [];
      return;
    }
    const response = await schemaAPI.getSchemas(currentProjectId, 0, 100);
    schemas.value = response || []; 
  } catch (error) {
    ElMessage.error('加载数据模式列表失败');
    console.error('加载数据模式列表失败:', error);
  } finally {
    loading.value = false;
  }
};

const handleAddSchema = () => {
  currentSchema.value = defaultStandardSchema();
  dialogTitle.value = '新建数据模式';
  dialogVisible.value = true;
};

const handleEditSchema = (schema) => {
  currentSchema.value = JSON.parse(JSON.stringify(schema)); 
  if (currentSchema.value.schema_type === 'high_frequency_wide' && !currentSchema.value.columns) {
    // Ensure high_freq fields are present if columns is null
    currentSchema.value.time_column_index = currentSchema.value.time_column_index ?? 0;
    currentSchema.value.data_start_column_index = currentSchema.value.data_start_column_index ?? 1;
    currentSchema.value.num_data_columns = currentSchema.value.num_data_columns ?? 50;
    currentSchema.value.data_column_base_name = currentSchema.value.data_column_base_name ?? 'value';
    currentSchema.value.sampling_rate_hz = currentSchema.value.sampling_rate_hz ?? 50.0;
  } else if (currentSchema.value.schema_type === 'standard' && !currentSchema.value.columns) {
    currentSchema.value.columns = [{ name: '', type: 'string' }];
  }
  dialogTitle.value = '编辑数据模式';
  dialogVisible.value = true;
};

const handleDeleteSchema = async (schema) => {
  try {
    await ElMessageBox.confirm(`确定删除模式 "${schema.name}" 吗?`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    loading.value = true;
    // Explicitly convert projectId to Number
    const currentProjectId = Number(props.projectId);
    if (isNaN(currentProjectId) || currentProjectId <= 0) {
      ElMessage.error('无效的项目ID，无法删除数据模式。');
      return;
    }
    await schemaAPI.deleteSchema(currentProjectId, schema.id); 
    ElMessage.success('删除成功');
    await loadSchemas(); 
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败');
      console.error('删除失败:', error);
    }
  } finally {
    loading.value = false;
  }
};

const addColumn = () => {
  if (currentSchema.value.schema_type === 'standard') {
    if (!currentSchema.value.columns) {
      currentSchema.value.columns = [];
    }
    currentSchema.value.columns.push({ name: '', type: 'string' });
  }
};

const removeColumn = (index) => {
   if (currentSchema.value.schema_type === 'standard' && currentSchema.value.columns) {
    currentSchema.value.columns.splice(index, 1);
  }
};

const saveSchema = async () => {
  saving.value = true;
  try {
    let payload = { ...currentSchema.value };
    if (payload.schema_type === 'standard') {
      payload.time_column_index = null;
      payload.data_start_column_index = null;
      payload.num_data_columns = null;
      payload.data_column_base_name = null;
      payload.sampling_rate_hz = null;
    } else if (payload.schema_type === 'high_frequency_wide') {
      payload.columns = null;
    }

    // Explicitly convert projectId to Number
    const currentProjectId = Number(props.projectId);
    if (isNaN(currentProjectId) || currentProjectId <= 0) {
      ElMessage.error('无效的项目ID，无法保存数据模式。');
      return;
    }

    if (isEditing.value) {
      await schemaAPI.updateSchema(currentProjectId, payload.id, payload);
    } else {
      await schemaAPI.createSchema(currentProjectId, payload);
    }
    ElMessage.success('保存成功');
    dialogVisible.value = false;
    await loadSchemas(); 
  } catch (error) {
    ElMessage.error(`保存失败: ${error.response?.data?.detail || error.message}`);
    console.error('保存失败:', error);
  } finally {
    saving.value = false;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString('zh-CN');
};

import { watch } from 'vue'; // Import watch

// ... existing code ...

watch(() => props.projectId, (newProjectId) => {
  if (newProjectId && newProjectId > 0) { // Only load if projectId is valid
    loadSchemas();
  } else {
    schemas.value = []; // Clear schemas if projectId is invalid
    ElMessage.warning('无效的项目ID，无法加载数据模式。');
  }
}, { immediate: true }); // Run immediately on component mount
</script>

<style scoped>
.data-schema-management {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
