import { ref, computed } from 'vue'
import { authApi } from '@/services/authApi'
import { ElMessage } from 'element-plus'


const user = ref(null)
const isAuthenticated = ref(false)
const loading = ref(false)


export function useAuth() {

  const initAuth = async () => {

    const storedUser = authApi.getStoredUser()
    const storedToken = authApi.getStoredToken()

    if (storedToken && storedUser) {
      user.value = storedUser
      isAuthenticated.value = true
      console.log('✓ Auth initialized from localStorage')
      return
    }


    try {
      console.log('No token in localStorage, attempting Session auto-login...')
      const response = await authApi.getOrCreateTokenFromSession()

      if (response.data.success) {
        user.value = response.data.user
        isAuthenticated.value = true
        console.log('✓ Auto-login successful via Session Cookie')
        ElMessage.success('Welcome back! Auto-login successful')
      }
    } catch (error) {

      if (error.response?.status === 401) {
        console.log('No active session found, user needs to login')
      } else {
        console.error('Auto-login error:', error)
      }
    }
  }

  
  const login = async (credentials) => {
    loading.value = true
    try {
      const response = await authApi.login(credentials)

      if (response.data.success) {
        user.value = response.data.user
        isAuthenticated.value = true
        ElMessage.success(response.data.message || 'Login successful')
        return { success: true }
      } else {
        ElMessage.error(response.data.error || 'Login failed')
        return { success: false, error: response.data.error }
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.response?.data?.message || 'Login failed, please try again'
      ElMessage.error(errorMsg)
      return { success: false, error: errorMsg }
    } finally {
      loading.value = false
    }
  }

  
  const register = async (userData) => {
    loading.value = true
    try {
      const response = await authApi.register(userData)

      if (response.data.success) {
        user.value = response.data.user
        isAuthenticated.value = true


        if (response.data.limited_access) {
          ElMessage.warning({
            message: response.data.message,
            duration: 5000
          })
        } else {
          ElMessage.success(response.data.message || 'Registration successful')
        }

        return { success: true, limitedAccess: response.data.limited_access }
      } else {

        if (response.data.errors) {
          const errorMessages = Object.values(response.data.errors).flat().join('; ')
          ElMessage.error(errorMessages)
          return { success: false, errors: response.data.errors }
        }
        ElMessage.error(response.data.error || 'Registration failed')
        return { success: false, error: response.data.error }
      }
    } catch (error) {
      const errorData = error.response?.data
      if (errorData?.errors) {
        const errorMessages = Object.values(errorData.errors).flat().join('; ')
        ElMessage.error(errorMessages)
        return { success: false, errors: errorData.errors }
      }
      const errorMsg = errorData?.error || errorData?.message || 'Registration failed, please try again'
      ElMessage.error(errorMsg)
      return { success: false, error: errorMsg }
    } finally {
      loading.value = false
    }
  }

  
  const logout = async () => {
    loading.value = true
    try {
      await authApi.logout()
      user.value = null
      isAuthenticated.value = false
      ElMessage.success('Logout successful')
    } catch (error) {
      console.error('Logout error:', error)

      user.value = null
      isAuthenticated.value = false
      ElMessage.warning('Logged out, but server communication failed')
    } finally {
      loading.value = false
    }
  }

  
  const refreshUserInfo = async () => {
    if (!isAuthenticated.value) return

    loading.value = true
    try {
      const response = await authApi.getUserInfo()
      if (response.data) {
        user.value = response.data
      }
    } catch (error) {
      console.error('Failed to refresh user info:', error)

      if (error.response?.status === 401) {
        user.value = null
        isAuthenticated.value = false
      }
    } finally {
      loading.value = false
    }
  }


  const userPermissions = computed(() => user.value?.permissions || {})

  const hasAutoComputePermission = computed(() =>
    userPermissions.value.auto_compute_permission || false
  )

  const hasDatabasePermission = computed(() =>
    userPermissions.value.database_permission !== false
  )

  const hasMLPredictionPermission = computed(() =>
    userPermissions.value.ml_prediction_permission !== false
  )

  const hasGaussianPermission = computed(() =>
    userPermissions.value.gaussian_permission || false
  )

  const dailyTaskLimit = computed(() =>
    userPermissions.value.daily_task_limit || 0
  )

  return {

    user,
    isAuthenticated,
    loading,


    initAuth,
    login,
    register,
    logout,
    refreshUserInfo,


    userPermissions,
    hasAutoComputePermission,
    hasDatabasePermission,
    hasMLPredictionPermission,
    hasGaussianPermission,
    dailyTaskLimit
  }
}
