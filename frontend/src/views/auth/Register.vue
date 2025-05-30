<template>
  <div class="register-container">
    <el-card class="register-card">
      <template #header>
        <div class="card-header">
          <span>Register</span>
        </div>
      </template>
      <el-form :model="registerForm" :rules="rules" ref="registerFormRef" label-width="auto" class="register-form">
        <el-form-item label="Username" prop="username">
          <el-input v-model="registerForm.username" placeholder="Enter your username"></el-input>
        </el-form-item>
        <el-form-item label="Email (Optional)" prop="email">
          <el-input v-model="registerForm.email" placeholder="Enter your email"></el-input>
        </el-form-item>
        <el-form-item label="Password" prop="password">
          <el-input type="password" v-model="registerForm.password" placeholder="Enter your password" show-password></el-input>
        </el-form-item>
        <el-form-item label="Confirm Password" prop="confirmPassword">
          <el-input type="password" v-model="registerForm.confirmPassword" placeholder="Confirm your password" show-password></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleRegister" :loading="loading">Register</el-button>
          <el-button @click="goToLogin">Back to Login</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { authAPI } from '@/api'; // Ensure authAPI is imported

const router = useRouter();

const registerFormRef = ref(null);
const loading = ref(false);

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
});

const validatePass = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('Please input the password'));
  } else {
    if (registerForm.confirmPassword !== '') {
      if (!registerFormRef.value) return;
      registerFormRef.value.validateField('confirmPassword', () => null);
    }
    callback();
  }
};

const validatePass2 = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('Please input the password again'));
  } else if (value !== registerForm.password) {
    callback(new Error("Two inputs don't match!"));
  } else {
    callback();
  }
};

const rules = reactive({
  username: [
    { required: true, message: 'Please enter username', trigger: 'blur' },
    { min: 3, message: 'Length should be at least 3', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: 'Please enter a valid email address', trigger: ['blur', 'change'] }
  ],
  password: [
    { required: true, validator: validatePass, trigger: 'blur' },
    { min: 6, message: 'Length should be at least 6', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validatePass2, trigger: 'blur' }
  ]
});

const handleRegister = async () => {
  if (!registerFormRef.value) return;
  registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const response = await authAPI.registerUser({
          username: registerForm.username,
          email: registerForm.email || undefined, // Send undefined if empty
          password: registerForm.password
        });
        ElMessage.success('Registration successful! Please log in.');
        router.push('/login'); // Redirect to login page
      } catch (error) {
        console.error('Registration failed:', error);
        ElMessage.error(error.message || 'Registration failed. Please try again.');
      } finally {
        loading.value = false;
      }
    } else {
      ElMessage.error('Please correct the form errors.');
      return false;
    }
  });
};

const goToLogin = () => {
  router.push('/login');
};
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f0f2f5;
}

.register-card {
  width: 450px;
  max-width: 90%;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  text-align: center;
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

.register-form {
  padding: 20px;
}

.el-button {
  width: 100%;
  margin-bottom: 10px;
}
</style>
