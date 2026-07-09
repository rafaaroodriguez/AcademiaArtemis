<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { useAcademyStore } from './stores/useAcademy'

const academy = useAcademyStore()

// Cuando la página cargue, le pedimos los datos a Python
onMounted(() => {
  academy.fetchInfo()
})
</script>

<template>
  <header class="navbar">
    <RouterLink to="/" class="logo">Academia Artemis</RouterLink>
    <nav>
      <RouterLink to="/">Inicio</RouterLink>
      <RouterLink to="/cursos">Cursos</RouterLink>
      <RouterLink to="/contacto">Contacto</RouterLink>
    </nav>
  </header>

  <main>
    <RouterView />
  </main>

  <footer class="footer">
    <p>© {{ new Date().getFullYear() }} Academia Artemis · Academia 100% online</p>
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
</style>
