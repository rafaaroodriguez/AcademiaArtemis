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

    <div v-if="!academy.tiers.length" class="cargando">
      <span class="loader"></span>
      <span>Cargando niveles...</span>
    </div>
    <p v-if="error" class="error">{{ error }}</p>

    <div class="tiers-grid">
      <div
        v-for="tier in academy.tiers"
        :key="tier.id"
        class="card"
        :class="{ popular: tier.id === 2 }"
      >
        <p v-if="tier.id === 2" class="etiqueta-popular">El más elegido</p>
        <h2>{{ tier.name }}</h2>
        <p class="price">{{ tier.price }}€<span class="per">/mes</span></p>
        <ul class="ventajas">
          <li>{{ tier.benefits }}</li>
          <li>Temario por asignaturas</li>
          <li>Sin permanencia</li>
        </ul>

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
  position: relative;
  border: 1px solid var(--borde);
  padding: 32px 28px;
  border-radius: var(--radio);
  width: 260px;
  background: white;
  box-shadow: var(--sombra);
  display: flex;
  flex-direction: column;
  gap: 14px;
  text-align: left;
}
.card h2 {
  font-size: 1.15rem;
}
.card.popular {
  border-color: var(--marca);
  box-shadow: 0 8px 28px rgba(241, 80, 47, 0.18);
}
.etiqueta-popular {
  position: absolute;
  top: -13px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--marca);
  color: white;
  font-size: 0.78rem;
  font-weight: 700;
  padding: 4px 14px;
  border-radius: 999px;
  white-space: nowrap;
}
.price {
  font-size: 2.2rem;
  font-weight: 800;
  color: var(--tinta);
  letter-spacing: -0.02em;
}
.per {
  font-size: 0.95rem;
  color: var(--texto-suave);
  font-weight: normal;
}
.ventajas {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex-grow: 1;
  padding: 0;
}
.ventajas li {
  color: var(--texto-suave);
  font-size: 0.93rem;
  padding-left: 26px;
  position: relative;
  line-height: 1.45;
}
.ventajas li::before {
  content: '✓';
  position: absolute;
  left: 0;
  color: var(--marca);
  font-weight: 800;
}
.btn {
  background: var(--marca);
  color: white;
  padding: 12px 20px;
  border-radius: 10px;
  text-decoration: none;
  font-weight: 700;
  border: none;
  font-size: 0.98rem;
  cursor: pointer;
  text-align: center;
  font-family: inherit;
}
.btn:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>
