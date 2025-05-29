<template>
  <div class="data-list-container project-data-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ pageTitle }}</span>
          <el-button type="primary" @click="fetchProjectVersions" :loading="loading">
            <el-icon><Refresh /></el-icon>
            Refresh
          </el-button>
        </div>
      </template>

      <div v-if="projectId" class="project-context-info">
        <el-tag type="info">Project ID: {{ projectId }}</el-tag>
      </div>

      <!-- Data Versions Table -->
      <el-table :data="versions" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="Version ID" width="100" />
        <el-table-column prop="entity_id" label="Data Entity ID" width="200" />
        <el-table-column prop="version" label="Version #" width="100" />
        <el-table-column prop="entity_type" label="Entity Type" width="120">
            <template #default="{ row }">
                <el-tag :type="row.entity_type === 'dataset' ? 'success' : (row.entity_type === 'model' ? 'primary' : 'info')">
                    {{ row.entity_type }}
                </el-tag>
            </template>
        </el-table-column>
        <el-table-column prop="notes" label="Notes/Description" />
        <el-table-column label="Created At" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="Actions" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              size="small" 
              type="primary" 
              @click="viewDataVersion(row)"
              v-if="row.entity_type === 'dataset' || row.entity_type === 'cleaned_data' || row.entity_type === 'features'">
              View Data
            </el-button>
            <!-- Add other actions like rollback, clean, extract features for specific versions if needed -->
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-container" v-if="totalVersions > 0">
        <el-pagination
          :current-page="currentPage"
          @update:current-page="handleCurrentChange"
          :page-size="pageSize"
          @update:page-size="handleSizeChange"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalVersions"
          layout="total, sizes, prev, pager, next, jumper"
        />
      </div>

      <div v-if="error" class="error-message">
        <el-alert type="error" :title="error" show-icon :closable="false"></el-alert>
      </div>
       <div v-if="!loading && versions.length === 0 && !error" class="empty-state">
        <el-empty description="No data versions found for this project."></el-empty>
      </div>
    </el-card>

    <!-- Data Detail/View Dialog (Simplified for now) -->
    <el-dialog v-model="showDetailDialog" title="View Data Version" width="80%" top="5vh">
      <div v-if="selectedVersionData">
        <p><strong>Project ID:</strong> {{ selectedVersionData.project_id }}</p>
        <p><strong>Data Entity ID:</strong> {{ selectedVersionData.entity_id }}</p>
        <p><strong>Version:</strong> {{ selectedVersionData.version }}</p>
        <p><strong>File Identifier:</strong> {{ selectedVersionData.file_identifier }}</p>
        <p><strong>Notes:</strong> {{ selectedVersionData.notes || 'N/A' }}</p>
        <!-- Here you would typically display the actual data, e.g., in a table or preview -->
        <el-alert type="info" title="Data Preview Not Implemented Yet" description="Displaying actual data content requires further implementation (e.g., fetching and rendering file content based on file_identifier)." :closable="false"></el-alert>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">Close</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } // Import useRouter
from 'vue-router';
import { ElMessage, ElMessageBox, ElEmpty } from 'element-plus';
import { projectAPI } from '@/api'; // Ensure projectAPI is imported

const props = defineProps({
  projectId: {
    type: [String, Number],
    required: true 
  }
});

const router = useRouter(); // Initialize router
const route = useRoute();

const versions = ref([]);
const loading = ref(true);
const error = ref(null);
const currentPage = ref(1);
const pageSize = ref(10); // Default page size
const totalVersions = ref(0);

const showDetailDialog = ref(false);
const selectedVersionData = ref(null);

const pageTitle = computed(() => `Data Versions for Project ID: ${props.projectId}`);

const fetchProjectVersions = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await projectAPI.getProjectVersions(props.projectId, (currentPage.value - 1) * pageSize.value, pageSize.value);
    // Assuming the API returns a list of version history items directly in response for now.
    // If it's an object like { items: [], total: 0 }, adjust accordingly.
    if (Array.isArray(response)) { // Simple array response
        versions.value = response;
        totalVersions.value = response.length; // This might be incorrect if API doesn't return total count for pagination
                                            // For proper pagination, API should return total count of items.
                                            // Let's assume for now the API returns all items if not paginated by API itself.
                                            // Or if API does paginate, it should return 'total'
    } else if (response && typeof response === 'object' && Array.isArray(response.items)) { // Paginated response
        versions.value = response.items;
        totalVersions.value = response.total;
    } else { // Fallback for unexpected structure
        versions.value = response || []; // Ensure it's an array
        totalVersions.value = (response && response.length) ? response.length : 0;
         console.warn("Unexpected response structure for project versions:", response);
    }

  } catch (err) {
    console.error(`Failed to fetch versions for project ${props.projectId}:`, err);
    error.value = `Failed to load data versions for project ${props.projectId}. Please try again later.`;
    versions.value = []; // Clear data on error
    totalVersions.value = 0;
  } finally {
    loading.value = false;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' };
  return new Date(dateString).toLocaleString(undefined, options);
};

const viewDataVersion = (versionEntry) => {
  // For 'dataset', 'cleaned_data', 'features', we'd typically navigate to a detailed view
  // that might involve fetching and rendering the data (e.g., from a Parquet file).
  // This could use the existing viewProjectDataVersion API endpoint.
  // Example:
  // router.push({ 
  //   name: 'ProjectDataView', // A new route for viewing specific version data
  //   params: { 
  //     projectId: props.projectId, 
  //     dataEntityId: versionEntry.entity_id, 
  //     versionNumber: versionEntry.version 
  //   } 
  // });
  
  // For now, show a simple dialog with metadata
  selectedVersionData.value = versionEntry;
  showDetailDialog.value = true;
  ElMessage.info(`Viewing details for ${versionEntry.entity_type} - ${versionEntry.entity_id} v${versionEntry.version}. Data preview needs implementation.`);
};


const handleSizeChange = (newSize) => {
  pageSize.value = newSize;
  currentPage.value = 1; // Reset to first page
  fetchProjectVersions();
};

const handleCurrentChange = (newPage) => {
  currentPage.value = newPage;
  fetchProjectVersions();
};

watch(() => props.projectId, (newProjectId) => {
  if (newProjectId) {
    currentPage.value = 1; // Reset pagination when project ID changes
    pageSize.value = 10;
    fetchProjectVersions();
  }
}, { immediate: true }); // Fetch on initial load

onMounted(() => {
  if (!props.projectId) {
     error.value = "Project ID is missing. Cannot load data versions.";
     loading.value = false;
     ElMessage.error("Project ID is required to view data versions.");
     // Optionally redirect or handle this state further
  }
  // Data is fetched by the watcher with immediate: true
});
</script>

<style scoped>
.project-data-list { /* Changed class name for clarity */
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.project-context-info {
  margin-bottom: 20px;
  padding: 10px;
  background-color: #f4f4f5;
  border-radius: 4px;
  text-align: center;
}
.pagination-container {
  margin-top: 20px;
  text-align: right;
}
.error-message {
  margin-top: 20px;
}
.empty-state {
  margin-top: 20px;
  text-align: center;
}
</style>
