<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { isAxiosError } from 'axios'
import { api } from '../lib/api'
import { useAcademyStore } from '../stores/useAcademy'
import type { Usuario } from '../stores/useAuth'

interface Material {
  id: number
  tipo: string
  titulo: string
  url: string
}

interface Tema {
  id: number
  titulo: string
  descripcion: string
  materiales: Material[]
}

interface Asignatura {
  id: number
  nombre: string
  temas: Tema[]
}

const academy = useAcademyStore()

const alumnos = ref<Usuario[]>([])
const nivelActivo = ref(1)
const asignaturas = ref<Asignatura[]>([])
const error = ref('')

// Formularios
const nuevaAsignatura = ref('')
const nuevoTema = ref<Record<number, { titulo: string; descripcion: string; material_url: string }>>({})

function mensaje(e: unknown): string {
  if (isAxiosError(e) && e.response?.data?.error) return e.response.data.error
  return 'Error de conexión con el servidor'
}

async function cargarAlumnos() {
  const { data } = await api.get('/api/admin/alumnos')
  alumnos.value = data.alumnos
}

async function cargarContenido() {
  const { data } = await api.get(`/api/niveles/${nivelActivo.value}/contenido`)
  asignaturas.value = data.asignaturas
  for (const a of asignaturas.value) {
    if (!nuevoTema.value[a.id]) {
      nuevoTema.value[a.id] = { titulo: '', descripcion: '', material_url: '' }
    }
  }
}

async function cambiarNivel(id: number) {
  nivelActivo.value = id
  error.value = ''
  try {
    await cargarContenido()
  } catch (e) {
    error.value = mensaje(e)
  }
}

async function crearAsignatura() {
  error.value = ''
  try {
    await api.post('/api/admin/asignaturas', {
      nivel_id: nivelActivo.value,
      nombre: nuevaAsignatura.value,
    })
    nuevaAsignatura.value = ''
    await cargarContenido()
  } catch (e) {
    error.value = mensaje(e)
  }
}

async function borrarAsignatura(id: number) {
  if (!confirm('¿Borrar la asignatura con todos sus temas?')) return
  error.value = ''
  try {
    await api.delete(`/api/admin/asignaturas/${id}`)
    await cargarContenido()
  } catch (e) {
    error.value = mensaje(e)
  }
}

async function crearTema(asignaturaId: number) {
  error.value = ''
  try {
    await api.post(`/api/admin/asignaturas/${asignaturaId}/temas`, nuevoTema.value[asignaturaId])
    nuevoTema.value[asignaturaId] = { titulo: '', descripcion: '', material_url: '' }
    await cargarContenido()
  } catch (e) {
    error.value = mensaje(e)
  }
}

const editandoTema = ref<number | null>(null)
const formEdicion = ref({ titulo: '', descripcion: '' })

function empezarEdicion(tema: Tema) {
  editandoTema.value = tema.id
  formEdicion.value = {
    titulo: tema.titulo,
    descripcion: tema.descripcion,
  }
}

// --- Niveles y precios ---
const formNiveles = ref<Record<number, { nombre: string; precio: number; descripcion: string }>>({})
const nivelGuardado = ref(0)

function prepararFormNiveles() {
  for (const tier of academy.tiers) {
    formNiveles.value[tier.id] = {
      nombre: tier.name,
      precio: tier.price,
      descripcion: tier.benefits,
    }
  }
}

async function guardarNivel(nivelId: number) {
  error.value = ''
  nivelGuardado.value = 0
  try {
    await api.put(`/api/admin/niveles/${nivelId}`, formNiveles.value[nivelId])
    await academy.fetchInfo()
    prepararFormNiveles()
    nivelGuardado.value = nivelId
  } catch (e) {
    error.value = mensaje(e)
  }
}

// --- Materiales de un tema ---
const nuevoMaterial = ref<Record<number, { tipo: string; titulo: string; url: string }>>({})

