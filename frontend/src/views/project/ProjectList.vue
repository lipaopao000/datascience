<template>
  <div class="project-list-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Projects</span>
          <el-button type="primary" @click="showCreateProjectForm = true">Create Project</el-button>
        </div>
      </template>

      <el-table :data="projects" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80"></el-table-column>
        <el-table-column label="Name" width="200">
          <template #default="scope">
            <span @click="goToProjectDetails(scope.row.id)" style="cursor: pointer; color: #409EFF;">{{ scope.row.name }}</span>
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
        <el-table-column label="Actions" width="300">
          <template #default="scope">
            <el-button size="small" @click="handleEditProject(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDeleteProject(scope.row.id)">删除</el-button>
            <el-button size="small" type="info" @click="goToProjectDetails(scope.row.id)" style="margin-left: 5px;">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="error" class="error-message">
        <el-alert type="error" :title="error" show-icon :closable="false"></el-alert>
      </div>
    </el-card>

    <!-- Project Creation Form -->
    <el-dialog v-model="showCreateProjectForm" title="Create New Project" width="500px">
      <el-form :model="newProjectForm" :rules="newProjectRules" ref="newProjectFormRef" label-width="120px">
        <el-form-item label="Project Name" prop="name">
          <el-input v-model="newProjectForm.name"></el-input>
        </el-form-item>
        <el-form-item label="Description">
          <el-input type="textarea" v-model="newProjectForm.description"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateProjectForm = false">Cancel</el-button>
          <el-button type="primary" @click="handleCreateProject">Create</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Project Edit Form -->
    <el-dialog v-model="showEditProjectForm" title="Edit Project" width="500px">
      <el-form :model="editProjectForm" :rules="newProjectRules" ref="editProjectFormRef" label-width="120px">
        <el-form-item label="Project Name" prop="name">
          <el-input v-model="editProjectForm.name"></el-input>
        </el-form-item>
        <el-form-item label="Description">
          <el-input type="textarea" v-model="editProjectForm.description"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditProjectForm = false">Cancel</el-button>
          <el-button type="primary" @click="handleUpdateProject">Save</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import { useRouter } from 'vue-router'; // Import useRouter
import { projectAPI } from '@/api';
import { ElMessage, ElMessageBox, ElForm, ElFormItem, ElInput, ElButton, ElCard, ElTable, ElTableColumn, ElAlert, ElDialog } from 'element-plus';

const projects = ref([]);
const loading = ref(true);
const error = ref(null);

const showCreateProjectForm = ref(false);
const newProjectFormRef = ref(null);
const newProjectForm = reactive({
  name: '',
  description: ''
});

const showEditProjectForm = ref(false);
const editProjectFormRef = ref(null);
const editProjectForm = reactive({
  id: null,
  name: '',
  description: ''
});

const newProjectRules = {
  name: [{ required: true, message: 'Please enter project name', trigger: 'blur' }],
};

const handleCreateProject = async () => {
  if (!newProjectFormRef.value) return;
  newProjectFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await projectAPI.createProject(newProjectForm);
        ElMessage.success('Project created successfully!');
        showCreateProjectForm.value = false;
        newProjectForm.name = '';
        newProjectForm.description = '';
        fetchProjects();
      } catch (err) {
        console.error('Failed to create project:', err);
        ElMessage.error('Failed to create project: ' + (err.response?.data?.detail || err.message));
      }
    } else {
      ElMessage.error('Please fill in all required fields.');
      return false;
    }
  });
};

const handleEditProject = (project) => {
  editProjectForm.id = project.id;
  editProjectForm.name = project.name;
  editProjectForm.description = project.description;
  showEditProjectForm.value = true;
};

const handleUpdateProject = async () => {
  if (!editProjectFormRef.value) return;
  editProjectFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await projectAPI.updateProject(editProjectForm.id, {
          name: editProjectForm.name,
          description: editProjectForm.description
        });
        ElMessage.success('Project updated successfully!');
        showEditProjectForm.value = false;
        fetchProjects();
      } catch (err) {
        console.error('Failed to update project:', err);
        ElMessage.error('Failed to update project: ' + (err.response?.data?.detail || err.message));
      }
    } else {
      ElMessage.error('Please fill in all required fields.');
      return false;
    }
  });
};

const handleDeleteProject = async (projectId) => {
  ElMessageBox.confirm(
    'This will permanently delete the project. Continue?',
    'Warning',
    {
      confirmButtonText: 'OK',
      cancelButtonText: 'Cancel',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        await projectAPI.deleteProject(projectId);
        ElMessage.success('Project deleted successfully!');
        fetchProjects();
      } catch (err) {
        console.error('Failed to delete project:', err);
        ElMessage.error('Failed to delete project: ' + (err.response?.data?.detail || err.message));
      }
    })
    .catch(() => {
      ElMessage.info('Delete cancelled');
    });
};

const fetchProjects = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await projectAPI.getProjects();
    projects.value = response;
  } catch (err) {
    console.error('Failed to fetch projects:', err);
    error.value = 'Failed to load projects. Please try again later.';
  } finally {
    loading.value = false;
  }
};

const router = useRouter(); // Initialize router

const setActiveProject = (projectId) => {
  localStorage.setItem('activeProjectId', projectId);
};

const goToProjectDetails = (projectId) => {
  setActiveProject(projectId);
  router.push({ name: 'ProjectDetail', params: { projectId: projectId } });
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

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

/* Removed overlay/card styles for dialogs as Element Plus handles them */

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}
</style>
