<template>
  <div class="project-list-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ $t('projectList.projects') }}</span>
          <el-button type="primary" @click="showCreateProjectForm = true">{{ $t('projectList.createProject') }}</el-button>
        </div>
      </template>

      <el-table :data="projects" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" :label="$t('projectList.id')" width="80"></el-table-column>
        <el-table-column :label="$t('projectList.name')" width="200">
          <template #default="scope">
            <span @click="goToProjectDetails(scope.row.id)" style="cursor: pointer; color: #409EFF;">{{ scope.row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" :label="$t('projectList.description')"></el-table-column>
        <el-table-column prop="owner_id" :label="$t('projectList.ownerId')" width="120"></el-table-column>
        <el-table-column :label="$t('projectList.createdAt')" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('projectList.updatedAt')" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('projectList.actions')" width="300">
          <template #default="scope">
            <el-button size="small" @click="handleEditProject(scope.row)">{{ $t('projectList.edit') }}</el-button>
            <el-button size="small" type="danger" @click="handleDeleteProject(scope.row.id)">{{ $t('projectList.delete') }}</el-button>
            <el-button size="small" type="info" @click="goToProjectDetails(scope.row.id)" style="margin-left: 5px;">
              {{ $t('projectList.viewDetails') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="error" class="error-message">
        <el-alert type="error" :title="error" show-icon :closable="false"></el-alert>
      </div>
    </el-card>

    <!-- Project Creation Form -->
    <el-dialog v-model="showCreateProjectForm" :title="$t('projectList.createNewProject')" width="500px">
      <el-form :model="newProjectForm" :rules="newProjectRules" ref="newProjectFormRef" label-width="120px">
        <el-form-item :label="$t('projectList.projectName')" prop="name">
          <el-input v-model="newProjectForm.name"></el-input>
        </el-form-item>
        <el-form-item :label="$t('projectList.description')">
          <el-input type="textarea" v-model="newProjectForm.description"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateProjectForm = false">{{ $t('projectList.cancel') }}</el-button>
          <el-button type="primary" @click="handleCreateProject">{{ $t('projectList.create') }}</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Project Edit Form -->
    <el-dialog v-model="showEditProjectForm" :title="$t('projectList.editProject')" width="500px">
      <el-form :model="editProjectForm" :rules="newProjectRules" ref="editProjectFormRef" label-width="120px">
        <el-form-item :label="$t('projectList.projectName')" prop="name">
          <el-input v-model="editProjectForm.name"></el-input>
        </el-form-item>
        <el-form-item :label="$t('projectList.description')">
          <el-input type="textarea" v-model="editProjectForm.description"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditProjectForm = false">{{ $t('projectList.cancel') }}</el-button>
          <el-button type="primary" @click="handleUpdateProject">{{ $t('projectList.save') }}</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { projectAPI } from '@/api';
import { ElMessage, ElMessageBox, ElForm, ElFormItem, ElInput, ElButton, ElCard, ElTable, ElTableColumn, ElAlert, ElDialog } from 'element-plus';
import { useI18n } from 'vue-i18n'; // Import useI18n

const { t } = useI18n(); // Initialize useI18n at the top

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
  name: [{ required: true, message: t('projectList.projectNameRequired'), trigger: 'blur' }],
};

const handleCreateProject = async () => {
  if (!newProjectFormRef.value) return;
  newProjectFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await projectAPI.createProject(newProjectForm);
        ElMessage.success(t('projectList.projectCreatedSuccess'));
        showCreateProjectForm.value = false;
        newProjectForm.name = '';
        newProjectForm.description = '';
        fetchProjects();
      } catch (err) {
        console.error('Failed to create project:', err);
        ElMessage.error(t('projectList.failedToCreateProject') + (err.response?.data?.detail || err.message));
      }
    } else {
      ElMessage.error(t('projectList.fillRequiredFields'));
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
        ElMessage.success(t('projectList.projectUpdatedSuccess'));
        showEditProjectForm.value = false;
        fetchProjects();
      } catch (err) {
        console.error('Failed to update project:', err);
        ElMessage.error(t('projectList.failedToUpdateProject') + (err.response?.data?.detail || err.message));
      }
    } else {
      ElMessage.error(t('projectList.fillRequiredFields'));
      return false;
    }
  });
};

const handleDeleteProject = async (projectId) => {
  ElMessageBox.confirm(
    t('projectList.deleteConfirm'),
    t('projectList.warning'),
    {
      confirmButtonText: t('projectList.ok'),
      cancelButtonText: t('projectList.cancel'),
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        await projectAPI.deleteProject(projectId);
        ElMessage.success(t('projectList.projectDeletedSuccess'));
        fetchProjects();
      } catch (err) {
        console.error('Failed to delete project:', err);
        ElMessage.error(t('projectList.failedToDeleteProject') + (err.response?.data?.detail || err.message));
      }
    })
    .catch(() => {
      ElMessage.info(t('projectList.deleteCancelled'));
    });
};

const fetchProjects = async () => {
  loading.value = true;
  error.value = null;
  try {
    // Check if user is authenticated
    const token = localStorage.getItem('authToken');
    if (!token) {
      router.push({ name: 'Login' });
      return;
    }

    const response = await projectAPI.getProjects();
    projects.value = response;
  } catch (err) {
    console.error('Failed to fetch projects:', err);
    if (err.response?.status === 401) {
      error.value = t('projectList.sessionExpired');
      // Clear token and redirect to login
      localStorage.removeItem('authToken');
      router.push({ name: 'Login' });
    } else {
      error.value = t('projectList.failedToLoadProjects');
    }
  } finally {
    loading.value = false;
  }
};

const router = useRouter();

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
