<template>
  <div class="experiment-runs-container">
    <el-card v-if="experiment" v-loading="loading">
      <template #header>
        <div class="card-header">
          <h2>Experiment: {{ experiment.name }} Runs</h2>
          <el-button type="primary" @click="goBackToProjectDetail">Back to Project</el-button>
        </div>
      </template>

      <div class="experiment-overview">
        <p><strong>Description:</strong> {{ experiment.description || 'N/A' }}</p>
        <p><strong>Project ID:</strong> {{ experiment.project_id }}</p>
        <p><strong>Created At:</strong> {{ formatDate(experiment.created_at) }}</p>
      </div>

      <h3>Runs</h3>
      <el-table :data="runs" v-loading="loadingRuns" style="width: 100%">
        <el-table-column prop="id" label="Run ID" width="80"></el-table-column>
        <el-table-column prop="run_name" label="Run Name" width="180"></el-table-column>
        <el-table-column prop="status" label="Status" width="100"></el-table-column>
        <el-table-column prop="source_type" label="Source Type" width="120"></el-table-column>
        <el-table-column prop="source_name" label="Source Name" width="180"></el-table-column>
        <el-table-column label="Start Time" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column label="End Time" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="150">
          <template #default="scope">
            <el-button size="small" @click="viewRunDetails(scope.row.id)">View Details</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="error" class="error-message">
        <el-alert type="error" :title="error" show-icon :closable="false"></el-alert>
      </div>
    </el-card>

    <div v-else-if="!loading && error" class="error-message">
      <el-alert type="error" :title="error" show-icon :closable="false"></el-alert>
    </div>
    <div v-else-if="!loading" class="no-experiment-found">
      <el-empty description="Experiment not found"></el-empty>
    </div>

    <!-- Run Details Dialog -->
    <el-dialog v-model="showRunDetailsDialog" title="Run Details" width="70%">
      <div v-if="currentRunDetails">
        <h4>Run: {{ currentRunDetails.run_name || 'N/A' }} (ID: {{ currentRunDetails.id }})</h4>
        <p>Status: {{ currentRunDetails.status }}</p>
        <p>Source: {{ currentRunDetails.source_type }} - {{ currentRunDetails.source_name }}</p>
        <p>Start Time: {{ formatDate(currentRunDetails.start_time) }}</p>
        <p>End Time: {{ formatDate(currentRunDetails.end_time) }}</p>

        <el-tabs v-model="activeRunDetailTab">
          <el-tab-pane label="Parameters" name="parameters">
            <el-table :data="currentRunDetails.parameters" style="width: 100%" border>
              <el-table-column prop="key" label="Key" width="180"></el-table-column>
              <el-table-column prop="value" label="Value"></el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="Metrics" name="metrics">
            <el-table :data="currentRunDetails.metrics" style="width: 100%" border>
              <el-table-column prop="key" label="Key" width="180"></el-table-column>
              <el-table-column prop="value" label="Value"></el-table-column>
              <el-table-column prop="step" label="Step" width="80"></el-table-column>
              <el-table-column label="Timestamp" width="180">
                <template #default="scope">
                  {{ formatDate(scope.row.timestamp) }}
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="Artifacts" name="artifacts">
            <el-table :data="currentRunDetails.artifacts" style="width: 100%" border>
              <el-table-column prop="path" label="Path"></el-table-column>
              <el-table-column prop="file_type" label="Type" width="120"></el-table-column>
              <el-table-column prop="file_size" label="Size (bytes)" width="120"></el-table-column>
              <el-table-column label="Actions" width="100">
                <template #default="scope">
                  <el-button size="small" @click="downloadArtifact(currentRunDetails.id, scope.row.path)">Download</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
      <div v-else-if="runDetailsLoading">Loading run details...</div>
      <div v-else-if="runDetailsError" class="error-message">
        <el-alert type="error" :title="runDetailsError" show-icon :closable="false"></el-alert>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showRunDetailsDialog = false">Close</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { experimentAPI } from '@/api';
import { ElMessage, ElCard, ElButton, ElTable, ElTableColumn, ElAlert, ElEmpty, ElDialog, ElTabs, ElTabPane } from 'element-plus';

const route = useRoute();
const router = useRouter();

const experiment = ref(null);
const runs = ref([]);
const loading = ref(true);
const loadingRuns = ref(false);
const error = ref(null);

const showRunDetailsDialog = ref(false);
const currentRunDetails = ref(null);
const runDetailsLoading = ref(false);
const runDetailsError = ref(null);
const activeRunDetailTab = ref('parameters'); // Default tab for run details

const experimentId = ref(null);

const fetchExperimentDetails = async (id) => {
  loading.value = true;
  error.value = null;
  try {
    experiment.value = await experimentAPI.getExperiment(id);
    if (experiment.value) {
      await fetchRunsForExperiment(id);
    }
  } catch (err) {
    console.error('Failed to fetch experiment details:', err);
    error.value = 'Failed to load experiment details. ' + (err.response?.data?.detail || err.message);
    experiment.value = null;
  } finally {
    loading.value = false;
  }
};

const fetchRunsForExperiment = async (id) => {
  loadingRuns.value = true;
  try {
    runs.value = await experimentAPI.getRunsByExperiment(id);
  } catch (err) {
    console.error('Failed to fetch runs for experiment:', err);
    // Don't set global error, just for runs
    ElMessage.error('Failed to load runs: ' + (err.response?.data?.detail || err.message));
  } finally {
    loadingRuns.value = false;
  }
};

const viewRunDetails = async (runId) => {
  showRunDetailsDialog.value = true;
  runDetailsLoading.value = true;
  runDetailsError.value = null;
  currentRunDetails.value = null;
  try {
    const run = await experimentAPI.getRun(runId);
    const parameters = await experimentAPI.getRunParameters(runId);
    const metrics = await experimentAPI.getRunMetrics(runId);
    const artifacts = await experimentAPI.getRunArtifacts(runId);
    
    currentRunDetails.value = {
      ...run,
      parameters,
      metrics,
      artifacts
    };
  } catch (err) {
    console.error('Failed to fetch run details:', err);
    runDetailsError.value = 'Failed to load run details: ' + (err.response?.data?.detail || err.message);
  } finally {
    runDetailsLoading.value = false;
  }
};

const downloadArtifact = async (runId, artifactPath) => {
  try {
    const response = await experimentAPI.downloadArtifact(runId, artifactPath);
    const blob = new Blob([response], { type: 'application/octet-stream' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = artifactPath.split('/').pop(); // Get filename from path
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
    ElMessage.success('Artifact download started.');
  } catch (err) {
    console.error('Failed to download artifact:', err);
    ElMessage.error('Failed to download artifact: ' + (err.response?.data?.detail || err.message));
  }
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

const goBackToProjectDetail = () => {
  if (experiment.value && experiment.value.project_id) {
    router.push({ name: 'ProjectDetail', params: { projectId: experiment.value.project_id } });
  } else {
    router.push({ name: 'ProjectList' }); // Fallback if project_id is not available
  }
};

watch(() => route.params.experimentId, (newExperimentId) => {
  if (newExperimentId) {
    experimentId.value = parseInt(newExperimentId);
    fetchExperimentDetails(experimentId.value);
  }
}, { immediate: true });
</script>

<style scoped>
.experiment-runs-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.experiment-overview {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}

.experiment-overview p {
  margin: 5px 0;
  font-size: 14px;
  color: #606266;
}

.error-message, .no-experiment-found {
  margin-top: 20px;
  text-align: center;
}
</style>
