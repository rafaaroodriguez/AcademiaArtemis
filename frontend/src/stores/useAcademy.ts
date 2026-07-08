import {defineStore} from 'pinia';
import axios from 'axios';

export const useAcademyStore = defineStore('academy', {
    state: () => ({
        name: '',
        tagline: '',
        tiers: [] as any[],
    }),
    actions: {
        async fetchInfo(){
            try {
                const response = await axios.get('http://127.0.0.1:5000/api/datos_academia');
                this.name = response.data.nombre;
                this.tagline = response.data.biografia;
                this.tiers = response.data.niveles;
            } catch (error) {
                console.error('Failed to fetch academy info:', error);
            }
        }
    }
})