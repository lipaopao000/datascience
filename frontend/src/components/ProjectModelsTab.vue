<template>
  <div class="project-models-tab">
    <h3>Registered Models</h3>
    <el-button type="primary" @click="registerModel" style="margin-bottom: 15px;">Register New Model</el-button>

    <el-table :data="registeredModels" v-loading="loading" style="width: 100%">
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
          <el-button size="small" @click="viewModelVersions(scope.row.id)">View Versions</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="error" class="error-message">
      <el-alert type="error" :title="error" show-icon :closable="false"></el-alert>
    </div>

    <!-- Register Model Dialog -->
    <el-dialog v-model="showRegisterModelDialog" title="Register New Model" width="500px">
      <el-form :model="newModelForm" :rules="newModelRules" ref="newModelFormRef" label-width="120px">
        <el-form-item label="Model Name" prop="name">
          <el-input v-model="newModelForm.name"></el-input>
        </el-form-item>
        <el-form-item label="Description">
          <el-input type="textarea" v-model="newModelForm.description"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showRegisterModelDialog = false">Cancel</el-button>
          <el-button type="primary" @click="submitRegisterModel">Register</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, reactive, defineProps } from 'vue';
import { modelRegistryAPI, projectAPI } from '@/api'; // Import projectAPI for train endpoint
import { ElMessage, ElTable, ElTableColumn, ElButton, ElAlert, ElEmpty, ElDialog, ElForm, ElFormItem, ElInput, ElInputNumber, ElSelect, ElOption } from 'element-plus';
import { useRouter } from 'vue-router';

const props = defineProps({
  projectId: { // This is the registered_model_id
    type: Number,
    required: true
  }
});

const router = useRouter();

const registeredModels = ref([]);
const loading = ref(true);
const error = ref(null);

const showRegisterModelDialog = ref(false);
const newModelFormRef = ref(null);
const newModelForm = reactive({
  name: '',
  description: '',
  project_id: null
});

const newModelRules = {
  name: [{ required: true, message: 'Please enter model name', trigger: 'blur' }],
};

