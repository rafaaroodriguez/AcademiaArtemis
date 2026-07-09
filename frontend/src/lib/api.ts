import axios from 'axios'

// En local usa el Flask de tu máquina; en Vercel se define VITE_API_URL
// con la URL del backend desplegado en Render.
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000',
})

// Si hay sesión iniciada, todas las peticiones llevan el token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
