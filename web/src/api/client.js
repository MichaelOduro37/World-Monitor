import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const client = axios.create({ baseURL: BASE_URL })

// Attach token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error)
    else prom.resolve(token)
  })
  failedQueue = []
}

// Auto-refresh on 401
client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            original.headers.Authorization = `Bearer ${token}`
            return client(original)
          })
          .catch((err) => Promise.reject(err))
      }
      original._retry = true
      isRefreshing = true
      const refresh = localStorage.getItem('refresh_token')
      if (!refresh) {
        isRefreshing = false
        return Promise.reject(error)
      }
      try {
        const { data } = await axios.post(`${BASE_URL}/auth/refresh`, { refresh_token: refresh })
        localStorage.setItem('access_token', data.access_token)
        if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
        client.defaults.headers.common.Authorization = `Bearer ${data.access_token}`
        processQueue(null, data.access_token)
        original.headers.Authorization = `Bearer ${data.access_token}`
        return client(original)
      } catch (err) {
        processQueue(err, null)
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(err)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  }
)

export default client

// Auth
export const login = (email, password) => {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  return client
    .post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    .then((r) => r.data)
}

export const register = (email, password, full_name) =>
  client.post('/auth/register', { email, password, full_name }).then((r) => r.data)

export const refreshToken = (refresh_token) =>
  client.post('/auth/refresh', { refresh_token }).then((r) => r.data)

export const getMe = () => client.get('/auth/me').then((r) => r.data)

// Events
export const getEvents = (params = {}) =>
  client.get('/events', { params }).then((r) => r.data)

export const getEvent = (id) => client.get(`/events/${id}`).then((r) => r.data)

// Subscriptions
export const getSubscriptions = () => client.get('/subscriptions').then((r) => r.data)

export const createSubscription = (payload) =>
  client.post('/subscriptions', payload).then((r) => r.data)

export const updateSubscription = (id, payload) =>
  client.put(`/subscriptions/${id}`, payload).then((r) => r.data)

export const deleteSubscription = (id) =>
  client.delete(`/subscriptions/${id}`).then((r) => r.data)

// Stats
export const getStatsSummary = () => client.get('/stats/summary').then((r) => r.data)

export const getStatsHotspots = (days = 7) =>
  client.get('/stats/hotspots', { params: { days } }).then((r) => r.data)
