<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAcademyStore } from '../stores/useAcademy'
import { useAuthStore } from '../stores/useAuth'

const academy = useAcademyStore()
const auth = useAuthStore()
const router = useRouter()

const error = ref('')
const eligiendo = ref(0)

async function elegirPlan(nivelId: number) {
  error.value = ''
  eligiendo.value = nivelId
  try {
    // Con Stripe configurado, elegirPlan redirige a la página de pago y no
    // volvemos por aquí; sin Stripe la activación es directa
    const activadoDirectamente = await auth.elegirPlan(nivelId)
    if (activadoDirectamente) {
      router.push(`/nivel/${nivelId}`)
    }
  } catch (e) {
    error.value = (e as Error).message
    eligiendo.value = 0
  }
}
</script>

<template>
  <section class="cursos">
    <h1>Nuestros cursos</h1>
    <p class="intro">Elige el nivel que se ajusta a tu etapa. Todos los planes son mensuales y sin permanencia.</p>

    <p v-if="!academy.tiers.length" class="loading">Cargando niveles...</p>
    <p v-if="error" class="error">{{ error }}</p>

    <div class="tiers-grid">
      <div v-for="tier in academy.tiers" :key="tier.id" class="card">
        <h2>{{ tier.name }}</h2>
        <p class="price">{{ tier.price }}€<span class="per">/mes</span></p>
        <p class="benefits">{{ tier.benefits }}</p>

        <!-- Sin sesión: a registrarse -->
        <RouterLink v-if="!auth.estaLogueado" to="/registro" class="btn">Apuntarme</RouterLink>

        <!-- Con sesión y este plan contratado: al contenido -->
        <RouterLink
          v-else-if="auth.usuario!.nivel_id === tier.id"
          :to="`/nivel/${tier.id}`"
          class="btn"
        >
          Entrar al contenido
        </RouterLink>

        <!-- Con sesión y otro plan (o ninguno): contratar este -->
        <button v-else class="btn" :disabled="eligiendo !== 0" @click="elegirPlan(tier.id)">
          {{ eligiendo === tier.id ? 'Activando...' : auth.usuario!.nivel_id ? 'Cambiar a este plan' : 'Elegir este plan' }}
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.cursos {
  text-align: center;
  padding: 60px 20px 80px;
}
.cursos h1 {
  font-size: 2rem;
  margin-bottom: 12px;
}
.intro {
  color: #555;
  max-width: 560px;
  margin: 0 auto;
}
.loading {
  margin-top: 40px;
  color: #888;
}
.error {
  margin-top: 20px;
  color: #c0392b;
}
.tiers-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 20px;
  margin-top: 40px;
}
.card {
  border: 1px solid #ddd;
  padding: 24px;
  border-radius: 12px;
  width: 220px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.price {
  font-size: 1.8rem;
  font-weight: bold;
  color: #f1502f;
}
.per {
  font-size: 0.9rem;
  color: #888;
  font-weight: normal;
}
.benefits {
  color: #555;
  flex-grow: 1;
}
.btn {
  background: #f1502f;
  color: white;
  padding: 10px 20px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: bold;
  border: none;
  font-size: 1rem;
  cursor: pointer;
}
.btn:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>
