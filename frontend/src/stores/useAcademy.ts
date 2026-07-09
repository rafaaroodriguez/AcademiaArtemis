import {defineStore} from 'pinia';
import axios from 'axios';

// En local usa el Flask de tu máquina; en Vercel se define VITE_API_URL
// con la URL del backend desplegado en Render.
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

export interface Nivel {
    id: number;
    name: string;
    price: number;
    benefits: string;
}

export const useAcademyStore = defineStore('academy', {
    state: () => ({
        name: '',
        tagline: '',
        tiers: [] as Nivel[],
    }),
    actions: {
        async fetchInfo(){
            try {
                const response = await axios.get(`${API_URL}/api/datos_academia`);
                this.name = response.data.nombre;
                this.tagline = response.data.biografia;
                this.tiers = response.data.niveles;
            } catch (error) {
                console.error('Failed to fetch academy info:', error);
            }
        }
    }
})
