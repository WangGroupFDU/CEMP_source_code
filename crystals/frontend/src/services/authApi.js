import axios from 'axios'

const authClient = axios.create({
  baseURL: '',
  timeout: 30000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})


authClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('cemp_token')
    if (token) {
      config.headers.Authorization = `Token ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)


authClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('cemp_token')
      localStorage.removeItem('cemp_user')
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  async login(credentials) {
    const response = await authClient.post('/register/login/', credentials)

    if (response.data.success && response.data.token) {
      localStorage.setItem('cemp_token', response.data.token)
      localStorage.setItem('cemp_user', JSON.stringify(response.data.user))
    }

    return response
  },

  async register(userData) {
    const response = await authClient.post('/register/register/', userData)

    if (response.data.success && response.data.token) {
      localStorage.setItem('cemp_token', response.data.token)
      localStorage.setItem('cemp_user', JSON.stringify(response.data.user))
    }

    return response
  },

  async logout() {
    try {
      const response = await authClient.post('/register/logout/', {})
      return response
    } finally {
      localStorage.removeItem('cemp_token')
      localStorage.removeItem('cemp_user')
    }
  },

  async getUserInfo() {
    const response = await authClient.get('/register/api/user/')

    if (response.data) {
      localStorage.setItem('cemp_user', JSON.stringify(response.data))
    }

    return response
  },

  isAuthenticated() {
    return !!localStorage.getItem('cemp_token')
  },

  getStoredUser() {
    const userStr = localStorage.getItem('cemp_user')
    try {
      return userStr ? JSON.parse(userStr) : null
    } catch (error) {
      return null
    }
  },

  getStoredToken() {
    return localStorage.getItem('cemp_token')
  },

  async getOrCreateTokenFromSession() {
    const response = await authClient.get('/register/api/get-or-create-token/')

    if (response.data.success && response.data.token) {
      localStorage.setItem('cemp_token', response.data.token)
      localStorage.setItem('cemp_user', JSON.stringify(response.data.user))
    }

    return response
  }
}

export default authApi
