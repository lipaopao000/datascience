<template>
  <el-dialog
    v-model="dialogVisible"
    title="数据格式化"
    width="50%"
    top="10vh"
    @close="handleClose"
  >
    <el-form :model="formatForm" label-width="150px">
      <el-form-item label="选中的数据ID">
        <el-tag
          v-for="dataId in selectedDataIds"
          :key="dataId"
          size="small"
          style="margin-right: 8px; margin-bottom: 8px;"
        >
          {{ dataId }}
        </el-tag>
      </el-form-item>

      <el-form-item label="转换为有表头数据">
        <el-switch v-model="formatForm.convertToHeadered" />
        <el-tooltip
          class="box-item"
          effect="dark"
          content="将无表头数据转换为有表头数据，需要选择一个数据模式。"
          placement="right"
        >
          <el-icon style="margin-left: 8px;"><InfoFilled /></el-icon>
        </el-tooltip>
      </el-form-item>

      <el-form-item label="选择数据模式" v-if="formatForm.convertToHeadered">
        <el-select v-model="formatForm.selectedSchemaId" placeholder="请选择一个数据模式" clearable>
          <el-option
            v-for="schema in availableSchemas"
            :key="schema.id"
            :label="schema.name"
            :value="schema.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="值列名 (高频宽表模式)" v-if="formatForm.convertToHeadered && isSelectedSchemaHighFrequency">
        <el-input v-model="formatForm.valueColumnName" placeholder="例如: value" />
        <el-tooltip
          class="box-item"
          effect="dark"
          content="为高频宽表模式转换后的值列指定名称。"
          placement="right"
        >
          <el-icon style="margin-left: 8px;"><InfoFilled /></el-icon>
        </el-tooltip>
      </el-form-item>
    </el-form>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="submitFormat" :loading="loading">
          格式化
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, onMounted, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { InfoFilled } from '@element-plus/icons-vue';
import { dataAPI, schemaAPI } from '@/api';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  selectedDataIds: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['update:visible', 'formattedSuccess']);

const dialogVisible = ref(props.visible);
const loading = ref(false);
const availableSchemas = ref([]);

const formatForm = reactive({
  convertToHeadered: false,
  selectedSchemaId: null,
  valueColumnName: 'value' // Default value column name
});

// Watch for changes in the visible prop
watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal;
  if (newVal) {
    loadSchemas();
    resetForm();
  }
});

// Watch for changes in dialogVisible (internal state)
watch(dialogVisible, (newVal) => {
  emit('update:visible', newVal);
});

const loadSchemas = async () => {
  try {
    const response = await schemaAPI.getSchemas();
    availableSchemas.value = response || [];
  } catch (error) {
    console.error('加载数据模式列表失败:', error);
    ElMessage.error('加载数据模式列表失败');
  }
};

const isSelectedSchemaHighFrequency = computed(() => {
  if (!formatForm.selectedSchemaId || !availableSchemas.value.length) {
    return false;
  }
  const selectedSchema = availableSchemas.value.find(s => s.id === formatForm.selectedSchemaId);
  return selectedSchema && selectedSchema.schema_type === 'high_frequency_wide';
});

const resetForm = () => {
  formatForm.convertToHeadered = false;
  formatForm.selectedSchemaId = null;
  formatForm.valueColumnName = 'value'; // Reset to default
};

const handleClose = () => {
  dialogVisible.value = false;
};

const submitFormat = async () => {
  if (formatForm.convertToHeadered && !formatForm.selectedSchemaId) {
    ElMessage.warning('请选择一个数据模式以转换为有表头数据。');
    return;
  }

  loading.value = true;
  try {
    const payload = {
      data_ids: props.selectedDataIds,
      convert_to_headered: formatForm.convertToHeadered,
      schema_id: formatForm.selectedSchemaId,
      value_column_name: (formatForm.convertToHeadered && isSelectedSchemaHighFrequency.value) ? formatForm.valueColumnName : undefined
    };
    
    const response = await dataAPI.formatData(payload); 
    ElMessage.success(response.message);
    console.log('Format Response:', response);

    emit('formattedSuccess');
    handleClose();
  } catch (error) {
    ElMessage.error('数据格式化失败: ' + (error.response?.data?.detail || error.message));
    console.error('数据格式化失败:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  if (props.visible) {
    loadSchemas();
  }
});
</script>

<style scoped>
/* Add styles here if needed */
</style>
