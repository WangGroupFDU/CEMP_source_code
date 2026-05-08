<template>
  <div class="navbar">
    <div class="navbar-container">
      
      <div class="navbar-left">
        <router-link to="/database" class="logo-link">
          <el-icon :size="28" color="#f97316"><Aim /></el-icon>
          <span class="logo-text">CRYSTALS</span>
        </router-link>
      </div>

      
      <div class="navbar-right">
        <router-link to="/database" class="nav-link">
          Database
        </router-link>
        <router-link to="/prediction" class="nav-link">
          Prediction
        </router-link>
        <router-link to="/visualization" class="nav-link">
          Visualization
        </router-link>
        <a href="https://example.com/" class="nav-link">
          Home
        </a>

        
        <div v-if="!isAuthenticated" class="auth-links">
          <el-button type="primary" size="default" @click="showLoginDialog = true">
            Login
          </el-button>
          <el-button type="success" size="default" @click="showRegisterDialog = true">
            Register
          </el-button>
        </div>
        <div v-else class="user-section">
          <el-dropdown @command="handleUserCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              <span class="username">{{ user?.username }}</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  <div class="user-details">
                    <div><strong>{{ user?.username }}</strong></div>
                    <div class="user-email">{{ user?.email }}</div>
                  </div>
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  Logout
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    
    <el-dialog v-model="showLoginDialog" title="Login" width="400px" :close-on-click-modal="false">
      <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" label-position="top">
        <el-form-item label="Username" prop="username">
          <el-input v-model="loginForm.username" placeholder="Enter username" />
        </el-form-item>
        <el-form-item label="Password" prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="Enter password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showLoginDialog = false">Cancel</el-button>
          <el-button type="primary" :loading="loading" @click="handleLogin">
            Login
          </el-button>
        </span>
      </template>
    </el-dialog>

    
    <el-dialog v-model="showRegisterDialog" title="Register" width="450px" :close-on-click-modal="false">
      <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef" label-position="top">
        <el-form-item label="Username" prop="username">
          <el-input v-model="registerForm.username" placeholder="Enter username" />
        </el-form-item>
        <el-form-item label="Email" prop="email">
          <el-input v-model="registerForm.email" placeholder="Enter email" />
          <div class="form-hint">
            Use educational (.edu), military (.mil), or government (.gov) email for full access
          </div>
        </el-form-item>
        <el-form-item label="Password" prop="password1">
          <el-input v-model="registerForm.password1" type="password" placeholder="Enter password" show-password />
        </el-form-item>
        <el-form-item label="Confirm Password" prop="password2">
          <el-input v-model="registerForm.password2" type="password" placeholder="Confirm password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showRegisterDialog = false">Cancel</el-button>
          <el-button type="success" :loading="loading" @click="handleRegister">
            Register
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuth } from '@/composables/useAuth'
import { Aim, User, ArrowDown, SwitchButton } from '@element-plus/icons-vue'

const { user, isAuthenticated, loading, initAuth, login, register, logout } = useAuth()

const showLoginDialog = ref(false)
const showRegisterDialog = ref(false)

const loginFormRef = ref(null)
const registerFormRef = ref(null)

const loginForm = ref({
  username: '',
  password: ''
})

const loginRules = {
  username: [{ required: true, message: 'Please enter username', trigger: 'blur' }],
  password: [{ required: true, message: 'Please enter password', trigger: 'blur' }]
}

const registerForm = ref({
  username: '',
  email: '',
  password1: '',
  password2: ''
})

const registerRules = {
  username: [{ required: true, message: 'Please enter username', trigger: 'blur' }],
  email: [
    { required: true, message: 'Please enter email', trigger: 'blur' },
    { type: 'email', message: 'Please enter valid email', trigger: 'blur' }
  ],
  password1: [
    { required: true, message: 'Please enter password', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' }
  ],
  password2: [
    { required: true, message: 'Please confirm password', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.value.password1) {
          callback(new Error('Passwords do not match'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const handleLogin = async () => {
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      const result = await login(loginForm.value)
      if (result.success) {
        showLoginDialog.value = false
        loginForm.value = { username: '', password: '' }
      }
    }
  })
}

const handleRegister = async () => {
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      const result = await register(registerForm.value)
      if (result.success) {
        showRegisterDialog.value = false
        registerForm.value = { username: '', email: '', password1: '', password2: '' }
      }
    }
  })
}

const handleUserCommand = async (command) => {
  if (command === 'logout') {
    await logout()
  }
}

onMounted(() => {
  initAuth()
})
</script>

<style scoped>
.navbar {
  background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 2000;
  height: 64px;
}

.navbar-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 2rem;
  max-width: 100%;
}

.navbar-left {
  display: flex;
  align-items: center;
}

.logo-link {
  display: flex;
  align-items: center;
  text-decoration: none;
  transition: transform 0.3s ease;
  gap: 12px;
}

.logo-link:hover {
  transform: scale(1.05);
}

.logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
  letter-spacing: 0.05em;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.nav-link {
  color: #e2e8f0;
  text-decoration: none;
  font-size: 1rem;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  transition: all 0.3s ease;
  position: relative;
}

.nav-link::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 50%;
  width: 0;
  height: 2px;
  background: linear-gradient(90deg, #f97316 0%, #ea580c 100%);
  transition: all 0.3s ease;
  transform: translateX(-50%);
}

.nav-link:hover {
  color: #ffffff;
  background-color: rgba(255, 255, 255, 0.1);
}

.nav-link:hover::after {
  width: 80%;
}

.nav-link.router-link-active {
  color: #f97316;
  background-color: rgba(249, 115, 22, 0.1);
}

.nav-link.router-link-active::after {
  width: 80%;
}


.auth-links {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-left: 1rem;
}

.user-section {
  margin-left: 1rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #e2e8f0;
  cursor: pointer;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.user-info:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.username {
  font-weight: 500;
  font-size: 0.95rem;
}

.user-details {
  padding: 0.25rem 0;
}

.user-email {
  font-size: 0.85rem;
  color: #94a3b8;
  margin-top: 0.25rem;
}


.form-hint {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.25rem;
  line-height: 1.4;
}


@media (max-width: 1024px) {
  .navbar-right {
    gap: 1rem;
  }

  .nav-link {
    font-size: 0.9rem;
    padding: 0.4rem 0.8rem;
  }

  .auth-links {
    margin-left: 0.5rem;
  }

  .user-section {
    margin-left: 0.5rem;
  }
}

@media (max-width: 768px) {
  .navbar-container {
    padding: 0 1rem;
  }

  .logo-text {
    font-size: 1.25rem;
  }

  .navbar-right {
    gap: 0.5rem;
  }

  .nav-link {
    font-size: 0.8rem;
    padding: 0.3rem 0.6rem;
  }

  .auth-links {
    gap: 0.5rem;
  }

  .username {
    display: none;
  }
}
</style>
