import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import { useAuthStore } from '../stores/useAuth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'inicio', component: HomeView },
    { path: '/cursos', name: 'cursos', component: () => import('../views/CursosView.vue') },
    { path: '/contacto', name: 'contacto', component: () => import('../views/ContactoView.vue') },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { soloInvitados: true },
    },
    {
      path: '/registro',
      name: 'registro',
      component: () => import('../views/RegistroView.vue'),
      meta: { soloInvitados: true },
    },
    {
      path: '/cuenta',
      name: 'cuenta',
      component: () => import('../views/MiCuentaView.vue'),
      meta: { requiereSesion: true },
    },
    {
      path: '/nivel/:id',
      name: 'nivel',
      component: () => import('../views/NivelView.vue'),
      meta: { requiereSesion: true },
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('../views/AdminView.vue'),
      meta: { requiereSesion: true, requiereAdmin: true },
    },
    {
      path: '/recuperar',
      name: 'recuperar',
      component: () => import('../views/RecuperarView.vue'),
      meta: { soloInvitados: true },
    },
    {
      path: '/restablecer',
      name: 'restablecer',
      component: () => import('../views/RestablecerView.vue'),
      meta: { soloInvitados: true },
    },
    { path: '/aviso-legal', name: 'aviso-legal', component: () => import('../views/AvisoLegalView.vue') },
    { path: '/privacidad', name: 'privacidad', component: () => import('../views/PrivacidadView.vue') },
    { path: '/cookies', name: 'cookies', component: () => import('../views/CookiesView.vue') },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  // Las páginas privadas piden iniciar sesión y recuerdan a dónde ibas
  if (to.meta.requiereSesion && !auth.estaLogueado) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  // Con la sesión iniciada, login y registro no pintan nada
  if (to.meta.soloInvitados && auth.estaLogueado) {
    return { path: '/cuenta' }
  }
  // La zona de administración solo la ven los administradores
  if (to.meta.requiereAdmin && !auth.esAdmin) {
    return { path: '/' }
  }
})

export default router
