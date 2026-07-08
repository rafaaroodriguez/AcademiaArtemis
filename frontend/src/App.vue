<script setup lang="ts">
import { onMounted } from 'vue'
import { useAcademyStore } from './stores/useAcademy'

const academy = useAcademyStore()

// Cuando la página cargue, le pedimos los datos a Python
onMounted(() => {
  academy.fetchInfo()
})
</script>

<template>
  <div class="container">
    <header>
      <h1>{{ academy.name || 'Cargando...' }}</h1>
      <p>{{ academy.tagline }}</p>
    </header>

    <div class="tiers-grid">
      <div v-for="tier in academy.tiers" :key="tier.id" class="card">
        <h2>{{ tier.name }}</h2>
        <p class="price">{{ tier.price }}€</p>
        <p>{{ tier.benefits }}</p>
        <button>Seleccionar</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.container 
{ 
  text-align: center; 
  font-family: sans-serif; 
  padding: 20px; 
}
.tiers-grid 
{ 
  display: flex; 
  justify-content: center; 
  gap: 20px; 
  margin-top: 40px; 
}
.card 
{ 
  border: 1px solid #ddd; 
  padding: 20px; 
  border-radius: 12px; 
  width: 200px; 
  box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
}
.price 
{ 
  font-size: 1.5rem; 
  font-weight: bold; 
  color: #f1502f; 
}
button 
{ 
  background: #f1502f; 
  color: white; 
  border: none; 
  padding: 10px 20px; 
  border-radius: 5px; 
  cursor: pointer; 
}
</style>