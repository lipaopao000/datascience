<template>
  <div class="data-upload">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据上传</span>
          <el-button type="text" @click="showHelp = true">
            <el-icon><QuestionFilled /></el-icon>
            帮助
          </el-button>
        </div>
      </template>

      <div class="upload-container">
        <el-upload
          ref="uploadRef"
          class="upload-demo"
          drag
          :action="uploadAction"
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

        <el-form-item label="数据分组名称 (可选)" style="margin-top: 20px;">
          <el-input v-model="groupName" placeholder="输入分组名称" />
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
                <el-descriptions-item label="数据文件数">
                  {{ result.details.patient_count }}
                </el-descriptions-item>
                <el-descriptions-item label="文件类型">
                  {{ result.details.file_info?.source || '未知' }}
                </el-descriptions-item>
                <el-descriptions-item label="数据ID" v-if="result.details.file_info?.data_id">
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
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { dataAPI } from '@/api'

const uploadRef = ref()
const fileList = ref([])
const uploading = ref(false)
const uploadProgress = ref(0)
const progressStatus = ref('')
const progressText = ref('')
const uploadResults = ref([]) 
const showHelp = ref(false)
const groupName = ref('')

const uploadAction = 'http://localhost:8000/api/upload'

// 上传前检查
const beforeUpload = (file) => {
  const isValidType = file.type === 'application/zip' || 
                     file.type === 'text/csv' || 
                     file.name.endsWith('.zip') || 
                     file.name.endsWith('.csv')
  
  if (!isValidType) {
    ElMessage.error('只支持 ZIP 和 CSV 文件格式')
    return false
  }

  const isValidSize = file.size / 1024 / 1024 < 500
  if (!isValidSize) {
    ElMessage.error('文件大小不能超过 500MB')
    return false
  }

  return true
}

// 开始上传
const submitUpload = async () => {
  console.log('submitUpload: function started');
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择文件')
    console.log('submitUpload: No file selected');
    return
  }

  uploading.value = true
  uploadProgress.value = 0
  progressStatus.value = ''
  progressText.value = '准备上传...'
  uploadResults.value = [] // Clear previous results

  let totalFiles = fileList.value.length;
  let filesToUpload = fileList.value.map(f => f.raw);
  let fileNames = filesToUpload.map(f => f.name).join(', ');
  try {
    console.log(`submitUpload: Uploading files`, filesToUpload, 'with groupName:', groupName.value);
    const response = await dataAPI.uploadData(filesToUpload, groupName.value); 
    console.log(`submitUpload: API response for files:`, response);
    
    uploadProgress.value = 100;
    progressStatus.value = 'success';
    progressText.value = `上传完成: ${response.patient_count} 个数据集成功处理`;

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
    
    ElMessage.success(response.message);

  } catch (error) {
    uploadProgress.value = 100;
    progressStatus.value = 'exception';
    progressText.value = '上传失败';
    
    const errorMessage = error.response?.data?.detail || error.message || '未知错误';
    uploadResults.value.push({
      title: '上传失败',
      type: 'error',
      description: `文件上传失败: ${errorMessage}`,
      fileName: fileNames 
    });
    ElMessage.error(`数据上传失败: ${errorMessage}`);
  } finally {
    setTimeout(() => {
      clearFiles();
    }, 3000);
    uploading.value = false;
  }
}

const handleProgress = (event) => {
  // Not used for manual upload
}

const handleSuccess = (response) => {
  // Not used for manual upload
}

const handleError = (error) => {
 // Not used for manual upload
}

const handleFileChange = (file, newFileList) => {
  fileList.value = newFileList;
  console.log('handleFileChange: fileList updated', fileList.value);
};

const clearFiles = () => {
  fileList.value = []
  uploadResults.value = [] 
  uploadProgress.value = 0
  uploading.value = false
  groupName.value = ''
}
</script>

<style scoped>
.data-upload {
  max-width: 800px;
  margin: 0 auto;
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
