<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { isAxiosError } from 'axios'
import { api } from '../lib/api'

interface Tema {
  id: number
  titulo: string
  descripcion: string
  material_url: string
}

interface Asignatura {
  id: number
  nombre: string
  temas: Tema[]
}

const route = useRoute()

const nombreNivel = ref('')
const asignaturas = ref<Asignatura[]>([])
const error = ref('')
const cargando = ref(true)

async function cargar(nivelId: string) {
  cargando.value = true
  error.value = ''
  try {
    const { data } = await api.get(`/api/niveles/${nivelId}/contenido`)
    nombreNivel.value = data.nivel.name
    asignaturas.value = data.asignaturas
  } catch (e) {
    if (isAxiosError(e) && e.response?.data?.error) {
      error.value = e.response.data.error
    } else {
      error.value = 'No se pudo cargar el contenido. Inténtalo de nuevo.'
    }
  } finally {
    cargando.value = false
  }
}

// immediate: carga al entrar; watch: recarga si se navega entre niveles
watch(() => route.params.id as string, cargar, { immediate: true })
</script>

<template>
  <section class="nivel">
    <p v-if="cargando" class="aviso">Cargando contenido...</p>
    <div v-else-if="error" class="aviso">
      <p class="error">{{ error }}</p>
      <RouterLink to="/cursos" class="volver">Ver los planes disponibles</RouterLink>
    </div>

    <template v-else>
      <h1>{{ nombreNivel }}</h1>
      <p class="intro">Todo el contenido de tu nivel, organizado por asignaturas.</p>

      <div v-for="asignatura in asignaturas" :key="asignatura.id" class="asignatura">
        <h2>{{ asignatura.nombre }}</h2>
        <ol>
          <li v-for="tema in asignatura.temas" :key="tema.id">
            <div class="tema">
              <strong>{{ tema.titulo }}</strong>
              <p>{{ tema.descripcion }}</p>
              <a v-if="tema.material_url" :href="tema.material_url" target="_blank" rel="noopener">
                Abrir material
              </a>
              <span v-else class="pronto">Material disponible próximamente</span>
            </div>
          </li>
        </ol>
      </div>
    </template>
  </section>
</template>

<style scoped>
.nivel {
  max-width: 720px;
  margin: 0 auto;
  padding: 60px 20px 80px;
}
.nivel h1 {
  font-size: 2rem;
  text-align: center;
}
.intro {
  text-align: center;
  color: #555;
  margin: 12px 0 40px;
}
.aviso {
  text-align: center;
  color: #888;
}
.error {
  color: #c0392b;
}
.volver {
  display: inline-block;
  margin-top: 12px;
  color: #f1502f;
  font-weight: bold;
}
.asignatura {
  margin-bottom: 32px;
}
.asignatura h2 {
  font-size: 1.3rem;
  color: #f1502f;
  border-bottom: 2px solid #f1502f;
  padding-bottom: 8px;
  margin-bottom: 16px;
}
ol {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.tema {
  border: 1px solid #eee;
  border-radius: 10px;
  padding: 16px;
}
.tema p {
  color: #555;
  margin: 6px 0;
}
.tema a {
  color: #f1502f;
  font-weight: bold;
}
.pronto {
  color: #999;
  font-size: 0.9rem;
  font-style: italic;
}
</style>
