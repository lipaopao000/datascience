<template>
  <div class="project-data-tab">
    <h3>Data Versions</h3>
    <el-button type="primary" @click="goToDataUpload" style="margin-bottom: 15px;">Upload New Data</el-button>

    <el-table :data="dataVersions" v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="Version ID" width="100"></el-table-column>
      <el-table-column prop="entity_id" label="Data Entity ID" width="200"></el-table-column>
      <el-table-column prop="version" label="Version" width="80"></el-table-column>
      <el-table-column prop="notes" label="Notes"></el-table-column>
      <el-table-column prop="file_identifier" label="File" width="180"></el-table-column>
      <el-table-column label="Created At" width="180">
        <template #default="scope">
          {{ formatDate(scope.row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="Actions" width="250">
        <template #default="scope">
          <el-button size="small" @click="viewData(scope.row.entity_id, scope.row.version)">View</el-button>
          <el-button size="small" @click="cleanData(scope.row.entity_id, scope.row.version)">Clean</el-button>
          <el-button size="small" @click="extractFeatures(scope.row.entity_id, scope.row.version)">Features</el-button>
          <el-button size="small" type="warning" @click="rollbackData(scope.row.entity_id, scope.row.version)">Rollback</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="error" class="error-message">
      <el-alert type="error" :title="error" show-icon :closable="false"></el-alert>
    </div>

    <!-- Data View Dialog -->
    <el-dialog v-model="showDataViewDialog" title="Data Preview" width="80%">
      <div v-if="currentDataPreview">
        <h4>Columns: {{ currentDataPreview.columns.join(', ') }}</h4>
        <p>Shape: ({{ currentDataPreview.shape[0] }} rows, {{ currentDataPreview.shape[1] }} columns)</p>
        <el-table :data="currentDataPreview.data" style="width: 100%; max-height: 400px; overflow-y: auto;" border>
          <el-table-column v-for="col in currentDataPreview.columns" :key="col" :prop="col" :label="col" show-overflow-tooltip></el-table-column>
        </el-table>
        <h4 style="margin-top: 20px;">Summary Statistics</h4>
        <el-table :data="formatSummaryStats(currentDataPreview.summary)" style="width: 100%; max-height: 300px; overflow-y: auto;" border>
          <el-table-column prop="stat" label="Statistic" width="120"></el-table-column>
          <el-table-column v-for="col in currentDataPreview.columns" :key="col" :prop="col" :label="col" show-overflow-tooltip></el-table-column>
        </el-table>
      </div>
      <div v-else-if="dataViewLoading">Loading data...</div>
      <div v-else-if="dataViewError" class="error-message">
        <el-alert type="error" :title="dataViewError" show-icon :closable="false"></el-alert>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showDataViewDialog = false">Close</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Data Cleaning Dialog -->
    <el-dialog v-model="showCleanDataDialog" title="Clean Data" width="500px">
      <el-form :model="cleaningForm" label-width="150px">
        <el-form-item label="Remove Outliers">
          <el-switch v-model="cleaningForm.remove_outliers"></el-switch>
        </el-form-item>
        <el-form-item label="Outlier Method" v-if="cleaningForm.remove_outliers">
          <el-select v-model="cleaningForm.outlier_method">
            <el-option label="IQR" value="iqr"></el-option>
            <el-option label="Z-score" value="zscore"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="Fill Missing Values">
          <el-switch v-model="cleaningForm.fill_missing"></el-switch>
        </el-form-item>
        <el-form-item label="Missing Method" v-if="cleaningForm.fill_missing">
          <el-select v-model="cleaningForm.missing_method">
            <el-option label="Interpolate" value="interpolate"></el-option>
            <el-option label="Mean" value="mean"></el-option>
            <el-option label="Median" value="median"></el-option>
            <el-option label="Zero" value="zero"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="Smooth Data">
          <el-switch v-model="cleaningForm.smooth_data"></el-switch>
        </el-form-item>
        <el-form-item label="Smooth Window" v-if="cleaningForm.smooth_data">
          <el-input-number v-model="cleaningForm.smooth_window" :min="1"></el-input-number>
        </el-form-item>
        <el-form-item label="Notes">
          <el-input type="textarea" v-model="cleaningForm.notes"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCleanDataDialog = false">Cancel</el-button>
          <el-button type="primary" @click="submitCleanData">Clean</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Feature Extraction Dialog -->
    <el-dialog v-model="showFeatureExtractionDialog" title="Extract Features" width="500px">
      <el-form :model="featureExtractionForm" label-width="150px">
        <el-form-item label="Feature Config (JSON)">
          <el-input type="textarea" v-model="featureExtractionForm.feature_config_json" :rows="5"></el-input>
          <small>Example: {"time_features": ["mean", "std"], "frequency_features": ["fft_mean"]}</small>
        </el-form-item>
        <el-form-item label="Notes">
          <el-input type="textarea" v-model="featureExtractionForm.notes"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showFeatureExtractionDialog = false">Cancel</el-button>
          <el-button type="primary" @click="submitFeatureExtraction">Extract</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Rollback Dialog -->
    <el-dialog v-model="showRollbackDialog" title="Rollback Data" width="400px">
      <p>Are you sure you want to rollback data entity <strong>{{ rollbackTarget.entityId }}</strong> to version <strong>{{ rollbackTarget.version }}</strong>?</p>
      <el-form :model="rollbackForm" label-width="80px">
        <el-form-item label="Notes">
          <el-input type="textarea" v-model="rollbackForm.notes"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showRollbackDialog = false">Cancel</el-button>
          <el-button type="primary" @click="confirmRollback">Rollback</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, reactive, defineProps } from 'vue';
import { projectAPI } from '@/api';
import { ElMessage, ElMessageBox, ElTable, ElTableColumn, ElButton, ElAlert, ElDialog, ElForm, ElFormItem, ElSwitch, ElSelect, ElOption, ElInput, ElInputNumber } from 'element-plus';
import { useRouter } from 'vue-router';

const props = defineProps({
  projectId: {
    type: Number,
    required: true
  }
});

const router = useRouter();

const dataVersions = ref([]);
const loading = ref(true);
const error = ref(null);

const showDataViewDialog = ref(false);
const currentDataPreview = ref(null);
const dataViewLoading = ref(false);
const dataViewError = ref(null);

const showCleanDataDialog = ref(false);
const cleaningForm = reactive({
  entityId: null,
  version: null,
  remove_outliers: true,
  outlier_method: "iqr",
  fill_missing: true,
  missing_method: "interpolate",
  smooth_data: false,
  smooth_window: 5,
  notes: ""
});

const showFeatureExtractionDialog = ref(false);
const featureExtractionForm = reactive({
  entityId: null,
  version: null,
  feature_config_json: '{}',
  notes: ""
});

const showRollbackDialog = ref(false);
const rollbackTarget = reactive({
  entityId: null,
  version: null
});
const rollbackForm = reactive({
  notes: ""
});

const fetchDataVersions = async (projectId) => {
  loading.value = true;
  error.value = null;
  const currentProjectId = Number(projectId); // Explicitly convert to Number
  console.log('ProjectDataTab - Fetching data versions for projectId:', currentProjectId);

  if (isNaN(currentProjectId) || currentProjectId <= 0) {
    error.value = '无效的项目ID，无法加载数据版本。';
    dataVersions.value = [];
    loading.value = false;
    return;
  }

  try {
    const response = await projectAPI.getProjectVersions(currentProjectId);
    // Filter for 'data' entity_type
    dataVersions.value = response.filter(v => v.entity_type === 'data');
  } catch (err) {
    console.error('Failed to fetch data versions:', err);
    error.value = 'Failed to load data versions. ' + (err.response?.data?.detail || err.message);
  } finally {
    loading.value = false;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

const goToDataUpload = () => {
  router.push({ name: 'ProjectDataUpload', params: { projectId: props.projectId } });
};

const viewData = async (entityId, version) => {
  showDataViewDialog.value = true;
  dataViewLoading.value = true;
  dataViewError.value = null;
  currentDataPreview.value = null;
  const currentProjectId = Number(props.projectId); // Explicitly convert to Number
  if (isNaN(currentProjectId) || currentProjectId <= 0) {
    dataViewError.value = '无效的项目ID，无法查看数据。';
    dataViewLoading.value = false;
    return;
  }
  try {
    const response = await projectAPI.viewProjectDataVersion(currentProjectId, entityId, version);
    currentDataPreview.value = response;
  } catch (err) {
    console.error('Failed to view data:', err);
    dataViewError.value = 'Failed to load data preview: ' + (err.response?.data?.detail || err.message);
  } finally {
    dataViewLoading.value = false;
  }
};

const formatSummaryStats = (summary) => {
  if (!summary) return [];
  const formatted = [];
  const statsKeys = Object.keys(summary).length > 0 ? Object.keys(Object.values(summary)[0]) : [];

  statsKeys.forEach(statKey => {
    const row = { stat: statKey };
    for (const col in summary) {
      row[col] = summary[col][statKey] !== undefined ? summary[col][statKey].toFixed(2) : 'N/A';
    }
    formatted.push(row);
  });
  return formatted;
};

const cleanData = (entityId, version) => {
  cleaningForm.entityId = entityId;
  cleaningForm.version = version;
  cleaningForm.notes = `Cleaned data from entity ${entityId} version ${version}`;
  showCleanDataDialog.value = true;
};

const submitCleanData = async () => {
  try {
    const cleaningConfig = {
      remove_outliers: cleaningForm.remove_outliers,
      outlier_method: cleaningForm.outlier_method,
      fill_missing: cleaningForm.fill_missing,
      missing_method: cleaningForm.missing_method,
      smooth_data: cleaningForm.smooth_data,
      smooth_window: cleaningForm.smooth_window,
    };
    
    const currentProjectId = Number(props.projectId); // Explicitly convert to Number
    if (isNaN(currentProjectId) || currentProjectId <= 0) {
      ElMessage.error('无效的项目ID，无法清洗数据。');
      return;
    }

    await projectAPI.cleanProjectDataVersion(
      currentProjectId,
      cleaningForm.entityId,
      cleaningForm.version,
      {
        cleaning_config: cleaningConfig,
        notes: cleaningForm.notes
      }
    );
    ElMessage.success('数据清洗 initiated successfully!');
    showCleanDataDialog.value = false;
    fetchDataVersions(currentProjectId); // Refresh list
  } catch (err) {
    console.error('Failed to clean data:', err);
    ElMessage.error('Failed to clean data: ' + (err.response?.data?.detail || err.message));
  }
};

const extractFeatures = (entityId, version) => {
  featureExtractionForm.entityId = entityId;
  featureExtractionForm.version = version;
  featureExtractionForm.notes = `Features extracted from entity ${entityId} version ${version}`;
  featureExtractionForm.feature_config_json = JSON.stringify({
    "time_features": ["mean", "std", "min", "max"],
    "frequency_features": ["fft_mean", "fft_std"]
  }, null, 2); // Pre-fill with example
  showFeatureExtractionDialog.value = true;
};

const submitFeatureExtraction = async () => {
  try {
    let featureConfig = {};
    try {
      featureConfig = JSON.parse(featureExtractionForm.feature_config_json);
    } catch (e) {
      ElMessage.error('Invalid JSON for feature config.');
      return;
    }

    const currentProjectId = Number(props.projectId); // Explicitly convert to Number
    if (isNaN(currentProjectId) || currentProjectId <= 0) {
      ElMessage.error('无效的项目ID，无法提取特征。');
      return;
    }

    await projectAPI.extractProjectFeatures(
      currentProjectId,
      {
        source_data_entity_id: featureExtractionForm.entityId,
        source_data_version: featureExtractionForm.version,
        feature_config: featureConfig,
        notes: featureExtractionForm.notes
      }
    );
    ElMessage.success('Feature extraction initiated successfully!');
    showFeatureExtractionDialog.value = false;
    fetchDataVersions(currentProjectId); // Refresh list (features are also versioned)
  } catch (err) {
    console.error('Failed to extract features:', err);
    ElMessage.error('Failed to extract features: ' + (err.response?.data?.detail || err.message));
  }
};

const rollbackData = (entityId, version) => {
  rollbackTarget.entityId = entityId;
  rollbackTarget.version = version;
  rollbackForm.notes = `Rollback to data entity ${entityId} version ${version}`;
  showRollbackDialog.value = true;
};

const confirmRollback = async () => {
  try {
    const currentProjectId = Number(props.projectId); // Explicitly convert to Number
    if (isNaN(currentProjectId) || currentProjectId <= 0) {
      ElMessage.error('无效的项目ID，无法回滚数据。');
      return;
    }

    await projectAPI.rollbackProjectDataVersion(
      currentProjectId,
      rollbackTarget.entityId,
      rollbackTarget.version,
      { notes: rollbackForm.notes }
    );
    ElMessage.success('Data rollback successful!');
    showRollbackDialog.value = false;
    fetchDataVersions(currentProjectId); // Refresh list
  } catch (err) {
    console.error('Failed to rollback data:', err);
    ElMessage.error('Failed to rollback data: ' + (err.response?.data?.detail || err.message));
  }
};

watch(() => props.projectId, (newProjectId) => {
  if (newProjectId) {
    fetchDataVersions(newProjectId);
  }
}, { immediate: true });
</script>

<style scoped>
.project-data-tab {
  padding: 20px;
}
.error-message {
  margin-top: 20px;
}
</style>
