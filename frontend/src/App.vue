<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAcademyStore } from './stores/useAcademy'
import { useAuthStore } from './stores/useAuth'

const academy = useAcademyStore()
const auth = useAuthStore()
const router = useRouter()

// Cuando la página cargue, le pedimos los datos a Python
onMounted(() => {
  academy.fetchInfo()
})

const menuAbierto = ref(false)

// El tema inicial lo fija un script en index.html (antes de pintar nada);
// aquí solo leemos el resultado y gestionamos el cambio
const temaOscuro = ref(document.documentElement.dataset.theme === 'dark')

function alternarTema() {
  temaOscuro.value = !temaOscuro.value
  const tema = temaOscuro.value ? 'dark' : 'light'
  document.documentElement.dataset.theme = tema
  localStorage.setItem('tema', tema)
}

function cerrarSesion() {
  auth.logout()
  router.push('/')
}
</script>

<template>
  <header class="navbar">
    <div class="navbar-contenido">
      <RouterLink to="/" class="logo">
        <span class="logo-marca">A</span>
        Academia Artemis
      </RouterLink>
      <div class="nav-acciones">
        <button
          class="tema-btn"
          :aria-label="temaOscuro ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'"
          :title="temaOscuro ? 'Tema claro' : 'Tema oscuro'"
          @click="alternarTema"
        >
          {{ temaOscuro ? '☀️' : '🌙' }}
        </button>
        <button class="menu-btn" aria-label="Abrir menú" @click="menuAbierto = !menuAbierto">☰</button>
      </div>
      <nav :class="{ abierta: menuAbierto }" @click="menuAbierto = false">
        <RouterLink to="/">Inicio</RouterLink>
        <RouterLink to="/cursos">Cursos</RouterLink>
        <RouterLink to="/contacto">Contacto</RouterLink>
        <template v-if="auth.estaLogueado">
          <RouterLink v-if="auth.esAdmin" to="/admin">Admin</RouterLink>
          <RouterLink to="/cuenta" class="saludo">Hola, {{ auth.usuario!.nombre }}</RouterLink>
          <button class="salir" @click="cerrarSesion">Cerrar sesión</button>
        </template>
        <template v-else>
          <RouterLink to="/login">Iniciar sesión</RouterLink>
          <RouterLink to="/registro" class="destacado">Registrarse</RouterLink>
        </template>
      </nav>
    </div>
  </header>

  <main>
    <RouterView />
  </main>

  <footer class="footer">
    <div class="footer-contenido">
      <div class="footer-col footer-marca">
        <p class="footer-logo"><span class="logo-marca">A</span> Academia Artemis</p>
        <p class="footer-lema">
          Academia 100% online con contenido para todos los niveles: ESO, Bachillerato y
          Universidad.
        </p>
      </div>
      <div class="footer-col">
        <h3>Navegación</h3>
        <RouterLink to="/">Inicio</RouterLink>
        <RouterLink to="/cursos">Cursos</RouterLink>
        <RouterLink to="/contacto">Contacto</RouterLink>
      </div>
      <div class="footer-col">
        <h3>Legal</h3>
        <RouterLink to="/aviso-legal">Aviso legal</RouterLink>
        <RouterLink to="/privacidad">Política de privacidad</RouterLink>
        <RouterLink to="/cookies">Política de cookies</RouterLink>
      </div>
    </div>
    <p class="footer-copy">© {{ new Date().getFullYear() }} Academia Artemis</p>
  </footer>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
</style>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 50;
  background: var(--nav-fondo);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--borde);
}
.navbar-contenido {
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 14px 24px;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--tinta);
  text-decoration: none;
  letter-spacing: -0.02em;
}
.logo-marca {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 9px;
  background: linear-gradient(135deg, var(--marca), var(--marca-oscuro));
  color: white;
  font-weight: 800;
  font-size: 1rem;
  box-shadow: 0 2px 8px rgba(241, 80, 47, 0.35);
}
nav {
  display: flex;
  gap: 22px;
  align-items: center;
  flex-wrap: wrap;
}
nav a {
  color: var(--texto);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.95rem;
}
nav a.router-link-active {
  color: var(--marca);
  font-weight: 700;
}
.destacado {
  background: var(--marca);
  color: white !important;
  padding: 9px 18px;
  border-radius: 10px;
  font-weight: 700;
  transition: background 0.2s ease;
}
.destacado:hover {
  background: var(--marca-oscuro);
}
.saludo {
  color: var(--texto-suave);
}
.salir {
  background: transparent;
  border: 1px solid var(--borde);
  padding: 7px 14px;
  border-radius: 10px;
  cursor: pointer;
  color: var(--texto-suave);
  font-size: 0.9rem;
  font-family: inherit;
}
.salir:hover {
  border-color: var(--marca);
  color: var(--marca);
}
.nav-acciones {
  display: flex;
  align-items: center;
  gap: 8px;
  order: 3;
}
.tema-btn {
  background: transparent;
  border: 1px solid var(--borde);
  border-radius: 10px;
  width: 38px;
  height: 38px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: border-color 0.2s ease;
}
.tema-btn:hover {
  border-color: var(--marca);
}
.menu-btn {
  display: none;
  background: transparent;
  border: none;
  font-size: 1.6rem;
  cursor: pointer;
  color: var(--tinta);
}
@media (min-width: 721px) {
  nav {
    order: 2;
  }
}
@media (max-width: 720px) {
  .menu-btn {
    display: block;
  }
  nav {
    order: 4;
  }
  nav {
    display: none;
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;
    padding-top: 8px;
  }
  nav.abierta {
    display: flex;
  }
}

main {
  min-height: calc(100vh - 280px);
}

.footer {
  background: var(--oscuro);
  color: #cbd5e1;
  margin-top: 60px;
}
.footer-contenido {
  max-width: 1120px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 40px;
  padding: 48px 24px 32px;
}
.footer-col {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.footer-col h3 {
  color: white;
  font-size: 0.95rem;
  margin-bottom: 4px;
}
.footer-col a {
  color: #94a3b8;
  text-decoration: none;
  font-size: 0.92rem;
}
.footer-col a:hover {
  color: white;
}
.footer-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  color: white;
  font-weight: 800;
  font-size: 1.05rem;
}
.footer-lema {
  color: #94a3b8;
  font-size: 0.92rem;
  line-height: 1.6;
  max-width: 320px;
}
.footer-copy {
  text-align: center;
  padding: 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  color: #64748b;
  font-size: 0.85rem;
}
@media (max-width: 720px) {
  .footer-contenido {
    grid-template-columns: 1fr;
    gap: 28px;
  }
}
</style>