const fetchRegisteredModels = async (projectId) => {
  loading.value = true;
  error.value = null;
  const currentProjectId = Number(projectId); // Explicitly convert to Number
  console.log('ProjectModelsTab - Fetching registered models for projectId:', currentProjectId);

  if (isNaN(currentProjectId) || currentProjectId <= 0) {
    error.value = '无效的项目ID，无法加载注册模型。';
    registeredModels.value = [];
    loading.value = false;
    return;
  }

  try {
    const response = await modelRegistryAPI.getRegisteredModels(0, 100, currentProjectId);
    registeredModels.value = response;
  } catch (err) {
    console.error('Failed to fetch registered models:', err);
    error.value = 'Failed to load registered models. ' + (err.response?.data?.detail || err.message);
  } finally {
    loading.value = false;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

const registerModel = () => {
  newModelForm.name = '';
  newModelForm.description = '';
  newModelForm.project_id = Number(props.projectId); // Explicitly convert to Number
  showRegisterModelDialog.value = true;
};

const submitRegisterModel = async () => {
  if (!newModelFormRef.value) return;
  newModelFormRef.value.validate(async (valid) => {
    if (valid) {
      const currentProjectId = Number(props.projectId); // Explicitly convert to Number
      if (isNaN(currentProjectId) || currentProjectId <= 0) {
        ElMessage.error('无效的项目ID，无法注册模型。');
        return;
      }
      newModelForm.project_id = currentProjectId; // Ensure project_id is number in payload
      try {
        await modelRegistryAPI.createRegisteredModel(newModelForm);
        ElMessage.success('Model registered successfully!');
        showRegisterModelDialog.value = false;
        fetchRegisteredModels(currentProjectId); // Refresh list
      } catch (err) {
        console.error('Failed to register model:', err);
        ElMessage.error('Failed to register model: ' + (err.response?.data?.detail || err.message));
      }
    } else {
      ElMessage.error('Please fill in all required fields.');
      return false;
    }
  });
};

const viewModelVersions = (modelId) => {
  // Navigate to a dedicated page for viewing versions of this registered model
  // This route needs to be defined in router/index.js
  router.push({ name: 'ModelVersions', params: { modelId: modelId } });
};

const showPredictDialogFlag = ref(false);
const predictForm = reactive({
  model_entity_id: '',
  model_version: null,
  input_features_json: '{}'
});
const predictionResult = ref(null);
const showPredictionResultDialog = ref(false);

const showPredictDialog = (version) => {
  predictForm.model_entity_id = registeredModel.value.name; // Use registered model name as entity_id
  predictForm.model_version = version.version;
  predictForm.input_features_json = JSON.stringify({}, null, 2); // Clear previous input
  showPredictDialogFlag.value = true;
};

const submitPrediction = async () => {
  try {
    let inputFeatures = {};
    try {
      inputFeatures = JSON.parse(predictForm.input_features_json);
    } catch (e) {
      ElMessage.error('Invalid JSON for input features.');
      return;
    }

    const requestBody = {
      model_entity_id: predictForm.model_entity_id,
      model_version: predictForm.model_version,
      input_features: inputFeatures
    };

    const currentProjectId = Number(registeredModel.value.project_id); // Explicitly convert to Number
    if (isNaN(currentProjectId) || currentProjectId <= 0) {
      ElMessage.error('无效的项目ID，无法进行预测。');
      return;
    }
    const response = await projectAPI.predictWithProjectModel(currentProjectId, requestBody);
    predictionResult.value = response.predictions;
    showPredictionResultDialog.value = true;
    showPredictDialogFlag.value = false;
  } catch (err) {
    console.error('Failed to make prediction:', err);
    ElMessage.error('Failed to make prediction: ' + (err.response?.data?.detail || err.message));
  }
};

const showStageTransitionDialogFlag = ref(false);
const stageTransitionForm = reactive({
  version_id: null,
  current_stage: '',
  new_stage: 'None'
});

const submitStageTransition = async () => {
  try {
    await modelRegistryAPI.transitionModelVersionStage(
      stageTransitionForm.version_id,
      stageTransitionForm.new_stage
    );
    ElMessage.success('Model stage updated successfully!');
    showStageTransitionDialogFlag.value = false;
    fetchModelVersions(props.modelId); // Refresh list
  } catch (err) {
    console.error('Failed to transition model stage:', err);
    ElMessage.error('Failed to transition model stage: ' + (err.response?.data?.detail || err.message));
  }
};

const showTrainNewModelDialog = ref(false);
const trainModelForm = reactive({
  source_features_entity_id: '',
  source_features_version: 1,
  model_type: '',
  target_column: '',
  hyperparameters_json: '{}',
  grid_search_cv_json: '{}',
  notes: ''
});

const trainNewModel = () => {
  trainModelForm.source_features_entity_id = '';
  trainModelForm.source_features_version = 1;
  trainModelForm.model_type = '';
  trainModelForm.target_column = '';
  trainModelForm.hyperparameters_json = '{}';
  trainModelForm.grid_search_cv_json = '{}';
  trainModelForm.notes = `Trained model for ${registeredModel.value.name}`;
  showTrainNewModelDialog.value = true;
};

const submitTrainNewModel = async () => {
  try {
    let hyperparameters = {};
    try {
      hyperparameters = JSON.parse(trainModelForm.hyperparameters_json);
    } catch (e) {
      ElMessage.error('Invalid JSON for hyperparameters.');
      return;
    }

    let gridSearchCVConfig = null;
    if (trainModelForm.grid_search_cv_json && trainModelForm.grid_search_cv_json !== '{}') {
      try {
        gridSearchCVConfig = JSON.parse(trainModelForm.grid_search_cv_json);
      } catch (e) {
        ElMessage.error('Invalid JSON for Grid Search CV config.');
        return;
      }
    }

    const requestBody = {
      source_features_entity_id: trainModelForm.source_features_entity_id,
      source_features_version: trainModelForm.source_features_version,
      model_type: trainModelForm.model_type,
      target_column: trainModelForm.target_column,
      model_params: {
        hyperparameters: hyperparameters,
        grid_search_cv: gridSearchCVConfig
      },
      notes: trainModelForm.notes
    };

    const currentProjectId = Number(registeredModel.value.project_id); // Explicitly convert to Number
    if (isNaN(currentProjectId) || currentProjectId <= 0) {
      ElMessage.error('无效的项目ID，无法进行模型训练。');
      return;
    }

    await projectAPI.trainProjectModel(currentProjectId, requestBody);
    ElMessage.success('Model training initiated successfully!');
    showTrainNewModelDialog.value = false;
    fetchModelVersions(props.modelId); // Refresh list
  } catch (err) {
    console.error('Failed to initiate model training:', err);
    ElMessage.error('Failed to initiate model training: ' + (err.response?.data?.detail || err.message));
  }
};

watch(() => props.modelId, (newModelId) => {
  if (newModelId) {
    fetchRegisteredModelDetails(newModelId);
  }
}, { immediate: true });
</script>

<style scoped>
.project-models-tab {
  padding: 20px;
}
.error-message {
  margin-top: 20px;
}

pre {
  background-color: #eee;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}
</style>
