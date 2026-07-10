import { defineStore } from 'pinia'
import { isAxiosError } from 'axios'
import { api } from '../lib/api'

export interface Usuario {
  id: number
  nombre: string
  email: string
  nivel_id: number | null
}

function mensajeDeError(error: unknown): string {
  if (isAxiosError(error) && error.response?.data?.error) {
    return error.response.data.error
  }
  return 'No se pudo conectar con el servidor. Inténtalo de nuevo.'
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    usuario: JSON.parse(localStorage.getItem('usuario') || 'null') as Usuario | null,
  }),
  getters: {
    estaLogueado: (state) => state.usuario !== null,
  },
  actions: {
    guardarSesion(token: string, usuario: Usuario) {
      localStorage.setItem('token', token)
      localStorage.setItem('usuario', JSON.stringify(usuario))
      this.usuario = usuario
    },
    async registro(nombre: string, email: string, password: string) {
      try {
        const { data } = await api.post('/api/registro', { nombre, email, password })
        this.guardarSesion(data.token, data.usuario)
      } catch (error) {
        throw new Error(mensajeDeError(error))
      }
    },
    async login(email: string, password: string) {
      try {
        const { data } = await api.post('/api/login', { email, password })
        this.guardarSesion(data.token, data.usuario)
      } catch (error) {
        throw new Error(mensajeDeError(error))
      }
    },
    // TODO (paso 4): esto pasará por el pago de Stripe antes de activar el plan
    async elegirPlan(nivelId: number) {
      try {
        const { data } = await api.post('/api/suscripcion', { nivel_id: nivelId })
        this.usuario = data.usuario
        localStorage.setItem('usuario', JSON.stringify(data.usuario))
      } catch (error) {
        throw new Error(mensajeDeError(error))
      }
    },
    // Pide el perfil al servidor; si el token caducó o no es válido, cierra la sesión
    async cargarPerfil() {
      try {
        const { data } = await api.get('/api/perfil')
        this.usuario = data.usuario
        localStorage.setItem('usuario', JSON.stringify(data.usuario))
      } catch (error) {
        // 401: token caducado · 422: token inválido (flask-jwt-extended)
        const status = isAxiosError(error) ? error.response?.status : undefined
        if (status === 401 || status === 422) {
          this.logout()
          throw new Error('Tu sesión ha caducado. Vuelve a iniciar sesión.')
        }
        throw new Error(mensajeDeError(error))
      }
    },
    logout() {
      localStorage.removeItem('token')
      localStorage.removeItem('usuario')
      this.usuario = null
    },
  },
})
