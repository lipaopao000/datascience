<template>
  <div class="project-experiments-tab">
    <h3>Experiments</h3>
    <el-button type="primary" @click="createExperiment" style="margin-bottom: 15px;">Create New Experiment</el-button>

    <el-table :data="experiments" v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80"></el-table-column>
      <el-table-column prop="name" label="Name" width="200"></el-table-column>
      <el-table-column prop="description" label="Description"></el-table-column>
      <el-table-column label="Created At" width="180">
        <template #default="scope">
          {{ formatDate(scope.row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="Updated At" width="180">
        <template #default="scope">
          {{ formatDate(scope.row.updated_at) }}
        </template>
      </el-table-column>
      <el-table-column label="Actions" width="150">
        <template #default="scope">
          <el-button size="small" @click="viewExperimentRuns(scope.row.id)">View Runs</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="error" class="error-message">
      <el-alert type="error" :title="error" show-icon :closable="false"></el-alert>
    </div>

    <!-- Create Experiment Dialog -->
    <el-dialog v-model="showCreateExperimentDialog" title="Create New Experiment" width="500px">
      <el-form :model="newExperimentForm" :rules="newExperimentRules" ref="newExperimentFormRef" label-width="120px">
        <el-form-item label="Experiment Name" prop="name">
          <el-input v-model="newExperimentForm.name"></el-input>
        </el-form-item>
        <el-form-item label="Description">
          <el-input type="textarea" v-model="newExperimentForm.description"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateExperimentDialog = false">Cancel</el-button>
          <el-button type="primary" @click="submitCreateExperiment">Create</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, reactive, defineProps } from 'vue';
import { experimentAPI } from '@/api';
import { ElMessage, ElTable, ElTableColumn, ElButton, ElAlert, ElDialog, ElForm, ElFormItem, ElInput } from 'element-plus';
import { useRouter } from 'vue-router';

const props = defineProps({
  projectId: {
    type: Number,
    required: true
  }
});

const router = useRouter();

const experiments = ref([]);
const loading = ref(true);
const error = ref(null);

const showCreateExperimentDialog = ref(false);
const newExperimentFormRef = ref(null);
const newExperimentForm = reactive({
  name: '',
  description: '',
  project_id: null
});

const newExperimentRules = {
  name: [{ required: true, message: 'Please enter experiment name', trigger: 'blur' }],
};

const fetchExperiments = async (projectId) => {
  loading.value = true;
  error.value = null;
  const currentProjectId = Number(projectId); // Explicitly convert to Number
  console.log('ProjectExperimentsTab - Fetching experiments for projectId:', currentProjectId);

  if (isNaN(currentProjectId) || currentProjectId <= 0) {
    error.value = '无效的项目ID，无法加载实验。';
    experiments.value = [];
    loading.value = false;
    return;
  }

  try {
    const response = await experimentAPI.getExperiments(0, 100, currentProjectId);
    experiments.value = response;
  } catch (err) {
    console.error('Failed to fetch experiments:', err);
    error.value = 'Failed to load experiments. ' + (err.response?.data?.detail || err.message);
  } finally {
    loading.value = false;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

const createExperiment = () => {
  newExperimentForm.name = '';
  newExperimentForm.description = '';
  newExperimentForm.project_id = Number(props.projectId); // Explicitly convert to Number
  showCreateExperimentDialog.value = true;
};

const submitCreateExperiment = async () => {
  if (!newExperimentFormRef.value) return;
  newExperimentFormRef.value.validate(async (valid) => {
        if (valid) {
          const currentProjectId = Number(props.projectId); // Explicitly convert to Number
          if (isNaN(currentProjectId) || currentProjectId <= 0) {
            ElMessage.error('无效的项目ID，无法创建实验。');
            return;
          }
          newExperimentForm.project_id = currentProjectId; // Ensure project_id is number in payload
          try {
            await experimentAPI.createExperiment(newExperimentForm);
            ElMessage.success('Experiment created successfully!');
            showCreateExperimentDialog.value = false;
            fetchExperiments(currentProjectId); // Refresh list
          } catch (err) {
            console.error('Failed to create experiment:', err);
            ElMessage.error('Failed to create experiment: ' + (err.response?.data?.detail || err.message));
          }
        } else {
          ElMessage.error('Please fill in all required fields.');
          return false;
        }
  });
};

const viewExperimentRuns = (experimentId) => {
  // Navigate to a dedicated page for viewing runs of this experiment
  // This route needs to be defined in router/index.js
  router.push({ name: 'ExperimentRuns', params: { experimentId: experimentId } });
};

watch(() => props.projectId, (newProjectId) => {
  if (newProjectId) {
    fetchExperiments(newProjectId);
  }
}, { immediate: true });
</script>

<style scoped>
.project-experiments-tab {
  padding: 20px;
}
.error-message {
  margin-top: 20px;
}
</style>
