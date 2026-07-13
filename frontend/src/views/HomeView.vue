<script setup lang="ts">
import { useAcademyStore } from '../stores/useAcademy'
import { useAuthStore } from '../stores/useAuth'

const academy = useAcademyStore()
const auth = useAuthStore()
</script>

<template>
  <section class="hero">
    <p class="insignia">✦ Academia 100% online</p>
    <h1>
      Aprende a tu ritmo,<br />
      aprueba <span class="acento">con nota</span>
    </h1>
    <p class="tagline">
      Contenido claro y directo para ESO, Bachillerato y Universidad, preparado por profesores y
      disponible cuando tú lo estés.
    </p>
    <div class="hero-actions">
      <RouterLink to="/cursos" class="btn btn-primary">Ver cursos</RouterLink>
      <RouterLink v-if="!auth.estaLogueado" to="/registro" class="btn btn-secondary">
        Crear cuenta gratis
      </RouterLink>
      <RouterLink v-else to="/cuenta" class="btn btn-secondary">Mi cuenta</RouterLink>
    </div>
    <dl class="cifras">
      <div>
        <dt>3</dt>
        <dd>niveles educativos</dd>
      </div>
      <div>
        <dt>100%</dt>
        <dd>online, sin horarios</dd>
      </div>
      <div>
        <dt>{{ academy.tiers[0]?.price ?? 4.99 }}€</dt>
        <dd>al mes, sin permanencia</dd>
      </div>
    </dl>
  </section>

  <section class="bloque">
    <h2>Todo lo que necesitas para aprobar</h2>
    <div class="features">
      <div class="feature">
        <span class="icono" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
        </span>
        <h3>Temario organizado</h3>
        <p>Cada nivel, ordenado por asignaturas y temas. Sin perderte buscando qué estudiar.</p>
      </div>
      <div class="feature">
        <span class="icono" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
        </span>
        <h3>Estudia donde quieras</h3>
        <p>El contenido está siempre disponible: en casa, en la biblioteca o desde el móvil.</p>
      </div>
      <div class="feature">
        <span class="icono" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        </span>
        <h3>Precio de estudiante</h3>
        <p>Planes mensuales desde {{ academy.tiers[0]?.price ?? 4.99 }}€ y sin permanencia: entra y sal cuando quieras.</p>
      </div>
    </div>
  </section>

  <section class="bloque bloque-suave">
    <h2>Cómo funciona</h2>
    <ol class="pasos">
      <li>
        <span class="numero">1</span>
        <h3>Crea tu cuenta</h3>
        <p>Regístrate gratis en menos de un minuto.</p>
      </li>
      <li>
        <span class="numero">2</span>
        <h3>Elige tu nivel</h3>
        <p>ESO, Bachillerato o Universidad: un plan para cada etapa.</p>
      </li>
      <li>
        <span class="numero">3</span>
        <h3>Empieza a estudiar</h3>
        <p>Acceso inmediato a todo el contenido de tu nivel.</p>
      </li>
    </ol>
  </section>

  <section class="cta-final">
    <h2>¿Empezamos?</h2>
    <p>Únete hoy y prepara el curso con ventaja.</p>
    <RouterLink to="/cursos" class="btn btn-claro">Ver planes y precios</RouterLink>
  </section>
</template>

<style scoped>
.hero {
  position: relative;
  text-align: center;
  padding: 96px 20px 72px;
  background:
    radial-gradient(600px 300px at 15% 0%, rgba(241, 80, 47, 0.08), transparent),
    radial-gradient(600px 300px at 85% 10%, rgba(241, 80, 47, 0.06), transparent);
}
.insignia {
  display: inline-block;
  background: var(--marca-suave);
  color: var(--marca-oscuro);
  font-weight: 600;
  font-size: 0.85rem;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid rgba(241, 80, 47, 0.25);
  margin-bottom: 24px;
}
.hero h1 {
  font-size: clamp(2.2rem, 6vw, 3.6rem);
  font-weight: 800;
  margin-bottom: 20px;
}
.acento {
  color: var(--marca);
}
.tagline {
  font-size: 1.15rem;
  color: var(--texto-suave);
  max-width: 560px;
  margin: 0 auto 36px;
  line-height: 1.6;
}
.hero-actions {
  display: flex;
  gap: 14px;
  justify-content: center;
  flex-wrap: wrap;
}
.btn {
  padding: 14px 30px;
  border-radius: 12px;
  text-decoration: none;
  font-weight: 700;
  font-size: 1rem;
}
.btn-primary {
  background: var(--marca);
  color: white;
}
.btn-secondary {
  border: 2px solid var(--borde);
  color: var(--tinta);
  background: var(--superficie);
}
.cifras {
  display: flex;
  justify-content: center;
  gap: clamp(24px, 6vw, 72px);
  margin-top: 56px;
  flex-wrap: wrap;
}
.cifras dt {
  font-size: 2rem;
  font-weight: 800;
  color: var(--marca);
}
.cifras dd {
  color: var(--texto-suave);
  font-size: 0.92rem;
}

.bloque {
  max-width: 1120px;
  margin: 0 auto;
  padding: 72px 24px;
  text-align: center;
}
.bloque h2 {
  font-size: clamp(1.6rem, 4vw, 2.2rem);
  font-weight: 800;
  margin-bottom: 40px;
}
.bloque-suave {
  max-width: none;
  background: var(--fondo-suave);
  border-top: 1px solid var(--borde);
  border-bottom: 1px solid var(--borde);
}
.features {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 24px;
}
.feature {
  width: 300px;
  text-align: left;
  padding: 28px;
  border: 1px solid var(--borde);
  border-radius: var(--radio);
  background: var(--superficie);
  box-shadow: var(--sombra);
}
.icono {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--marca-suave);
  color: var(--marca);
  margin-bottom: 16px;
}
.icono svg {
  width: 22px;
  height: 22px;
}
.feature h3 {
  font-size: 1.05rem;
  margin-bottom: 8px;
}
.feature p {
  color: var(--texto-suave);
  font-size: 0.95rem;
  line-height: 1.6;
}

.pasos {
  list-style: none;
  display: flex;
  justify-content: center;
  gap: 24px;
  flex-wrap: wrap;
  max-width: 1120px;
  margin: 0 auto;
}
.pasos li {
  width: 280px;
  text-align: center;
  padding: 12px;
}
.numero {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--marca);
  color: white;
  font-weight: 800;
  font-size: 1.1rem;
  margin-bottom: 14px;
  box-shadow: 0 4px 12px rgba(241, 80, 47, 0.3);
}
.pasos h3 {
  font-size: 1.05rem;
  margin-bottom: 6px;
}
.pasos p {
  color: var(--texto-suave);
  font-size: 0.95rem;
}

.cta-final {
  text-align: center;
  padding: 72px 24px;
  background: linear-gradient(135deg, var(--marca), var(--marca-oscuro));
}
.cta-final h2 {
  color: white;
  font-size: clamp(1.6rem, 4vw, 2.2rem);
  margin-bottom: 10px;
}
.cta-final p {
  color: rgba(255, 255, 255, 0.85);
  margin-bottom: 28px;
  font-size: 1.05rem;
}
.btn-claro {
  display: inline-block;
  /* Siempre blanco: va sobre el degradado naranja en ambos temas */
  background: white;
  color: var(--marca-oscuro);
}
</style>
