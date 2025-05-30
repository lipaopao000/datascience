<template>
  <div class="model-versions-container">
    <el-card v-if="registeredModel" v-loading="loading">
      <template #header>
        <div class="card-header">
          <h2>Model: {{ registeredModel.name }} Versions</h2>
          <el-button type="primary" @click="goBackToProjectDetail">Back to Project</el-button>
        </div>
      </template>

      <div class="model-overview">
        <p><strong>Description:</strong> {{ registeredModel.description || 'N/A' }}</p>
        <p><strong>Project ID:</strong> {{ registeredModel.project_id }}</p>
        <p><strong>Created At:</strong> {{ formatDate(registeredModel.created_at) }}</p>
      </div>

      <h3>Versions</h3>
      <el-button type="primary" @click="trainNewModel" style="margin-bottom: 15px;">Train New Model Version</el-button>
      <el-table :data="modelVersions" v-loading="loadingVersions" style="width: 100%">
        <el-table-column prop="id" label="Version ID" width="100"></el-table-column>
        <el-table-column prop="version" label="Version" width="80"></el-table-column>
        <el-table-column prop="model_framework" label="Framework" width="120"></el-table-column>
        <el-table-column prop="stage" label="Stage" width="100"></el-table-column>
        <el-table-column prop="model_path" label="Model Path"></el-table-column>
        <el-table-column label="Created At" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="250">
          <template #default="scope">
            <el-button size="small" @click="viewModelVersionDetails(scope.row.id)">View Details</el-button>
            <el-button size="small" @click="showPredictDialog(scope.row)">Predict</el-button>
            <el-button size="small" type="warning" @click="showStageTransitionDialog(scope.row)">Stage</el-button>
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
    <div v-else-if="!loading" class="no-model-found">
      <el-empty description="Registered Model not found"></el-empty>
    </div>

    <!-- Model Version Details Dialog -->
    <el-dialog v-model="showModelVersionDetailsDialog" title="Model Version Details" width="70%">
      <div v-if="currentModelVersionDetails">
        <h4>Version: {{ currentModelVersionDetails.version }} (ID: {{ currentModelVersionDetails.id }})</h4>
        <p>Framework: {{ currentModelVersionDetails.model_framework }}</p>
        <p>Stage: {{ currentModelVersionDetails.stage }}</p>
        <p>Model Path: {{ currentModelVersionDetails.model_path }}</p>
        <p>Run ID: {{ currentModelVersionDetails.run_id || 'N/A' }}</p>
        <p>Created At: {{ formatDate(currentModelVersionDetails.created_at) }}</p>
        
        <h4 style="margin-top: 20px;">Model Signature</h4>
        <pre>{{ JSON.stringify(currentModelVersionDetails.model_signature, null, 2) }}</pre>

        <h4 style="margin-top: 20px;">Model Metadata</h4>
        <pre>{{ JSON.stringify(currentModelVersionDetails.model_metadata, null, 2) }}</pre>
      </div>
      <div v-else-if="modelVersionDetailsLoading">Loading model version details...</div>
      <div v-else-if="modelVersionDetailsError" class="error-message">
        <el-alert type="error" :title="modelVersionDetailsError" show-icon :closable="false"></el-alert>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showModelVersionDetailsDialog = false">Close</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Predict Dialog -->
    <el-dialog v-model="showPredictDialogFlag" title="Make Prediction" width="600px">
      <el-form :model="predictForm" label-width="120px">
        <el-form-item label="Model Entity ID">
          <el-input v-model="predictForm.model_entity_id" disabled></el-input>
        </el-form-item>
        <el-form-item label="Model Version">
          <el-input-number v-model="predictForm.model_version" disabled></el-input-number>
        </el-form-item>
        <el-form-item label="Input Features (JSON)">
          <el-input type="textarea" v-model="predictForm.input_features_json" :rows="8"></el-input>
          <small>Example: {"feature1": 10.5, "feature2": "value"}</small>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showPredictDialogFlag = false">Cancel</el-button>
          <el-button type="primary" @click="submitPrediction">Predict</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Prediction Result Dialog -->
    <el-dialog v-model="showPredictionResultDialog" title="Prediction Result" width="500px">
      <div v-if="predictionResult">
        <h4>Predictions:</h4>
        <pre>{{ JSON.stringify(predictionResult, null, 2) }}</pre>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showPredictionResultDialog = false">Close</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Stage Transition Dialog -->
    <el-dialog v-model="showStageTransitionDialogFlag" title="Transition Model Stage" width="400px">
      <el-form :model="stageTransitionForm" label-width="120px">
        <el-form-item label="Current Stage">
          <el-input v-model="stageTransitionForm.current_stage" disabled></el-input>
        </el-form-item>
        <el-form-item label="New Stage">
          <el-select v-model="stageTransitionForm.new_stage" placeholder="Select new stage">
            <el-option label="None" value="None"></el-option>
            <el-option label="Staging" value="Staging"></el-option>
            <el-option label="Production" value="Production"></el-option>
            <el-option label="Archived" value="Archived"></el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showStageTransitionDialogFlag = false">Cancel</el-button>
          <el-button type="primary" @click="submitStageTransition">Confirm</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Train New Model Dialog -->
    <el-dialog v-model="showTrainNewModelDialog" title="Train New Model Version" width="700px">
      <el-form :model="trainModelForm" label-width="180px">
        <el-form-item label="Source Features Entity ID">
          <el-input v-model="trainModelForm.source_features_entity_id"></el-input>
        </el-form-item>
        <el-form-item label="Source Features Version">
          <el-input-number v-model="trainModelForm.source_features_version" :min="1"></el-input-number>
        </el-form-item>
        <el-form-item label="Model Type">
          <el-select v-model="trainModelForm.model_type" placeholder="Select model type">
            <el-option label="Logistic Regression" value="logistic_regression"></el-option>
            <el-option label="Random Forest Classifier" value="random_forest_classifier"></el-option>
            <el-option label="XGBoost Classifier" value="xgboost_classifier"></el-option>
            <!-- Add more model types as supported by backend -->
          </el-select>
        </el-form-item>
        <el-form-item label="Target Column">
          <el-input v-model="trainModelForm.target_column"></el-input>
        </el-form-item>
        <el-form-item label="Hyperparameters (JSON)">
          <el-input type="textarea" v-model="trainModelForm.hyperparameters_json" :rows="5"></el-input>
          <small>Example: {"n_estimators": 100, "max_depth": 10}</small>
        </el-form-item>
        <el-form-item label="Grid Search CV Config (JSON)">
          <el-input type="textarea" v-model="trainModelForm.grid_search_cv_json" :rows="5"></el-input>
          <small>Example: {"param_grid": {"n_estimators": [50, 100], "max_depth": [5, 10]}, "cv": 3, "scoring": "accuracy"}</small>
        </el-form-item>
        <el-form-item label="Notes">
          <el-input type="textarea" v-model="trainModelForm.notes"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showTrainNewModelDialog = false">Cancel</el-button>
          <el-button type="primary" @click="submitTrainNewModel">Train Model</el-button>
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
  modelId: { // This is the registered_model_id
    type: Number,
    required: true
  }
});

