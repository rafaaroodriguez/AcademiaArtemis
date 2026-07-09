import { defineStore } from 'pinia'
import { api } from '../lib/api'

export interface Nivel {
  id: number
  name: string
  price: number
  benefits: string
}

export const useAcademyStore = defineStore('academy', {
  state: () => ({
    name: '',
    tagline: '',
    tiers: [] as Nivel[],
  }),
  actions: {
    async fetchInfo() {
      try {
        const response = await api.get('/api/datos_academia')
        this.name = response.data.nombre
        this.tagline = response.data.biografia
        this.tiers = response.data.niveles
      } catch (error) {
        console.error('Failed to fetch academy info:', error)
      }
    },
  },
})
