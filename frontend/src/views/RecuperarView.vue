<script setup lang="ts">
import { ref } from 'vue'
import { api } from '../lib/api'

const email = ref('')
const mensaje = ref('')
const error = ref('')
const enviando = ref(false)

async function enviar() {
  mensaje.value = ''
  error.value = ''
  enviando.value = true
  try {
    const { data } = await api.post('/api/recuperar', { email: email.value })
    mensaje.value = data.mensaje
  } catch {
    error.value = 'No se pudo conectar con el servidor. Inténtalo de nuevo.'
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <section class="auth">
    <h1>Recuperar contraseña</h1>
    <p class="explicacion">
      Escribe el email de tu cuenta y te enviaremos un enlace para crear una contraseña nueva.
    </p>

    <p v-if="mensaje" class="ok">{{ mensaje }}</p>

    <form v-else @submit.prevent="enviar">
      <label>
        Email
        <input v-model="email" type="email" required autocomplete="email" />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="enviando">
        {{ enviando ? 'Enviando...' : 'Enviar enlace' }}
      </button>
    </form>

    <p class="cambio">
      <RouterLink to="/login">Volver a iniciar sesión</RouterLink>
    </p>
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
  margin-bottom: 12px;
}
.explicacion {
  color: var(--texto-suave);
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
  border: 1px solid var(--borde);
  border-radius: 8px;
  font-size: 1rem;
}
input:focus {
  outline: 2px solid #f1502f;
  border-color: transparent;
}
button {
  background: var(--marca);
  color: white;
  border: none;
  padding: 12px;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
}
button:disabled {
  opacity: 0.6;
  cursor: default;
}
.ok {
  color: #27ae60;
  font-weight: bold;
}
.error {
  color: #c0392b;
  font-size: 0.95rem;
}
.cambio {
  margin-top: 24px;
}
.cambio a {
  color: var(--marca);
  font-weight: bold;
}
</style>
