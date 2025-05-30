<template>
  <el-dialog
    v-model="dialogVisible"
    title="格式化项目数据"
    width="50%"
    top="10vh"
    @close="handleClose"
  >
    <el-form :model="formatForm" label-width="250px">
      <el-form-item label="已选数据版本">
        <el-tag
          v-for="version in selectedVersions"
          :key="version.id"
          size="small"
          style="margin-right: 8px; margin-bottom: 8px;"
        >
          {{ version.file_identifier }} (v{{ version.version }})
        </el-tag>
      </el-form-item>

      <el-form-item label="转换为带标题数据">
        <el-switch v-model="formatForm.convertToHeadered" />
        <el-tooltip
          class="box-item"
          effect="dark"
          content="将无标题数据转换为带标题数据，需要选择一个数据模式。"
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

      <!-- Dynamically render value column name inputs for each selected high-frequency wide data -->
      <template v-if="formatForm.convertToHeadered && selectedHighFrequencyVersions.length > 0">
        <el-form-item
          v-for="version in selectedHighFrequencyVersions"
          :key="version.id"
          :label="`${version.display_name || version.file_identifier} (v${version.version}) 值列名称`"
        >
          <el-input
            :model-value="formatForm.dataValueColumnNames.get(version.entity_id)"
            @update:model-value="val => formatForm.dataValueColumnNames.set(version.entity_id, val)"
            placeholder="例如：value"
          />
          <!-- Add a class to the el-form-item to control label width if needed -->
          <el-tooltip
            class="box-item"
            effect="dark"
            content="指定高频宽表转换后的值列名称。"
            placement="right"
          >
            <el-icon style="margin-left: 8px;"><InfoFilled /></el-icon>
          </el-tooltip>
        </el-form-item>
      </template>

      <el-form-item label="新版本备注">
        <el-input type="textarea" v-model="formatForm.notes" placeholder="例如：应用模式X，转换为带标题数据" />
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
import { projectAPI, schemaAPI } from '@/api'; // Use projectAPI and schemaAPI

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  projectId: {
    type: Number,
    required: true
  },
  selectedVersions: { // Now expects selected versions (from VersionHistoryResponse)
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
  dataValueColumnNames: new Map(), // Stores {entity_id: valueColumnName} for high-frequency wide data
  notes: '' // Notes for the new version
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
    // Fetch schemas for the current project
    const response = await schemaAPI.getSchemas(props.projectId);
    availableSchemas.value = response || [];
  } catch (error) {
    console.error('Failed to load data schemas:', error);
    ElMessage.error('Failed to load data schemas');
  }
};

const isSelectedSchemaHighFrequency = computed(() => {
  if (!formatForm.selectedSchemaId || !availableSchemas.value.length) {
    return false;
  }
  const selectedSchema = availableSchemas.value.find(s => s.id === formatForm.selectedSchemaId);
  return selectedSchema && selectedSchema.schema_type === 'high_frequency_wide';
});

const selectedHighFrequencyVersions = computed(() => {
  if (!formatForm.convertToHeadered || !isSelectedSchemaHighFrequency.value) {
    return [];
  }
  // Filter selectedVersions to only include those that are high-frequency wide
  // For simplicity, we assume all selected versions are intended to be formatted with the selected schema
  // and thus, if the selected schema is high_frequency_wide, all selected versions are treated as such.
  // In a more complex scenario, you might need to check each version's original schema or type.
  return props.selectedVersions.filter(version => {
    // Initialize valueColumnName for this version if not already set
    if (!formatForm.dataValueColumnNames.has(version.entity_id)) {
      formatForm.dataValueColumnNames.set(version.entity_id, 'value'); // Default value
    }
    return true; // All selected versions are considered for individual value column names
  });
});

const resetForm = () => {
  formatForm.convertToHeadered = false;
  formatForm.selectedSchemaId = null;
  formatForm.valueColumnName = 'value';
  formatForm.notes = '';
};

const handleClose = () => {
  dialogVisible.value = false;
};

const submitFormat = async () => {
  if (formatForm.convertToHeadered && !formatForm.selectedSchemaId) {
    ElMessage.warning('Please select a data schema to convert to headered data.');
    return;
  }

  loading.value = true;
  try {
    // Prepare payload for each selected data entity
    const dataEntityIdsToFormat = props.selectedVersions.map(v => v.entity_id);

    const dataSpecificValueColumns = Array.from(formatForm.dataValueColumnNames.entries()).map(([data_id, value_column_name]) => ({
      data_id,
      value_column_name
    }));

    const payload = {
      data_ids: dataEntityIdsToFormat,
      convert_to_headered: formatForm.convertToHeadered,
      schema_id: formatForm.selectedSchemaId,
      data_specific_value_columns: (formatForm.convertToHeadered && isSelectedSchemaHighFrequency.value) ? dataSpecificValueColumns : undefined,
      notes: formatForm.notes
    };
    
    // Call projectAPI.formatProjectData (new backend endpoint)
    const response = await projectAPI.formatProjectData(props.projectId, payload); 
    ElMessage.success(response.message);
    console.log('Format Response:', response);

    emit('formattedSuccess');
    handleClose();
  } catch (error) {
    ElMessage.error('Data formatting failed: ' + (error.response?.data?.detail || error.message));
    console.error('Data formatting failed:', error);
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
