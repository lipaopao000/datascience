<template>
  <div class="project-detail-container">
    <el-card v-if="project" v-loading="loading">
      <template #header>
        <div class="card-header">
          <h2>Project: {{ project.name }}</h2>
          <el-button type="primary" @click="goBack">Back to Projects</el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab" class="project-tabs" @tab-click="handleTabClick">
        <el-tab-pane label="Overview" name="overview">
          <div class="project-overview">
            <p><strong>Description:</strong> {{ project.description || 'N/A' }}</p>
            <p><strong>Owner ID:</strong> {{ project.owner_id }}</p>
            <p><strong>Created At:</strong> {{ formatDate(project.created_at) }}</p>
            <p><strong>Last Updated:</strong> {{ formatDate(project.updated_at) }}</p>
            <!-- Add more statistical information here if available -->
            <h3>Project Statistics</h3>
            <ProjectStatisticsAnalysis :projectId="Number(project.id)" />
          </div>
        </el-tab-pane>
        <el-tab-pane label="Data" name="data"></el-tab-pane>
        <el-tab-pane label="Experiments" name="experiments"></el-tab-pane>
        <el-tab-pane label="Models" name="models"></el-tab-pane>
      </el-tabs>
    </el-card>

    <div v-else-if="!loading && error" class="error-message">
      <el-alert type="error" :title="error" show-icon :closable="false"></el-alert>
    </div>
    <div v-else-if="!loading" class="no-project-found">
      <el-empty description="Project not found"></el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { projectAPI, experimentAPI, modelRegistryAPI } from '@/api';
import { ElMessage, ElCard, ElButton, ElTabs, ElTabPane, ElAlert, ElEmpty } from 'element-plus';
import ProjectStatisticsAnalysis from '@/views/analysis/StatisticsAnalysis.vue';
// Removed ProjectDataTab, ProjectExperimentsTab, ProjectModelsTab as they are no longer directly rendered

const route = useRoute();
const router = useRouter();

const project = ref(null);
const loading = ref(true);
const error = ref(null);
const activeTab = ref('overview'); // Default active tab to overview

const projectId = ref(null); // This will hold the parsed projectId from route params

const fetchProjectDetails = async (id) => {
  loading.value = true;
  error.value = null;
  try {
    project.value = await projectAPI.getProject(id);
    console.log('ProjectDetail - Fetched Project:', project.value); // Log fetched project
  } catch (err) {
    console.error('Failed to fetch project details:', err);
    error.value = 'Failed to load project details. ' + (err.response?.data?.detail || err.message);
    project.value = null;
  } finally {
    loading.value = false;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

const goBack = () => {
  router.push({ name: 'ProjectList' });
};

const handleTabClick = (tab) => {
  const currentProjectId = projectId.value;
  if (!currentProjectId) {
    ElMessage.error('Project ID is not available.');
    return;
  }

  switch (tab.paneName) {
    case 'data':
      router.push({ name: 'ProjectDataList', params: { projectId: currentProjectId } });
      break;
    case 'experiments':
      router.push({ name: 'ProjectExperimentList', params: { projectId: currentProjectId } }); // New route name
      break;
    case 'models':
      router.push({ name: 'ProjectModelManagement', params: { projectId: currentProjectId } });
      break;
    case 'overview':
      // Stay on the current page, or navigate to the ProjectDetail route itself
      router.push({ name: 'ProjectDetail', params: { projectId: currentProjectId } });
      break;
    default:
      break;
  }
};

// Watch for changes in route.params.projectId
watch(() => route.params.projectId, (newProjectId) => {
  if (newProjectId) {
    projectId.value = Number(newProjectId); // Ensure it's a Number
    console.log('ProjectDetail - Route Project ID:', projectId.value); // Log route projectId
    fetchProjectDetails(projectId.value);
    // Set active tab based on current route name if it's one of the project detail sub-routes
    if (route.name === 'ProjectDataList') {
      activeTab.value = 'data';
    } else if (route.name === 'ProjectExperimentList') { // New route name
      activeTab.value = 'experiments';
    } else if (route.name === 'ProjectModelManagement') {
      activeTab.value = 'models';
    } else {
      activeTab.value = 'overview';
    }
  }
}, { immediate: true }); // Immediate: true to run on initial component mount
</script>

<style scoped>
.project-detail-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-overview {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}

.project-overview p {
  margin: 5px 0;
  font-size: 14px;
  color: #606266;
}

.project-tabs {
  margin-top: 20px;
}

.error-message, .no-project-found {
  margin-top: 20px;
  text-align: center;
}
</style>
