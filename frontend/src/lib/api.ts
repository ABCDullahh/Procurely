import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

/**
 * Axios instance with auth interceptors
 */
export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Request interceptor - add auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

// Response interceptor - handle 401 and refresh token
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config

        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true

            const refreshToken = localStorage.getItem('refresh_token')
            if (refreshToken) {
                try {
                    const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                        refresh_token: refreshToken,
                    })

                    const { access_token, refresh_token } = response.data
                    localStorage.setItem('access_token', access_token)
                    localStorage.setItem('refresh_token', refresh_token)

                    originalRequest.headers.Authorization = `Bearer ${access_token}`
                    return api(originalRequest)
                } catch (refreshError) {
                    // Refresh failed, clear tokens and redirect to login
                    localStorage.removeItem('access_token')
                    localStorage.removeItem('refresh_token')
                    window.location.href = '/login'
                    return Promise.reject(refreshError)
                }
            }

            // No refresh token, redirect to login
            window.location.href = '/login'
        }

        return Promise.reject(error)
    }
)

// Auth API
export const authApi = {
    login: async (email: string, password: string) => {
        const response = await api.post('/auth/login', { email, password })
        return response.data
    },

    refresh: async (refreshToken: string) => {
        const response = await api.post('/auth/refresh', { refresh_token: refreshToken })
        return response.data
    },

    me: async () => {
        const response = await api.get('/auth/me')
        return response.data
    },

    tierInfo: async (): Promise<TierInfo> => {
        const response = await api.get('/auth/me/tier-info')
        return response.data
    },
}

export interface TierInfo {
    tier: string
    searches_used: number
    searches_limit: number  // -1 means unlimited
    can_search: boolean
}

export default api
