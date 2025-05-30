<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <span>{{ $t('login.login') }}</span>
        </div>
      </template>
      <el-form @submit.prevent="handleLogin" :model="loginForm" :rules="rules" ref="loginFormRef">
        <el-form-item prop="username">
          <el-input v-model="loginForm.username" :placeholder="$t('login.username')" prefix-icon="User"></el-input>
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="loginForm.password" type="password" :placeholder="$t('login.password')" prefix-icon="Lock" show-password></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading" class="login-button">{{ $t('login.login') }}</el-button>
          <el-button @click="goToRegister" class="register-button">{{ $t('login.register') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { authAPI } from '@/api';
import { useI18n } from 'vue-i18n'; // Import useI18n

const loginForm = reactive({
  username: '',
  password: '',
});

const loginFormRef = ref(null);
const loading = ref(false);
const router = useRouter();
const { t } = useI18n(); // Initialize useI18n

const rules = {
  username: [{ required: true, message: t('login.usernameRequired'), trigger: 'blur' }],
  password: [{ required: true, message: t('login.passwordRequired'), trigger: 'blur' }],
};

const goToRegister = () => {
  router.push('/register');
};

const handleLogin = async () => {
  if (!loginFormRef.value) return;
  loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        await authAPI.loginUser(loginForm.username, loginForm.password);
        ElMessage.success(t('login.loginSuccessful'));
        router.push('/projects'); // Or '/dashboard'
      } catch (error) {
        // Error message is handled by the API interceptor, but you can add specific logic here if needed
        console.error('Login failed:', error);
      } finally {
        loading.value = false;
      }
    } else {
      ElMessage.error(t('login.fillAllFields'));
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
  margin-bottom: 10px; /* Add some space between buttons */
}

.register-button {
  width: 100%;
}
</style>