const router = useRouter();

const registeredModel = ref(null);
const modelVersions = ref([]);
const loading = ref(true);
const loadingVersions = ref(false);
const error = ref(null);

const showModelVersionDetailsDialog = ref(false);
const currentModelVersionDetails = ref(null);
const modelVersionDetailsLoading = ref(false);
const modelVersionDetailsError = ref(null);

const showPredictDialogFlag = ref(false);
const predictForm = reactive({
  model_entity_id: '',
  model_version: null,
  input_features_json: '{}'
});
const predictionResult = ref(null);
const showPredictionResultDialog = ref(false);

const showStageTransitionDialogFlag = ref(false);
const stageTransitionForm = reactive({
  version_id: null,
  current_stage: '',
  new_stage: 'None'
});

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

const fetchRegisteredModelDetails = async (id) => {
  loading.value = true;
  error.value = null;
  try {
    registeredModel.value = await modelRegistryAPI.getRegisteredModel(id);
    if (registeredModel.value) {
      await fetchModelVersions(id);
    }
  } catch (err) {
    console.error('Failed to fetch registered model details:', err);
    error.value = 'Failed to load registered model details. ' + (err.response?.data?.detail || err.message);
    registeredModel.value = null;
  } finally {
    loading.value = false;
  }
};

const fetchModelVersions = async (registeredModelId) => {
  loadingVersions.value = true;
  try {
    modelVersions.value = await modelRegistryAPI.getModelVersionsByRegisteredModel(registeredModelId);
  } catch (err) {
    console.error('Failed to fetch model versions:', err);
    ElMessage.error('Failed to load model versions: ' + (err.response?.data?.detail || err.message));
  } finally {
    loadingVersions.value = false;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

const goBackToProjectDetail = () => {
  if (registeredModel.value && registeredModel.value.project_id) {
    router.push({ name: 'ProjectDetail', params: { projectId: registeredModel.value.project_id } });
  } else {
    router.push({ name: 'ProjectList' }); // Fallback if project_id is not available
  }
};

const viewModelVersionDetails = async (versionId) => {
  showModelVersionDetailsDialog.value = true;
  modelVersionDetailsLoading.value = true;
  modelVersionDetailsError.value = null;
  currentModelVersionDetails.value = null;
  try {
    currentModelVersionDetails.value = await modelRegistryAPI.getModelVersion(versionId);
  } catch (err) {
    console.error('Failed to fetch model version details:', err);
    modelVersionDetailsError.value = 'Failed to load model version details: ' + (err.response?.data?.detail || err.message);
  } finally {
    modelVersionDetailsLoading.value = false;
  }
};

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

    // Use projectAPI for prediction as it's a project-scoped operation
    const response = await projectAPI.predictWithProjectModel(registeredModel.value.project_id, requestBody);
    predictionResult.value = response.predictions;
    showPredictionResultDialog.value = true;
    showPredictDialogFlag.value = false;
  } catch (err) {
    console.error('Failed to make prediction:', err);
    ElMessage.error('Failed to make prediction: ' + (err.response?.data?.detail || err.message));
  }
};

const showStageTransitionDialog = (version) => {
  stageTransitionForm.version_id = version.id;
  stageTransitionForm.current_stage = version.stage;
  stageTransitionForm.new_stage = version.stage; // Default to current stage
  showStageTransitionDialogFlag.value = true;
};

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

    // Use projectAPI for training as it's a project-scoped operation
    await projectAPI.trainProjectModel(registeredModel.value.project_id, requestBody);
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
.model-versions-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.model-overview {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}

.model-overview p {
  margin: 5px 0;
  font-size: 14px;
  color: #606266;
}

.error-message, .no-model-found {
  margin-top: 20px;
  text-align: center;
}

pre {
  background-color: #eee;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}
</style>
