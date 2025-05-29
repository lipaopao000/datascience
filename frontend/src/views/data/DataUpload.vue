<template>
  <div class="data-upload">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ pageTitle }}</span>
          <el-button type="text" @click="showHelp = true">
            <el-icon><QuestionFilled /></el-icon>
            帮助
          </el-button>
        </div>
      </template>

      <div v-if="projectId" class="project-context-info">
        <el-tag type="info">Project ID: {{ projectId }}</el-tag>
      </div>

      <div class="upload-container">
        <el-upload
          ref="uploadRef"
          class="upload-demo"
          drag
          :action="uploadAction" 
          :http-request="handleCustomUpload" 
          :before-upload="beforeUpload"
          :on-success="handleSuccess" 
          :on-error="handleError"
          :on-progress="handleProgress"
          :on-change="handleFileChange"
          :file-list="fileList"
          :auto-upload="false"
          multiple
          accept=".zip,.csv"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 ZIP 压缩包或 CSV 文件，文件大小不超过 500MB
            </div>
          </template>
        </el-upload>

        <el-form-item label="数据分组名称 (可选)" style="margin-top: 20px;" v-if="!projectId">
          <el-input v-model="groupName" placeholder="输入分组名称" />
        </el-form-item>

        <el-form-item label="上传备注 (可选)" style="margin-top: 20px;">
          <el-input v-model="uploadNotes" type="textarea" placeholder="输入本次上传的备注信息" />
        </el-form-item>


        <div class="upload-actions" v-if="fileList.length > 0">
          <el-button type="primary" @click="submitUpload" :loading="uploading">
            <el-icon><Upload /></el-icon>
            开始上传 ({{ fileList.length }} 文件)
          </el-button>
          <el-button @click="clearFiles">
            <el-icon><Delete /></el-icon>
            清空文件
          </el-button>
        </div>

        <!-- 上传进度 -->
        <div class="upload-progress" v-if="uploading">
          <el-progress :percentage="uploadProgress" :status="progressStatus"></el-progress>
          <p class="progress-text">{{ progressText }}</p>
        </div>

        <!-- 上传结果 -->
        <div class="upload-result" v-if="uploadResults.length > 0">
          <div v-for="(result, index) in uploadResults" :key="index" style="margin-bottom: 15px;">
            <el-alert
              :title="result.title"
              :type="result.type"
              :description="result.description"
              show-icon
              :closable="false"
            />
            
            <div class="result-details" v-if="result.details">
              <el-descriptions :title="`文件: ${result.fileName}`" :column="2" border>
                <el-descriptions-item label="数据文件数" v-if="result.details.patient_count !== undefined">
                  {{ result.details.patient_count }}
                </el-descriptions-item>
                 <el-descriptions-item label="数据实体ID" v-if="result.details.data_entity_id">
                  {{ result.details.data_entity_id }}
                </el-descriptions-item>
                <el-descriptions-item label="版本号" v-if="result.details.version_number !== undefined">
                  {{ result.details.version_number }}
                </el-descriptions-item>
                <el-descriptions-item label="文件类型" v-if="result.details.file_info?.source">
                  {{ result.details.file_info?.source || '未知' }}
                </el-descriptions-item>
                <el-descriptions-item label="数据ID (旧)" v-if="result.details.file_info?.data_id">
                  {{ result.details.file_info.data_id }}
                </el-descriptions-item>
                 <el-descriptions-item label="分组名称" v-if="result.details.file_info?.group_name">
                  {{ result.details.file_info.group_name }}
                </el-descriptions-item>
                <el-descriptions-item label="处理文件数" v-if="result.details.file_info?.extracted_files">
                  {{ result.details.file_info.extracted_files }}
                </el-descriptions-item>
                <el-descriptions-item label="数据行数" v-if="result.details.file_info?.rows">
                  {{ result.details.file_info.rows }}
                </el-descriptions-item>
                <el-descriptions-item label="数据列数" v-if="result.details.file_info?.columns">
                  {{ result.details.file_info.columns.length }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 帮助对话框 -->
    <el-dialog v-model="showHelp" title="上传帮助" width="600px">
      <div class="help-content">
        <h3>支持的文件格式</h3>
        <ul>
          <li><strong>ZIP 压缩包：</strong>包含患者文件夹结构的压缩包，每个患者文件夹包含 ECG*.csv 和 MV*.csv 文件</li>
          <li><strong>CSV 文件：</strong>单个 ECG 或 MV 数据文件</li>
        </ul>

        <h3>文件结构要求</h3>
        <p>对于 ZIP 文件，推荐的目录结构：</p>
        <pre>
data.zip
├── 患者ID1/
│   ├── 时间段1/
│   │   ├── ECG_xxx.csv
│   │   └── MV_xxx.csv
│   └── 时间段2/
│       ├── ECG_xxx.csv
│       └── MV_xxx.csv
└── 患者ID2/
    └── ...
        </pre>

        <h3>数据格式要求</h3>
        <p>支持任意时序数据，请确保数据列名清晰，数值型数据可直接用于分析。</p>
        <p>对于特定格式的CSV文件（如无表头的高频数据），请先在“数据模式管理”中定义相应的模式，并在上传时选择该模式。</p>

        <h3>注意事项</h3>
        <ul>
          <li>文件大小限制：500MB</li>
          <li>CSV 文件编码：UTF-8</li>
          <li>数据将自动进行清洗和预处理</li>
          <li>上传完成后可在"数据列表"中查看</li>
        </ul>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { dataAPI, projectAPI } from '@/api'; // Ensure projectAPI is imported

const props = defineProps({
  projectId: {
    type: [String, Number],
    required: false // Not required for generic upload
  }
});

const uploadRef = ref();
const fileList = ref([]);
const uploading = ref(false);
const uploadProgress = ref(0);
const progressStatus = ref('');
const progressText = ref('');
const uploadResults = ref([]); 
const showHelp = ref(false);
const groupName = ref('');
const uploadNotes = ref(''); // For project-specific upload notes

const pageTitle = computed(() => props.projectId ? `Upload Data to Project ${props.projectId}` : '数据上传');
const uploadAction = 'http://localhost:8000/api/upload'; // Dummy action, as we use custom http-request

// 上传前检查
const beforeUpload = (file) => {
  const isValidType = file.type === 'application/zip' || 
                     file.type === 'text/csv' || 
                     file.name.endsWith('.zip') || 
                     file.name.endsWith('.csv');
  
  if (!isValidType) {
    ElMessage.error('只支持 ZIP 和 CSV 文件格式');
    return false;
  }

  const isValidSize = file.size / 1024 / 1024 < 500;
  if (!isValidSize) {
    ElMessage.error('文件大小不能超过 500MB');
    return false;
  }
  return true;
};

// Custom upload handler
const handleCustomUpload = async (options) => {
  // This function will be called by el-upload when auto-upload is false and submitUpload is triggered.
  // However, we are manually bundling files in submitUpload, so this might not be directly used
  // unless el-upload's internal submit is triggered. For our case, we manage upload via projectAPI directly.
  // For simplicity, we'll ensure submitUpload calls the correct API.
  // This custom request can be left empty if submitUpload handles everything.
  console.log('Custom HTTP request called, but we handle upload via submitUpload method.');
  return Promise.resolve(); // Or reject if needed
};


// 开始上传
const submitUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择文件');
    return;
  }

  uploading.value = true;
  uploadProgress.value = 0; // We might not have fine-grained progress for multiple files easily
  progressStatus.value = '';
  progressText.value = '准备上传...';
  uploadResults.value = []; // Clear previous results

  const formData = new FormData();
  fileList.value.forEach(fileObject => {
    formData.append('files', fileObject.raw); // Ensure we append the raw file
  });

  if (props.projectId && uploadNotes.value) {
    formData.append('notes', uploadNotes.value);
  }
  
  // For generic upload, if not project specific
  if (!props.projectId && groupName.value) {
     // The generic dataAPI.uploadData expects groupName as a query param, not in FormData
     // This part needs careful handling if generic upload is still to be supported alongside project upload.
     // For now, focusing on project-specific upload if projectId is present.
  }


  try {
    let response;
    if (props.projectId) {
      progressText.value = `正在上传到项目 ${props.projectId}...`;
      response = await projectAPI.uploadProjectData(props.projectId, formData);
       // Assuming response structure for project upload might be: { message: string, files: [...] }
      // Update results based on this new structure
      uploadProgress.value = 100;
      progressStatus.value = 'success';
      progressText.value = response.message || `${response.files?.length || 0} 文件处理完成。`;

      if (response.files && Array.isArray(response.files)) {
        response.files.forEach(fileSummary => {
            uploadResults.value.push({
            title: `文件 ${fileSummary.file_name} 处理成功`,
            type: 'success',
            description: `数据实体ID: ${fileSummary.data_entity_id}, 版本: ${fileSummary.version_number}`,
            details: fileSummary, // Contains data_entity_id, version_number, etc.
            fileName: fileSummary.file_name
          });
        });
      } else {
         // Handle cases where 'files' might not be an array or present, e.g., single file upload response
         uploadResults.value.push({
            title: '上传完成',
            type: 'success',
            description: response.message || '操作成功完成。',
            details: response, 
            fileName: "N/A" 
          });
      }
      ElMessage.success(response.message || '上传成功！');

    } else {
      // Fallback to generic upload if projectId is not present
      progressText.value = '正在上传...';
      // Note: dataAPI.uploadData takes (filesArray, groupName)
      // filesToUpload should be an array of File objects, not FormData
      const filesToUpload = fileList.value.map(f => f.raw);
      response = await dataAPI.uploadData(filesToUpload, groupName.value);
      
      // Existing result handling for generic upload
      uploadProgress.value = 100;
      progressStatus.value = 'success';
      progressText.value = `上传完成: ${response.patient_count || (response.file_info ? response.file_info.uploaded_files_summary.length : 0)} 个数据集成功处理`;

      if (response.file_info && response.file_info.uploaded_files_summary) {
         response.file_info.uploaded_files_summary.forEach(fileSummary => {
            uploadResults.value.push({
                title: fileSummary.source === 'zip' ? 'ZIP文件处理成功' : 'CSV文件处理成功',
                type: 'success',
                description: `文件 ${fileSummary.file_name} 处理成功。数据ID: ${fileSummary.data_id || 'N/A'}`,
                details: {
                patient_count: fileSummary.source === 'zip' ? fileSummary.extracted_files : 1,
                file_info: fileSummary
                },
                fileName: fileSummary.file_name
            });
        });
      }
      ElMessage.success(response.message || "上传成功！");
    }
  } catch (error) {
    uploadProgress.value = 100;
    progressStatus.value = 'exception';
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    progressText.value = `上传失败: ${errorMessage}`;
    uploadResults.value.push({
      title: '上传失败',
      type: 'error',
      description: `文件上传失败: ${errorMessage}`,
      fileName: fileList.value.map(f => f.name).join(', ')
    });
    // ElMessage for error is handled by global interceptor
  } finally {
    setTimeout(() => {
      clearFiles(); // Clear files after a delay to allow user to see results
    }, 5000); // Increased delay
    uploading.value = false;
  }
};

