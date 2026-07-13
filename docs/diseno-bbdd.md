# Diseño de la base de datos · Academia Artemis

Propuesta de evolución del esquema, pensada para implementarse por fases.
Estado actual: `usuario`, `asignatura`, `tema` en SQLite, con migraciones a
mano en el arranque de `main.py` y los niveles/precios hardcodeados en Python.

## Fase 0 — Herramienta de migraciones (hacer PRIMERO)

Sustituir las mini-migraciones artesanales por **Flask-Migrate (Alembic)**:

```
pip install flask-migrate
flask db init        # una vez
flask db migrate -m "descripcion"   # genera la migración al cambiar modelos
flask db upgrade     # la aplica
```

Sin esto, cada cambio de esquema con datos reales es una operación a corazón
abierto. Con esto, es un comando reversible.

## Fase 1 — Tabla `nivel`

Saca los niveles del diccionario `datos_academia` de `main.py`.

| campo       | tipo          | notas                          |
| ----------- | ------------- | ------------------------------ |
| id          | int PK        |                                |
| nombre      | varchar(80)   | "ESO", "Bachillerato"...       |
| precio      | numeric(6,2)  | editable desde el panel        |
| descripcion | text          | el texto de beneficios         |
| orden       | int           | orden de aparición             |
| creado_en   | datetime      |                                |

- `asignatura.nivel_id` y `usuario.nivel_id` pasan a ser FK reales.
- El endpoint `/api/datos_academia` lee de aquí.
- El panel de admin gana un editor de niveles/precios.

## Fase 2 — Tabla `material` (varios materiales por tema)

Sustituye el campo único `tema.material_url`.

| campo     | tipo         | notas                                   |
| --------- | ------------ | --------------------------------------- |
| id        | int PK       |                                         |
| tema_id   | FK tema      | índice                                  |
| tipo      | varchar(20)  | 'apuntes' \| 'ejercicios' \| 'video' \| 'enlace' |
| titulo    | varchar(200) |                                         |
| url       | varchar(500) |                                         |
| orden     | int          |                                         |
| creado_en | datetime     |                                         |

- Migración de datos: cada `material_url` existente se convierte en un
  material tipo 'enlace'.
- El panel de admin gestiona materiales dentro de cada tema.

## Fase 3 — Tabla `progreso` (opcional, muy vistosa)

El alumno marca temas completados y ve su avance por asignatura.

| campo         | tipo       | notas                        |
| ------------- | ---------- | ---------------------------- |
| usuario_id    | FK usuario | PK compuesta con tema_id     |
| tema_id       | FK tema    |                              |
| completado_en | datetime   |                              |

## Fase 4 — Tabla `suscripcion` (historial; la más delicada)

Hoy la suscripción vive en campos de `usuario` (funciona, pero sin historial).

| campo                  | tipo         | notas                                   |
| ---------------------- | ------------ | --------------------------------------- |
| id                     | int PK       |                                         |
| usuario_id             | FK usuario   | índice                                  |
| nivel_id               | FK nivel     |                                         |
| estado                 | varchar(20)  | 'activa' \| 'cancelada' \| 'impago'     |
| stripe_subscription_id | varchar(120) |                                         |
| creado_en              | datetime     | fecha de alta                           |
| finalizada_en          | datetime     | null mientras esté activa               |

- Permite métricas (altas por mes, bajas, ingresos estimados).
- Toca `checkout`, `confirmar`, `cancelar` y el webhook: hacerla en una
  iteración propia, con calma y con los tests pasando.
- Mientras tanto puede convivir: los campos de `usuario` como "estado actual"
  y esta tabla como historial.

## Recordatorios transversales

- `creado_en` en toda tabla nueva. Cuesta cero hoy, vale oro mañana.
- Índices en todas las FK que se consultan (`asignatura.nivel_id`,
  `tema.asignatura_id`, `material.tema_id`, `suscripcion.usuario_id`).
- SQLite en desarrollo, **Postgres en producción** (Render lo da; el código ya
  lee `DATABASE_URL`). Probar las migraciones contra Postgres antes de lanzar.
- Los tests de `Backend/tests/` deben seguir pasando tras cada fase.