function formMaterial(temaId: number) {
  if (!nuevoMaterial.value[temaId]) {
    nuevoMaterial.value[temaId] = { tipo: 'apuntes', titulo: '', url: '' }
  }
  return nuevoMaterial.value[temaId]
}

async function crearMaterial(temaId: number) {
  error.value = ''
  try {
    await api.post(`/api/admin/temas/${temaId}/materiales`, nuevoMaterial.value[temaId])
    nuevoMaterial.value[temaId] = { tipo: 'apuntes', titulo: '', url: '' }
    await cargarContenido()
  } catch (e) {
    error.value = mensaje(e)
  }
}

async function borrarMaterial(materialId: number) {
  if (!confirm('¿Borrar este material?')) return
  error.value = ''
  try {
    await api.delete(`/api/admin/materiales/${materialId}`)
    await cargarContenido()
  } catch (e) {
    error.value = mensaje(e)
  }
}

async function guardarTema(temaId: number) {
  error.value = ''
  try {
    await api.put(`/api/admin/temas/${temaId}`, formEdicion.value)
    editandoTema.value = null
    await cargarContenido()
  } catch (e) {
    error.value = mensaje(e)
  }
}

async function moverTema(temaId: number, direccion: 'subir' | 'bajar') {
  error.value = ''
  try {
    await api.post(`/api/admin/temas/${temaId}/mover`, { direccion })
    await cargarContenido()
  } catch (e) {
    error.value = mensaje(e)
  }
}

async function renombrarAsignatura(asignatura: Asignatura) {
  const nombre = prompt('Nuevo nombre de la asignatura:', asignatura.nombre)
  if (!nombre || nombre.trim() === asignatura.nombre) return
  error.value = ''
  try {
    await api.put(`/api/admin/asignaturas/${asignatura.id}`, { nombre })
    await cargarContenido()
  } catch (e) {
    error.value = mensaje(e)
  }
}

async function borrarAlumno(alumno: Usuario) {
  if (!confirm(`¿Borrar la cuenta de ${alumno.nombre} (${alumno.email})?`)) return
  error.value = ''
  try {
    await api.delete(`/api/admin/alumnos/${alumno.id}`)
    await cargarAlumnos()
  } catch (e) {
    error.value = mensaje(e)
  }
}

async function borrarTema(id: number) {
  if (!confirm('¿Borrar este tema?')) return
  error.value = ''
  try {
    await api.delete(`/api/admin/temas/${id}`)
    await cargarContenido()
  } catch (e) {
    error.value = mensaje(e)
  }
}

function nombreNivel(id: number | null): string {
  return academy.tiers.find((t) => t.id === id)?.name ?? '—'
}

onMounted(async () => {
  try {
    await Promise.all([cargarAlumnos(), cargarContenido()])
    if (!academy.tiers.length) {
      await academy.fetchInfo()
    }
    prepararFormNiveles()
  } catch (e) {
    error.value = mensaje(e)
  }
})
</script>