const handleProgress = (event, file, fileListInternal) => {
  // This is called by el-upload's internal XHR.
  // Since we use a custom submit, we'll manually set progress.
  // If we were to use el-upload's :http-request for fine-grained progress, this would be relevant.
  // For now, a simple "uploading..." state is managed by submitUpload.
};

const handleSuccess = (response, file, fileListInternal) => {
  // Primarily for auto-upload or if :http-request resolves.
  // Our submitUpload handles success logic.
};

const handleError = (error, file, fileListInternal) => {
  // Primarily for auto-upload or if :http-request rejects.
  // Our submitUpload handles error logic.
};

const handleFileChange = (file, newFileList) => {
  fileList.value = newFileList;
};

const clearFiles = () => {
  fileList.value = [];
  uploadResults.value = [];
  uploadProgress.value = 0;
  uploading.value = false;
  groupName.value = '';
  uploadNotes.value = ''; // Clear notes as well
};
</script>

<style scoped>
.data-upload {
  max-width: 800px;
  margin: 20px auto; /* Added margin for better page layout */
  padding: 20px;
}

.project-context-info {
  margin-bottom: 20px;
  text-align: center; /* Center the project ID tag */
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-container {
  padding: 20px 0;
}

.upload-demo {
  margin-bottom: 20px;
}

.upload-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin: 20px 0;
}

.upload-progress {
  margin: 20px 0;
  text-align: center;
}

.progress-text {
  margin-top: 10px;
  color: #606266;
  font-size: 14px;
}

.upload-result {
  margin-top: 20px;
}

.result-details {
  margin-top: 15px;
}

.help-content h3 {
  color: #409EFF;
  margin: 20px 0 10px 0;
  font-size: 16px;
}

.help-content ul {
  margin: 10px 0;
  padding-left: 20px;
}

.help-content li {
  margin: 5px 0;
  line-height: 1.5;
}

.help-content pre {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  overflow-x: auto;
}

:deep(.el-upload-dragger) {
  width: 100%;
  height: 180px;
}

:deep(.el-icon--upload) {
  font-size: 67px;
  color: #c0c4cc;
  margin: 40px 0 16px;
}

:deep(.el-upload__text) {
  color: #606266;
  font-size: 14px;
}

:deep(.el-upload__text em) {
  color: #409EFF;
  font-style: normal;
}

:deep(.el-upload__tip) {
  font-size: 12px;
  color: #606266;
  margin-top: 7px;
}
</style>
