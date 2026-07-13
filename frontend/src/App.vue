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

function cerrarSesion() {
  auth.logout()
  router.push('/')
}
</script>

<template>
  <header class="navbar">
    <RouterLink to="/" class="logo">Academia Artemis</RouterLink>
    <button
      class="menu-btn"
      aria-label="Abrir menú"
      @click="menuAbierto = !menuAbierto"
    >
      ☰
    </button>
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
  </header>

  <main>
    <RouterView />
  </main>

  <footer class="footer">
    <p>© {{ new Date().getFullYear() }} Academia Artemis · Academia 100% online</p>
    <nav class="legal-links">
      <RouterLink to="/aviso-legal">Aviso legal</RouterLink>
      <RouterLink to="/privacidad">Privacidad</RouterLink>
      <RouterLink to="/cookies">Cookies</RouterLink>
    </nav>
  </footer>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: sans-serif;
  color: #333;
}
</style>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 16px 24px;
  border-bottom: 1px solid #eee;
}
.logo {
  font-size: 1.2rem;
  font-weight: bold;
  color: #f1502f;
  text-decoration: none;
}
nav {
  display: flex;
  gap: 20px;
}
nav a {
  color: #333;
  text-decoration: none;
}
nav a.router-link-active {
  color: #f1502f;
  font-weight: bold;
}
nav {
  align-items: center;
  flex-wrap: wrap;
}
.destacado {
  background: #f1502f;
  color: white !important;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: bold;
}
.saludo {
  color: #555;
}
.salir {
  background: none;
  border: 1px solid #ccc;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  color: #555;
  font-size: 0.9rem;
}
.salir:hover {
  border-color: #f1502f;
  color: #f1502f;
}
.menu-btn {
  display: none;
  background: none;
  border: none;
  font-size: 1.6rem;
  cursor: pointer;
  color: #333;
}
@media (max-width: 720px) {
  .menu-btn {
    display: block;
  }
  .navbar nav {
    display: none;
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;
    padding-top: 8px;
  }
  .navbar nav.abierta {
    display: flex;
  }
}
main {
  min-height: calc(100vh - 130px);
}
.footer {
  text-align: center;
  padding: 20px;
  border-top: 1px solid #eee;
  color: #888;
  font-size: 0.9rem;
}
.legal-links {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 8px;
}
.legal-links a {
  color: #888;
  text-decoration: none;
}
.legal-links a:hover {
  color: #f1502f;
}
</style>