<template>
  <section class="admin">
    <h1>Panel de administración</h1>
    <p v-if="error" class="error">{{ error }}</p>

    <div class="panel">
      <h2>Alumnos ({{ alumnos.length }})</h2>
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Email</th>
            <th>Plan</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="alumno in alumnos" :key="alumno.id">
            <td>{{ alumno.nombre }} <span v-if="alumno.es_admin" class="etiqueta">admin</span></td>
            <td>{{ alumno.email }}</td>
            <td>{{ nombreNivel(alumno.nivel_id) }}</td>
            <td class="acciones-fila">
              <button v-if="!alumno.es_admin" class="borrar" @click="borrarAlumno(alumno)">
                Borrar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="panel">
      <h2>Niveles y precios</h2>
      <form
        v-for="tier in academy.tiers"
        :key="tier.id"
        class="fila-nivel"
        @submit.prevent="guardarNivel(tier.id)"
      >
        <template v-if="formNiveles[tier.id]">
          <input v-model="formNiveles[tier.id]!.nombre" class="campo-nombre" required />
          <div class="campo-precio">
            <input
              v-model.number="formNiveles[tier.id]!.precio"
              type="number"
              step="0.01"
              min="0.01"
              required
            />
            <span>€/mes</span>
          </div>
          <input
            v-model="formNiveles[tier.id]!.descripcion"
            class="campo-descripcion"
            placeholder="Descripción del plan"
          />
          <button type="submit" class="guardar">
            {{ nivelGuardado === tier.id ? 'Guardado ✓' : 'Guardar' }}
          </button>
        </template>
      </form>
    </div>

    <div class="panel">
      <h2>Temario</h2>
      <div class="niveles">
        <button
          v-for="tier in academy.tiers"
          :key="tier.id"
          :class="{ activo: tier.id === nivelActivo }"
          @click="cambiarNivel(tier.id)"
        >
          {{ tier.name }}
        </button>
      </div>

      <div v-for="asignatura in asignaturas" :key="asignatura.id" class="asignatura">
        <div class="cabecera">
          <h3>{{ asignatura.nombre }}</h3>
          <div class="botones">
            <button class="accion" @click="renombrarAsignatura(asignatura)">Renombrar</button>
            <button class="borrar" @click="borrarAsignatura(asignatura.id)">Borrar asignatura</button>
          </div>
        </div>
        <ul>
          <li v-for="(tema, indice) in asignatura.temas" :key="tema.id" class="tema-fila">
            <template v-if="editandoTema !== tema.id">
              <div class="tema-linea">
                <span>{{ tema.titulo }}</span>
                <div class="botones">
                  <button class="accion" :disabled="indice === 0" @click="moverTema(tema.id, 'subir')">↑</button>
                  <button
                    class="accion"
                    :disabled="indice === asignatura.temas.length - 1"
                    @click="moverTema(tema.id, 'bajar')"
                  >
                    ↓
                  </button>
                  <button class="accion" @click="empezarEdicion(tema)">Editar</button>
                  <button class="borrar" @click="borrarTema(tema.id)">Borrar</button>
                </div>
              </div>
              <div class="materiales-admin">
                <span v-for="material in tema.materiales" :key="material.id" class="chip">
                  {{ material.tipo }} · {{ material.titulo }}
                  <button class="chip-borrar" title="Borrar material" @click="borrarMaterial(material.id)">
                    ×
                  </button>
                </span>
                <form class="nuevo-material" @submit.prevent="crearMaterial(tema.id)">
                  <select v-model="formMaterial(tema.id).tipo">
                    <option value="apuntes">Apuntes</option>
                    <option value="ejercicios">Ejercicios</option>
                    <option value="video">Vídeo</option>
                    <option value="enlace">Enlace</option>
                  </select>
                  <input v-model="formMaterial(tema.id).titulo" placeholder="Título del material" required />
                  <input v-model="formMaterial(tema.id).url" placeholder="URL" type="url" required />
                  <button type="submit" class="accion">Añadir material</button>
                </form>
              </div>
            </template>
            <form v-else class="edicion" @submit.prevent="guardarTema(tema.id)">
              <input v-model="formEdicion.titulo" placeholder="Título" required />
              <input v-model="formEdicion.descripcion" placeholder="Descripción (opcional)" />
              <div class="botones">
                <button type="submit" class="guardar">Guardar</button>
                <button type="button" class="accion" @click="editandoTema = null">Cancelar</button>
              </div>
            </form>
          </li>
        </ul>
        <form class="nuevo-tema" @submit.prevent="crearTema(asignatura.id)">
          <input v-model="nuevoTema[asignatura.id]!.titulo" placeholder="Título del tema nuevo" required />
          <input v-model="nuevoTema[asignatura.id]!.descripcion" placeholder="Descripción (opcional)" />
          <input v-model="nuevoTema[asignatura.id]!.material_url" placeholder="URL del material (opcional)" />
          <button type="submit">Añadir tema</button>
        </form>
      </div>

      <form class="nueva-asignatura" @submit.prevent="crearAsignatura">
        <input v-model="nuevaAsignatura" placeholder="Nombre de la asignatura nueva" required />
        <button type="submit">Añadir asignatura</button>
      </form>
    </div>
  </section>
