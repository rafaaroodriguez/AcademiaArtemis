<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/useAuth'
import { useAcademyStore } from '../stores/useAcademy'

const auth = useAuthStore()
const academy = useAcademyStore()
const router = useRouter()

const plan = computed(() =>
  academy.tiers.find((t) => t.id === auth.usuario?.nivel_id) ?? null,
)

const error = ref('')
const cargando = ref(true)

// Al entrar refrescamos el perfil desde el servidor: así detectamos
// sesiones caducadas y siempre mostramos datos actualizados
onMounted(async () => {
  try {
    await auth.cargarPerfil()
  } catch (e) {
    error.value = (e as Error).message
    if (!auth.estaLogueado) {
      router.push({ path: '/login', query: { redirect: '/cuenta' } })
    }
  } finally {
    cargando.value = false
  }
})

function cerrarSesion() {
  auth.logout()
  router.push('/')
}
</script>

<template>
  <section class="cuenta">
    <h1>Mi cuenta</h1>

    <p v-if="cargando" class="aviso">Cargando tus datos...</p>
    <p v-else-if="error" class="aviso error">{{ error }}</p>

    <template v-else-if="auth.usuario">
      <div class="panel">
        <h2>Mis datos</h2>
        <dl>
          <dt>Nombre</dt>
          <dd>{{ auth.usuario.nombre }}</dd>
          <dt>Email</dt>
          <dd>{{ auth.usuario.email }}</dd>
        </dl>
      </div>

      <div class="panel">
        <h2>Mi suscripción</h2>
        <template v-if="plan">
          <dl>
            <dt>Plan</dt>
            <dd>{{ plan.name }}</dd>
            <dt>Precio</dt>
            <dd>{{ plan.price }}€/mes</dd>
          </dl>
          <div class="acciones">
            <RouterLink :to="`/nivel/${plan.id}`" class="btn">Ir a mi contenido</RouterLink>
            <RouterLink to="/cursos" class="cambiar">Cambiar de plan</RouterLink>
          </div>
        </template>
        <template v-else>
          <p class="sin-plan">Todavía no tienes ninguna suscripción activa.</p>
          <RouterLink to="/cursos" class="btn">Ver planes</RouterLink>
        </template>
      </div>

      <button class="salir" @click="cerrarSesion">Cerrar sesión</button>
    </template>
  </section>
</template>

<style scoped>
.cuenta {
  max-width: 560px;
  margin: 0 auto;
  padding: 60px 20px 80px;
}
.cuenta h1 {
  font-size: 2rem;
  text-align: center;
  margin-bottom: 32px;
}
.aviso {
  text-align: center;
  color: #888;
}
.error {
  color: #c0392b;
}
.panel {
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
}
.panel h2 {
  font-size: 1.1rem;
  color: #f1502f;
  margin-bottom: 16px;
}
dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px 24px;
}
dt {
  font-weight: bold;
  color: #555;
}
.sin-plan {
  color: #555;
  margin-bottom: 16px;
}
.acciones {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
  flex-wrap: wrap;
}
.cambiar {
  color: #f1502f;
  font-weight: bold;
}
.btn {
  display: inline-block;
  background: #f1502f;
  color: white;
  padding: 10px 20px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: bold;
}
.salir {
  display: block;
  margin: 0 auto;
  background: none;
  border: 1px solid #ccc;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  color: #555;
}
.salir:hover {
  border-color: #f1502f;
  color: #f1502f;
}
</style>
