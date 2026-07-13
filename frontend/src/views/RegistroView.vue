<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/useAuth'

const auth = useAuthStore()
const router = useRouter()

const nombre = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const enviando = ref(false)

async function enviar() {
  error.value = ''
  enviando.value = true
  try {
    await auth.registro(nombre.value, email.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <section class="auth">
    <h1>Crear cuenta</h1>
    <form @submit.prevent="enviar">
      <label>
        Nombre
        <input v-model="nombre" type="text" required autocomplete="name" />
      </label>
      <label>
        Email
        <input v-model="email" type="email" required autocomplete="email" />
      </label>
      <label>
        Contraseña
        <input
          v-model="password"
          type="password"
          required
          minlength="6"
          autocomplete="new-password"
          placeholder="Mínimo 6 caracteres"
        />
      </label>
      <label class="acepto">
        <input type="checkbox" required />
        <span>
          He leído y acepto la
          <RouterLink to="/privacidad" target="_blank">política de privacidad</RouterLink>
        </span>
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="enviando">
        {{ enviando ? 'Creando cuenta...' : 'Registrarme' }}
      </button>
    </form>
    <p class="cambio">
      ¿Ya tienes cuenta?
      <RouterLink to="/login">Inicia sesión</RouterLink>
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
button {
  background: #f1502f;
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
.acepto {
  flex-direction: row;
  align-items: flex-start;
  gap: 8px;
  font-weight: normal;
  color: #555;
}
.acepto a {
  color: #f1502f;
}
.error {
  color: #c0392b;
  font-size: 0.95rem;
}
.cambio {
  margin-top: 24px;
  color: #555;
}
.cambio a {
  color: #f1502f;
  font-weight: bold;
}
</style>