</template>

<style scoped>
.admin {
  max-width: 820px;
  margin: 0 auto;
  padding: 60px 20px 80px;
}
.admin h1 {
  font-size: 2rem;
  text-align: center;
  margin-bottom: 32px;
}
.error {
  text-align: center;
  color: #c0392b;
  margin-bottom: 16px;
}
.panel {
  border: 1px solid var(--borde);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}
.panel h2 {
  font-size: 1.2rem;
  color: var(--marca);
  margin-bottom: 16px;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}
th,
td {
  text-align: left;
  padding: 8px;
  border-bottom: 1px solid var(--borde);
}
.acciones-fila {
  text-align: right;
}
.etiqueta {
  background: var(--marca);
  color: white;
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 4px;
  vertical-align: middle;
}
.niveles {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.niveles button {
  padding: 8px 16px;
  border: 1px solid var(--borde);
  background: var(--superficie);
  border-radius: 8px;
  cursor: pointer;
}
.niveles button.activo {
  background: var(--marca);
  border-color: var(--marca);
  color: white;
  font-weight: bold;
}
.asignatura {
  border: 1px solid var(--borde);
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
}
.cabecera {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.cabecera h3 {
  font-size: 1.05rem;
}
ul {
  list-style: none;
  margin: 12px 0;
}
li {
  padding: 10px 0;
  border-bottom: 1px solid var(--borde);
}
.tema-linea {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.materiales-admin {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding-left: 8px;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--fondo-suave);
  border: 1px solid var(--borde);
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 0.82rem;
  color: var(--texto-suave);
}
.chip-borrar {
  background: transparent;
  border: none;
  color: var(--texto-suave);
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  padding: 0;
}
.chip-borrar:hover {
  color: #c0392b;
}
.nuevo-material {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  align-items: center;
}
.nuevo-material select,
.nuevo-material input {
  padding: 5px 8px;
  border: 1px solid var(--borde);
  border-radius: 6px;
  font-size: 0.85rem;
}
.fila-nivel {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--borde);
}
.fila-nivel input {
  padding: 8px 10px;
  border: 1px solid var(--borde);
  border-radius: 8px;
}
.campo-nombre {
  width: 150px;
}
.campo-precio {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--texto-suave);
}
.campo-precio input {
  width: 90px;
}
.campo-descripcion {
  flex: 1;
  min-width: 200px;
}
.botones {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.accion,
.borrar {
  background: transparent;
  border: 1px solid var(--borde);
  color: var(--texto-suave);
  border-radius: 6px;
  padding: 4px 10px;
  cursor: pointer;
  font-size: 0.8rem;
}
.accion:hover:not(:disabled) {
  border-color: var(--marca);
  color: var(--marca);
}
.accion:disabled {
  opacity: 0.4;
  cursor: default;
}
.edicion {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  width: 100%;
}
.edicion input {
  flex: 1;
  min-width: 140px;
  padding: 6px 10px;
  border: 1px solid var(--borde);
  border-radius: 6px;
}
.guardar {
  background: var(--marca);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 4px 12px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: bold;
}
.borrar:hover {
  border-color: #c0392b;
  color: #c0392b;
}
.nuevo-tema,
.nueva-asignatura {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.nuevo-tema input,
.nueva-asignatura input {
  flex: 1;
  min-width: 160px;
  padding: 8px 10px;
  border: 1px solid var(--borde);
  border-radius: 8px;
}
.nuevo-tema button,
.nueva-asignatura button {
  background: var(--marca);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
}
</style>
