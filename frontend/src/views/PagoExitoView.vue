<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/useAuth'
import { useAcademyStore } from '../stores/useAcademy'

const route = useRoute()
const auth = useAuthStore()
const academy = useAcademyStore()

const estado = ref<'verificando' | 'ok' | 'error'>('verificando')
const error = ref('')

const plan = computed(() =>
  academy.tiers.find((t) => t.id === auth.usuario?.nivel_id) ?? null,
)

onMounted(async () => {
  try {
    await auth.confirmarPago((route.query.session_id as string) || '')
    estado.value = 'ok'
  } catch (e) {
    error.value = (e as Error).message
    estado.value = 'error'
  }
})
</script>

<template>
  <section class="pago">
    <template v-if="estado === 'verificando'">
      <h1>Verificando tu pago...</h1>
      <p class="detalle">Un momento, estamos confirmándolo con la pasarela de pago.</p>
    </template>

    <template v-else-if="estado === 'ok'">
      <h1>🎉 ¡Suscripción activada!</h1>
      <p class="detalle">
        Ya tienes acceso a todo el contenido
        <template v-if="plan">del plan {{ plan.name }}</template>.
      </p>
      <RouterLink v-if="plan" :to="`/nivel/${plan.id}`" class="btn">Ir a mi contenido</RouterLink>
    </template>

    <template v-else>
      <h1>No hemos podido confirmar el pago</h1>
      <p class="detalle error">{{ error }}</p>
      <p class="detalle">
        Si crees que el cobro se realizó, escríbenos desde
        <RouterLink to="/contacto">Contacto</RouterLink> y lo revisamos.
      </p>
      <RouterLink to="/cursos" class="btn">Volver a los planes</RouterLink>
    </template>
  </section>
</template>

<style scoped>
.pago {
  max-width: 520px;
  margin: 0 auto;
  padding: 80px 20px;
  text-align: center;
}
.pago h1 {
  font-size: 1.8rem;
  margin-bottom: 16px;
}
.detalle {
  color: #555;
  margin-bottom: 16px;
}
.error {
  color: #c0392b;
  font-weight: bold;
}
.btn {
  display: inline-block;
  background: #f1502f;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: bold;
  margin-top: 8px;
}
.detalle a {
  color: #f1502f;
  font-weight: bold;
}
</style>
