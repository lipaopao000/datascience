<template>
  <div class="project-data-tab">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>Project Data</h3>
          <el-button type="primary" @click="goToDataUpload">Upload New Data</el-button>
        </div>
      </template>

      <!-- ProjectDataList component will handle displaying data versions and actions -->
      <ProjectDataList :projectId="Number(projectId)" />
    </el-card>
  </div>
</template>

<script setup>
import { defineProps } from 'vue';
import { useRouter } from 'vue-router';
import ProjectDataList from '@/components/ProjectDataList.vue'; // Import the new component

const props = defineProps({
  projectId: {
    type: Number,
    required: true
  }
});

const router = useRouter();

const goToDataUpload = () => {
  router.push({ name: 'ProjectDataUpload', params: { projectId: props.projectId } });
};
</script>

<style scoped>
.project-data-tab {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
