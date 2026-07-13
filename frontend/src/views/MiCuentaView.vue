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
const mensajeCancelacion = ref('')
const cancelando = ref(false)

async function cancelarSuscripcion() {
  if (!confirm('¿Seguro que quieres cancelar tu suscripción?')) return
  mensajeCancelacion.value = ''
  cancelando.value = true
  try {
    mensajeCancelacion.value = await auth.cancelarSuscripcion()
  } catch (e) {
    mensajeCancelacion.value = (e as Error).message
  } finally {
    cancelando.value = false
  }
}

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

    <div v-if="cargando" class="cargando">
      <span class="loader"></span>
      <span>Cargando tus datos...</span>
    </div>
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
          <p v-if="auth.usuario!.cancelacion_pendiente" class="aviso-cancelacion">
            Cancelación programada: mantienes el acceso hasta el final del periodo ya pagado.
          </p>
          <div class="acciones">
            <RouterLink :to="`/nivel/${plan.id}`" class="btn">Ir a mi contenido</RouterLink>
            <RouterLink to="/cursos" class="cambiar">Cambiar de plan</RouterLink>
            <button
              v-if="!auth.usuario!.cancelacion_pendiente"
              class="cancelar"
              :disabled="cancelando"
              @click="cancelarSuscripcion"
            >
              {{ cancelando ? 'Cancelando...' : 'Cancelar suscripción' }}
            </button>
          </div>
        </template>
        <template v-else>
          <p class="sin-plan">Todavía no tienes ninguna suscripción activa.</p>
          <RouterLink to="/cursos" class="btn">Ver planes</RouterLink>
        </template>
        <p v-if="mensajeCancelacion" class="mensaje-cancelacion">{{ mensajeCancelacion }}</p>
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
.cancelar {
  background: none;
  border: 1px solid #ccc;
  color: #777;
  border-radius: 8px;
  padding: 8px 14px;
  cursor: pointer;
  font-size: 0.9rem;
}
.cancelar:hover {
  border-color: #c0392b;
  color: #c0392b;
}
.cancelar:disabled {
  opacity: 0.6;
  cursor: default;
}
.aviso-cancelacion {
  background: #fff6e5;
  border: 1px solid #f0c36d;
  border-radius: 8px;
  padding: 10px 14px;
  color: #7a5b13;
  font-size: 0.95rem;
  margin-bottom: 12px;
}
.mensaje-cancelacion {
  margin-top: 12px;
  color: #555;
  font-size: 0.95rem;
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
