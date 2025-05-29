<template>
  <div class="project-list-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Projects</span>
          <!-- Optional: Add a button to create new projects -->
          <!-- <el-button type="primary" @click="goToCreateProject">Create Project</el-button> -->
        </div>
      </template>

      <el-table :data="projects" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80"></el-table-column>
        <el-table-column label="Name" width="200">
          <template #default="scope">
            <router-link :to="`/projects/${scope.row.id}/data`">{{ scope.row.name }}</router-link>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="Description"></el-table-column>
        <el-table-column prop="owner_id" label="Owner ID" width="120"></el-table-column>
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
        <el-table-column label="Actions" width="230">
          <template #default="scope">
            <router-link :to="{ name: 'ProjectDataUpload', params: { projectId: scope.row.id } }">
              <el-button size="small">Upload Data</el-button>
            </router-link>
            <router-link :to="{ name: 'ProjectDataList', params: { projectId: scope.row.id } }" style="margin-left: 5px;">
              <el-button size="small" type="primary">View Data</el-button>
            </router-link>
            <!-- Add other actions like delete or edit project if needed -->
          </template>
        </el-table-column>
      </el-table>

      <div v-if="error" class="error-message">
        <el-alert type="error" :title="error" show-icon :closable="false"></el-alert>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { projectAPI } from '@/api'; // Assuming your api/index.js is aliased as @/api
import { ElMessage } from 'element-plus';
// import { useRouter } from 'vue-router'; // If needed for navigation

// const router = useRouter(); // If navigation actions are added

const projects = ref([]);
const loading = ref(true);
const error = ref(null);

const fetchProjects = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await projectAPI.getProjects();
    projects.value = response; // Assuming the API returns an array of projects directly
  } catch (err) {
    console.error('Failed to fetch projects:', err);
    error.value = 'Failed to load projects. Please try again later.';
    // ElMessage is already handled by global interceptor for specific errors
  } finally {
    loading.value = false;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

/* Example action handlers (if buttons were enabled)
const viewProject = (projectId) => {
  router.push(`/projects/${projectId}`);
};

const deleteProject = async (projectId) => {
  try {
    await projectAPI.deleteProject(projectId);
    ElMessage.success('Project deleted successfully!');
    fetchProjects(); // Refresh the list
  } catch (err) {
    console.error('Failed to delete project:', err);
    // ElMessage for error is handled by interceptor
  }
};

const goToCreateProject = () => {
  router.push('/projects/create'); // Assuming a route for project creation
};
*/

onMounted(() => {
  fetchProjects();
});
</script>

<style scoped>
.project-list-container {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.error-message {
  margin-top: 20px;
}
</style>
