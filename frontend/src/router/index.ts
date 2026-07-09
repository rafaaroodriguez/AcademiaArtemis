import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'inicio', component: HomeView },
    { path: '/cursos', name: 'cursos', component: () => import('../views/CursosView.vue') },
    { path: '/contacto', name: 'contacto', component: () => import('../views/ContactoView.vue') },
  ],
})

export default router
