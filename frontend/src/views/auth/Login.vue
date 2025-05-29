<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <span>Login</span>
        </div>
      </template>
      <el-form @submit.prevent="handleLogin" :model="loginForm" :rules="rules" ref="loginFormRef">
        <el-form-item prop="username">
          <el-input v-model="loginForm.username" placeholder="Username" prefix-icon="User"></el-input>
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="Password" prefix-icon="Lock" show-password></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading" class="login-button">Login</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { authAPI } from '@/api'; // Assuming your api/index.js is aliased as @/api

const loginForm = reactive({
  username: '',
  password: '',
});

const loginFormRef = ref(null);
const loading = ref(false);
const router = useRouter();

const rules = {
  username: [{ required: true, message: 'Please input username', trigger: 'blur' }],
  password: [{ required: true, message: 'Please input password', trigger: 'blur' }],
};

const handleLogin = async () => {
  if (!loginFormRef.value) return;
  loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        await authAPI.loginUser(loginForm.username, loginForm.password);
        ElMessage.success('Login successful!');
        router.push('/projects'); // Or '/dashboard'
      } catch (error) {
        // Error message is handled by the API interceptor, but you can add specific logic here if needed
        console.error('Login failed:', error);
      } finally {
        loading.value = false;
      }
    } else {
      ElMessage.error('Please fill in all fields correctly.');
      return false;
    }
  });
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5; /* Optional: Add a background color */
}

.login-card {
  width: 400px;
}

.card-header {
  text-align: center;
  font-size: 20px;
}

.login-button {
  width: 100%;
}
</style>
