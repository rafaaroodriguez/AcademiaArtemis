<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { isAxiosError } from 'axios'
import { api } from '../lib/api'

const route = useRoute()

const password = ref('')
const mensaje = ref('')
const error = ref('')
const enviando = ref(false)

async function enviar() {
  mensaje.value = ''
  error.value = ''
  enviando.value = true
  try {
    const { data } = await api.post('/api/restablecer', {
      token: route.query.token || '',
      password: password.value,
    })
    mensaje.value = data.mensaje
  } catch (e) {
    if (isAxiosError(e) && e.response?.data?.error) {
      error.value = e.response.data.error
    } else {
      error.value = 'No se pudo conectar con el servidor. Inténtalo de nuevo.'
    }
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <section class="auth">
    <h1>Nueva contraseña</h1>

    <template v-if="mensaje">
      <p class="ok">{{ mensaje }}</p>
      <RouterLink to="/login" class="btn">Iniciar sesión</RouterLink>
    </template>

    <form v-else @submit.prevent="enviar">
      <label>
        Contraseña nueva
        <input
          v-model="password"
          type="password"
          required
          minlength="6"
          autocomplete="new-password"
          placeholder="Mínimo 6 caracteres"
        />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="enviando">
        {{ enviando ? 'Guardando...' : 'Guardar contraseña' }}
      </button>
    </form>
  </section>
</template>

<style scoped>
.auth {
  max-width: 380px;
  margin: 0 auto;
  padding: 60px 20px 80px;
  text-align: center;
}
.auth h1 {
  font-size: 1.8rem;
  margin-bottom: 24px;
}
form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  text-align: left;
}
label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-weight: bold;
  font-size: 0.95rem;
}
input {
  padding: 10px 12px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 1rem;
}
input:focus {
  outline: 2px solid #f1502f;
  border-color: transparent;
}
button,
.btn {
  background: #f1502f;
  color: white;
  border: none;
  padding: 12px;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  text-decoration: none;
  display: inline-block;
}
button:disabled {
  opacity: 0.6;
  cursor: default;
}
.ok {
  color: #27ae60;
  font-weight: bold;
  margin-bottom: 20px;
}
.error {
  color: #c0392b;
  font-size: 0.95rem;
}
</style>
