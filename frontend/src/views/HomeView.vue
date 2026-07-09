<script setup lang="ts">
import { useAcademyStore } from '../stores/useAcademy'

const academy = useAcademyStore()
</script>

<template>
  <section class="hero">
    <h1>{{ academy.name || 'Academia Artemis' }}</h1>
    <p class="tagline">{{ academy.tagline || 'Academia 100% online para todos los niveles' }}</p>
    <div class="hero-actions">
      <RouterLink to="/cursos" class="btn btn-primary">Ver cursos</RouterLink>
      <RouterLink to="/contacto" class="btn btn-secondary">Contactar</RouterLink>
    </div>
  </section>

  <section class="features">
    <div class="feature">
      <h2>100% online</h2>
      <p>Estudia donde y cuando quieras, con contenido siempre disponible.</p>
    </div>
    <div class="feature">
      <h2>Todos los niveles</h2>
      <p>ESO, Bachillerato y Universidad: un plan para cada etapa.</p>
    </div>
    <div class="feature">
      <h2>Desde 5€/mes</h2>
      <p>Precios pensados para estudiantes, sin permanencia.</p>
    </div>
  </section>
</template>

<style scoped>
.hero {
  text-align: center;
  padding: 80px 20px 60px;
}
.hero h1 {
  font-size: 2.5rem;
  margin-bottom: 12px;
}
.tagline {
  font-size: 1.2rem;
  color: #555;
  max-width: 560px;
  margin: 0 auto 32px;
}
.hero-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}
.btn {
  padding: 12px 28px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: bold;
}
.btn-primary {
  background: #f1502f;
  color: white;
}
.btn-secondary {
  border: 2px solid #f1502f;
  color: #f1502f;
}
.features {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 24px;
  padding: 40px 20px 80px;
}
.feature {
  width: 260px;
  text-align: center;
  padding: 24px;
  border: 1px solid #eee;
  border-radius: 12px;
}
.feature h2 {
  font-size: 1.2rem;
  color: #f1502f;
  margin-bottom: 8px;
}
.feature p {
  color: #555;
}
</style>
