<script setup lang="ts">
// TODO: sustituir por los datos de contacto reales de la academia
const email = 'info@academiaartemis.com'
const telefono = '600 000 000'
const telefonoLink = telefono.replace(/ /g, '')
</script>

<template>
  <section class="contacto">
    <h1>Contacto</h1>
    <p class="intro">¿Tienes dudas o quieres apuntarte? Escríbenos y te respondemos lo antes posible.</p>

    <div class="canales">
      <div class="canal">
        <h2>Email</h2>
        <a :href="`mailto:${email}`">{{ email }}</a>
      </div>
      <div class="canal">
        <h2>Teléfono / WhatsApp</h2>
        <a :href="`tel:${telefonoLink}`">{{ telefono }}</a>
      </div>
      <div class="canal">
        <h2>Horario</h2>
        <p>Lunes a viernes, 9:00 - 20:00</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.contacto {
  text-align: center;
  padding: 60px 20px 80px;
}
.contacto h1 {
  font-size: 2rem;
  margin-bottom: 12px;
}
.intro {
  color: #555;
  max-width: 560px;
  margin: 0 auto;
}
.canales {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 24px;
  margin-top: 40px;
}
.canal {
  width: 240px;
  padding: 24px;
  border: 1px solid #eee;
  border-radius: 12px;
}
.canal h2 {
  font-size: 1.1rem;
  color: #f1502f;
  margin-bottom: 8px;
}
.canal a {
  color: #333;
  text-decoration: none;
  font-weight: bold;
}
.canal p {
  color: #555;
}
</style>
