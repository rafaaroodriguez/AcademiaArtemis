import os
from datetime import timedelta
from functools import wraps

import stripe
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate, stamp, upgrade
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash

# Carga Backend/.env si existe (ADMIN_EMAIL, JWT_SECRET_KEY, etc.)
load_dotenv()

app = Flask(__name__)

# Render entrega la URL como postgres:// pero SQLAlchemy exige postgresql://
_db_url = os.environ.get('DATABASE_URL', 'sqlite:///academia.db')
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
# En producción (Render) hay que definir JWT_SECRET_KEY como variable de entorno
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-solo-para-local')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

# El usuario con este email es administrador del panel
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', '').strip().lower()

# URL del frontend, usada en los enlaces de los emails
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173').rstrip('/')

# Clave secreta de Stripe (sk_test_... en pruebas). Sin ella, la suscripción
# se activa directamente sin pago (solo útil en desarrollo).
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
    print("[Config] Stripe: configurado — los planes se contratan por la pasarela de pago")
else:
    print("[Config] Stripe: NO configurado — los planes se activan directamente sin pago (solo desarrollo)")

# Secreto de firma del webhook de Stripe (whsec_...). En local lo da
# 'stripe listen'; en producción, el panel de Stripe al crear el endpoint.
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

CORS(app)
db = SQLAlchemy(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)

# Límite de intentos por IP en los endpoints sensibles (fuerza bruta).
# En memoria: suficiente con un solo proceso; en producción con varios
# workers convendría un almacenamiento compartido (Redis).
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://",
    enabled=os.environ.get('RATELIMIT_ENABLED', '1') != '0',
)


@app.errorhandler(429)
def limite_alcanzado(_error):
    return jsonify({"error": "Demasiados intentos. Espera un minuto y vuelve a intentarlo"}), 429


class Nivel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    precio = db.Column(db.Numeric(6, 2), nullable=False)
    descripcion = db.Column(db.Text, default='')
    orden = db.Column(db.Integer, nullable=False, default=0)
    creado_en = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    def a_dict(self):
        # Mantiene los nombres que el frontend ya consume (name/price/benefits)
        return {
            "id": self.id,
            "name": self.nombre,
            "price": float(self.precio),
            "benefits": self.descripcion,
        }


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # Nivel contratado; None = sin suscripción
    nivel_id = db.Column(db.Integer, db.ForeignKey('nivel.id'), nullable=True)
    es_admin = db.Column(db.Boolean, nullable=False, default=False)
    # Identificadores de Stripe para gestionar la suscripción recurrente
    stripe_customer_id = db.Column(db.String(120), nullable=True)
    stripe_subscription_id = db.Column(db.String(120), nullable=True)
    # True cuando el alumno canceló: mantiene acceso hasta fin del periodo pagado
    cancelacion_pendiente = db.Column(db.Boolean, nullable=False, default=False)

    def a_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "nivel_id": self.nivel_id,
            "es_admin": self.es_admin,
            "cancelacion_pendiente": self.cancelacion_pendiente,
        }


class Asignatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nivel_id = db.Column(db.Integer, db.ForeignKey('nivel.id'), nullable=False, index=True)
    nombre = db.Column(db.String(120), nullable=False)
    temas = db.relationship('Tema', backref='asignatura', order_by='Tema.orden',
                            cascade='all, delete-orphan')

    def a_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "temas": [tema.a_dict() for tema in self.temas],
        }


class Tema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('asignatura.id'), nullable=False, index=True)
    orden = db.Column(db.Integer, nullable=False, default=0)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, default='')
    materiales = db.relationship('Material', backref='tema', order_by='Material.orden',
                                 cascade='all, delete-orphan')

    def a_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "materiales": [material.a_dict() for material in self.materiales],
        }


class Material(db.Model):
    TIPOS = ('apuntes', 'ejercicios', 'video', 'enlace')

    id = db.Column(db.Integer, primary_key=True)
    tema_id = db.Column(db.Integer, db.ForeignKey('tema.id'), nullable=False, index=True)
    tipo = db.Column(db.String(20), nullable=False, default='enlace')
    titulo = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    orden = db.Column(db.Integer, nullable=False, default=0)
    creado_en = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    def a_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "titulo": self.titulo,
            "url": self.url,
        }


def cargar_contenido_de_ejemplo():
    """Contenido provisional para desarrollo. TODO: sustituir por el temario real."""
    ejemplo = {
        1: {  # ESO
            "Matemáticas": ["Números enteros y fracciones", "Ecuaciones de primer grado", "Geometría básica"],
            "Lengua": ["Morfología: las clases de palabras", "Sintaxis de la oración simple"],
        },
        2: {  # Bachillerato
            "Matemáticas": ["Límites y continuidad", "Derivadas", "Integrales"],
            "Física y Química": ["Cinemática", "Formulación inorgánica"],
        },
        3: {  # Universidad
            "Cálculo": ["Cálculo diferencial en varias variables", "Series numéricas"],
            "Álgebra lineal": ["Espacios vectoriales", "Diagonalización"],
        },
    }
    for nivel_id, asignaturas in ejemplo.items():
        for nombre, temas in asignaturas.items():
            asignatura = Asignatura(nivel_id=nivel_id, nombre=nombre)
            db.session.add(asignatura)
            db.session.flush()
            for orden, titulo in enumerate(temas, start=1):
                db.session.add(Tema(
                    asignatura_id=asignatura.id,
                    orden=orden,
                    titulo=titulo,
                    descripcion=f"Apuntes y ejercicios de: {titulo}.",
                ))
    db.session.commit()


def cargar_niveles_iniciales():
    niveles = [
        ("ESO", 4.99, "Acceso a contenido sobre cursos de ESO"),
        ("Bachillerato", 9.99, "Acceso a contenido sobre cursos de Bachillerato"),
        ("Universidad", 14.99, "Acceso a contenido sobre cursos de Universidad"),
    ]
    for orden, (nombre, precio, descripcion) in enumerate(niveles, start=1):
        db.session.add(Nivel(nombre=nombre, precio=precio, descripcion=descripcion, orden=orden))
    db.session.commit()


def preparar_base_de_datos():
    with app.app_context():
        inspector = db.inspect(db.engine)
        if not inspector.has_table('usuario'):
            # Base vacía: se crea con el esquema actual y se marca como al día
            db.create_all()
            stamp()
        elif not inspector.has_table('alembic_version'):
            raise SystemExit(
                "Esta base de datos es anterior al sistema de migraciones y no se puede "
                "actualizar automáticamente. Al ser datos de desarrollo, borra el archivo "
                "Backend/instance/academia.db (o crea una base nueva en Postgres) y vuelve a arrancar."
            )
        else:
            # Base existente: aplica las migraciones pendientes
            upgrade()

        if Nivel.query.count() == 0:
            cargar_niveles_iniciales()
        if Asignatura.query.count() == 0:
            cargar_contenido_de_ejemplo()
        # Si el email de ADMIN_EMAIL ya tiene cuenta, se le hace administrador
        if ADMIN_EMAIL:
            admin = Usuario.query.filter_by(email=ADMIN_EMAIL).first()
            if admin and not admin.es_admin:
                admin.es_admin = True
                db.session.commit()


# SALTAR_BOOTSTRAP_DB=1 lo usan los comandos 'flask db ...' para generar migraciones
if os.environ.get('SALTAR_BOOTSTRAP_DB') != '1':
    preparar_base_de_datos()


def usuario_del_token():
    """Usuario de la sesión actual, o None si la cuenta ya no existe."""
    return db.session.get(Usuario, int(get_jwt_identity()))


def requiere_admin(funcion):
    """Como jwt_required, pero además el usuario debe ser administrador."""
    @wraps(funcion)
    @jwt_required()
    def envoltura(*args, **kwargs):
        usuario = db.session.get(Usuario, int(get_jwt_identity()))
        if not usuario or not usuario.es_admin:
            return jsonify({"error": "Esta zona es solo para administradores"}), 403
        return funcion(*args, **kwargs)
    return envoltura


@app.route('/api/datos_academia', methods=['GET'])
def obtener_perfil():
    niveles = Nivel.query.order_by(Nivel.orden, Nivel.id).all()
    return jsonify({
        "nombre": "Academia Artemis",
        "biografia": "academia 100% online con contenido para todos los niveles: ESO, Bachillerato y Universidad!",
        "niveles": [nivel.a_dict() for nivel in niveles],
    })


@app.route('/api/registro', methods=['POST'])
@limiter.limit("10 per minute")
def registro():
    datos = request.get_json(silent=True) or {}
    nombre = (datos.get('nombre') or '').strip()
    email = (datos.get('email') or '').strip().lower()
    password = datos.get('password') or ''

    if not nombre or not email:
        return jsonify({"error": "El nombre y el email son obligatorios"}), 400
    if len(password) < 6:
        return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400
    if Usuario.query.filter_by(email=email).first():
        return jsonify({"error": "Ya existe una cuenta con ese email"}), 409

    usuario = Usuario(
        nombre=nombre,
        email=email,
        password_hash=generate_password_hash(password),
        es_admin=(email == ADMIN_EMAIL),
    )
    db.session.add(usuario)
    db.session.commit()

    token = create_access_token(identity=str(usuario.id))
    return jsonify({"token": token, "usuario": usuario.a_dict()}), 201


@app.route('/api/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    datos = request.get_json(silent=True) or {}
    email = (datos.get('email') or '').strip().lower()
    password = datos.get('password') or ''

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario or not check_password_hash(usuario.password_hash, password):
        return jsonify({"error": "Email o contraseña incorrectos"}), 401

    token = create_access_token(identity=str(usuario.id))
    return jsonify({"token": token, "usuario": usuario.a_dict()})


@app.route('/api/suscripcion/checkout', methods=['POST'])
@jwt_required()
def crear_checkout():
    datos = request.get_json(silent=True) or {}
    nivel_id = datos.get('nivel_id')
    nivel = db.session.get(Nivel, nivel_id) if isinstance(nivel_id, int) else None
    if not nivel:
        return jsonify({"error": "Ese nivel no existe"}), 404

    usuario = usuario_del_token()
    if not usuario:
        return jsonify({"error": "Tu cuenta ya no existe. Regístrate de nuevo"}), 401

    if not STRIPE_SECRET_KEY:
        # Sin Stripe configurado (desarrollo): activación directa sin pago
        usuario.nivel_id = nivel_id
        db.session.commit()
        return jsonify({"usuario": usuario.a_dict()})

    try:
        sesion = stripe.checkout.Session.create(
            mode='subscription',
            customer_email=usuario.email,
            line_items=[{
                'quantity': 1,
                'price_data': {
                    'currency': 'eur',
                    'unit_amount': int(round(float(nivel.precio) * 100)),
                    'recurring': {'interval': 'month'},
                    'product_data': {'name': f"Plan {nivel.nombre} · Academia Artemis"},
                },
            }],
            metadata={'usuario_id': str(usuario.id), 'nivel_id': str(nivel_id)},
            success_url=f"{FRONTEND_URL}/pago/exito?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/cursos",
        )
    except stripe.StripeError as error:
        app.logger.error(f"Error de Stripe al crear el checkout: {error}")
        return jsonify({"error": "No se pudo iniciar el pago. Inténtalo de nuevo en unos minutos"}), 502
    return jsonify({"url": sesion.url})


@app.route('/api/suscripcion/confirmar', methods=['POST'])
@jwt_required()
def confirmar_checkout():
    """Tras volver de Stripe, comprobamos CON STRIPE que el pago está hecho
    antes de activar el plan. El navegador nunca decide si se activa."""
    if not STRIPE_SECRET_KEY:
        return jsonify({"error": "Stripe no está configurado"}), 503

    session_id = (request.get_json(silent=True) or {}).get('session_id') or ''
    try:
        sesion = stripe.checkout.Session.retrieve(session_id)

        usuario = usuario_del_token()
        if not usuario:
            return jsonify({"error": "Tu cuenta ya no existe. Regístrate de nuevo"}), 401
        # sesion.metadata es un StripeObject, no un dict: solo el acceso con
        # corchetes funciona en todas las versiones de la librería
        try:
            usuario_id_pago = str(sesion.metadata['usuario_id'])
            nivel_id_pago = int(sesion.metadata['nivel_id'])
        except (KeyError, TypeError):
            return jsonify({"error": "El pago no lleva los datos esperados"}), 400
        if usuario_id_pago != str(usuario.id):
            return jsonify({"error": "Este pago no corresponde a tu cuenta"}), 403
        if sesion.payment_status != 'paid':
            return jsonify({"error": "El pago no se ha completado"}), 400

        usuario.nivel_id = nivel_id_pago
        usuario.stripe_customer_id = valor_stripe(sesion, 'customer')
        usuario.stripe_subscription_id = valor_stripe(sesion, 'subscription')
        usuario.cancelacion_pendiente = False
        db.session.commit()
        return jsonify({"usuario": usuario.a_dict()})
    except Exception as error:
        # Cualquier fallo queda en el log y responde JSON limpio (con CORS),
        # en vez del 500 en HTML del depurador de Flask
        app.logger.exception(f"Error verificando el pago de la sesión {session_id}: {error}")
        return jsonify({"error": "No se pudo verificar el pago. Revisa la consola del backend"}), 500


@app.route('/api/niveles/<int:nivel_id>/contenido', methods=['GET'])
@jwt_required()
def contenido_nivel(nivel_id):
    nivel = db.session.get(Nivel, nivel_id)
    if not nivel:
        return jsonify({"error": "Ese nivel no existe"}), 404

    usuario = usuario_del_token()
    if not usuario:
        return jsonify({"error": "Tu cuenta ya no existe. Regístrate de nuevo"}), 401
    if not usuario.es_admin and usuario.nivel_id != nivel_id:
        return jsonify({"error": "Necesitas una suscripción a este nivel para ver su contenido"}), 403

    asignaturas = Asignatura.query.filter_by(nivel_id=nivel_id).order_by(Asignatura.nombre).all()
    return jsonify({
        "nivel": nivel.a_dict(),
        "asignaturas": [a.a_dict() for a in asignaturas],
    })


def valor_stripe(objeto, clave, defecto=None):
    """Lee una clave de un objeto de Stripe. Los StripeObject no siempre
    exponen .get(), así que solo es seguro el acceso con corchetes."""
    try:
        return objeto[clave]
    except (KeyError, TypeError):
        return defecto


def serializador_recuperacion():
    return URLSafeTimedSerializer(app.config['JWT_SECRET_KEY'], salt='recuperar-password')


def enviar_email_recuperacion(destinatario, enlace):
    host = os.environ.get('SMTP_HOST')
    if not host:
        # Sin servidor de correo configurado (desarrollo): el enlace sale por consola
        print(f"[DEV] Enlace de recuperación para {destinatario}: {enlace}")
        return
    import smtplib
    from email.message import EmailMessage

    mensaje = EmailMessage()
    mensaje['Subject'] = 'Recupera tu contraseña · Academia Artemis'
    mensaje['From'] = os.environ.get('MAIL_FROM', 'no-reply@academiaartemis.com')
    mensaje['To'] = destinatario
    mensaje.set_content(
        "Hola,\n\n"
        "Para restablecer tu contraseña de Academia Artemis entra en:\n"
        f"{enlace}\n\n"
        "El enlace caduca en 1 hora. Si no has pedido este cambio, ignora este mensaje."
    )
    with smtplib.SMTP(host, int(os.environ.get('SMTP_PORT', '587'))) as servidor:
        servidor.starttls()
        servidor.login(os.environ.get('SMTP_USER', ''), os.environ.get('SMTP_PASS', ''))
        servidor.send_message(mensaje)


@app.route('/api/recuperar', methods=['POST'])
@limiter.limit("5 per minute")
def recuperar():
    email = ((request.get_json(silent=True) or {}).get('email') or '').strip().lower()
    usuario = Usuario.query.filter_by(email=email).first()
    if usuario:
        token = serializador_recuperacion().dumps(usuario.id)
        enviar_email_recuperacion(email, f"{FRONTEND_URL}/restablecer?token={token}")
    # La respuesta es la misma exista o no la cuenta, para no revelar qué emails están registrados
    return jsonify({"mensaje": "Si existe una cuenta con ese email, te hemos enviado un enlace para restablecer la contraseña."})


@app.route('/api/restablecer', methods=['POST'])
def restablecer():
    datos = request.get_json(silent=True) or {}
    token = datos.get('token') or ''
    password = datos.get('password') or ''
    if len(password) < 6:
        return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400
    try:
        usuario_id = serializador_recuperacion().loads(token, max_age=3600)
    except SignatureExpired:
        return jsonify({"error": "El enlace ha caducado. Pide uno nuevo desde 'He olvidado mi contraseña'"}), 400
    except BadSignature:
        return jsonify({"error": "El enlace no es válido"}), 400

    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        return jsonify({"error": "El enlace no es válido"}), 400
    usuario.password_hash = generate_password_hash(password)
    db.session.commit()
    return jsonify({"mensaje": "Contraseña actualizada. Ya puedes iniciar sesión."})


@app.route('/api/suscripcion/cancelar', methods=['POST'])
@jwt_required()
def cancelar_suscripcion():
    usuario = usuario_del_token()
    if not usuario:
        return jsonify({"error": "Tu cuenta ya no existe. Regístrate de nuevo"}), 401
    if not usuario.nivel_id:
        return jsonify({"error": "No tienes ninguna suscripción activa"}), 400

    if STRIPE_SECRET_KEY and usuario.stripe_subscription_id:
        # Cancelación al final del periodo: el alumno conserva el acceso que
        # ya ha pagado; cuando Stripe la cierre, el webhook quitará el plan
        try:
            stripe.Subscription.modify(usuario.stripe_subscription_id, cancel_at_period_end=True)
        except stripe.StripeError as error:
            app.logger.error(f"Error de Stripe al cancelar {usuario.stripe_subscription_id}: {error}")
            return jsonify({"error": "No se pudo cancelar la suscripción. Inténtalo de nuevo en unos minutos"}), 502
        usuario.cancelacion_pendiente = True
        db.session.commit()
        return jsonify({
            "usuario": usuario.a_dict(),
            "mensaje": "Suscripción cancelada. Mantienes el acceso hasta el final del periodo ya pagado.",
        })

    # Sin Stripe (desarrollo) o plan activado sin pago: cancelación inmediata
    usuario.nivel_id = None
    usuario.stripe_subscription_id = None
    usuario.cancelacion_pendiente = False
    db.session.commit()
    return jsonify({"usuario": usuario.a_dict(), "mensaje": "Suscripción cancelada."})


@app.route('/api/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """Stripe llama aquí cuando pasa algo con las suscripciones (pago completado,
    cancelación, impago...). La firma garantiza que la llamada es de Stripe."""
    if not STRIPE_WEBHOOK_SECRET:
        return jsonify({"error": "Webhook no configurado"}), 503
    try:
        evento = stripe.Webhook.construct_event(
            request.data,
            request.headers.get('Stripe-Signature', ''),
            STRIPE_WEBHOOK_SECRET,
        )
    except Exception:
        return jsonify({"error": "Firma no válida"}), 400

    tipo = evento['type']
    objeto = evento['data']['object']

    if tipo == 'checkout.session.completed':
        # Activación de respaldo: cubre el caso de que el alumno pague pero
        # cierre el navegador antes de volver a la web
        metadatos = valor_stripe(objeto, 'metadata') or {}
        usuario = db.session.get(Usuario, int(valor_stripe(metadatos, 'usuario_id') or 0))
        nivel_id = valor_stripe(metadatos, 'nivel_id')
        if usuario and nivel_id and valor_stripe(objeto, 'payment_status') == 'paid':
            usuario.nivel_id = int(nivel_id)
            usuario.stripe_customer_id = valor_stripe(objeto, 'customer')
            usuario.stripe_subscription_id = valor_stripe(objeto, 'subscription')
            usuario.cancelacion_pendiente = False
            db.session.commit()

    elif tipo == 'customer.subscription.deleted':
        # La suscripción terminó (canceló y venció el periodo, o impago agotado)
        usuario = Usuario.query.filter_by(stripe_subscription_id=valor_stripe(objeto, 'id')).first()
        if usuario:
            usuario.nivel_id = None
            usuario.stripe_subscription_id = None
            usuario.cancelacion_pendiente = False
            db.session.commit()

    elif tipo == 'customer.subscription.updated':
        usuario = Usuario.query.filter_by(stripe_subscription_id=valor_stripe(objeto, 'id')).first()
        if usuario:
            estado = valor_stripe(objeto, 'status')
            if estado in ('canceled', 'unpaid', 'incomplete_expired'):
                usuario.nivel_id = None
                usuario.stripe_subscription_id = None
                usuario.cancelacion_pendiente = False
            else:
                # Refleja si hay una cancelación programada (o si se reactivó)
                usuario.cancelacion_pendiente = bool(valor_stripe(objeto, 'cancel_at_period_end'))
            db.session.commit()

    elif tipo == 'invoice.payment_failed':
        app.logger.warning(f"Cobro mensual fallido: {valor_stripe(objeto, 'customer')} "
                           f"(Stripe reintentará; si agota los reintentos llegará subscription.deleted)")

    return jsonify({"ok": True})


@app.route('/api/perfil', methods=['GET'])
@jwt_required()
def perfil():
    usuario = db.session.get(Usuario, int(get_jwt_identity()))
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify({"usuario": usuario.a_dict()})


# ------------------------- Zona de administración -------------------------

@app.route('/api/admin/alumnos', methods=['GET'])
@requiere_admin
def admin_alumnos():
    alumnos = Usuario.query.order_by(Usuario.id).all()
    return jsonify({"alumnos": [u.a_dict() for u in alumnos]})


@app.route('/api/admin/alumnos/<int:alumno_id>', methods=['DELETE'])
@requiere_admin
def admin_borrar_alumno(alumno_id):
    alumno = db.session.get(Usuario, alumno_id)
    if not alumno:
        return jsonify({"error": "Ese alumno no existe"}), 404
    if alumno.es_admin:
        return jsonify({"error": "No se puede borrar una cuenta de administrador"}), 400
    db.session.delete(alumno)
    db.session.commit()
    return jsonify({"ok": True})


@app.route('/api/admin/niveles/<int:nivel_id>', methods=['PUT'])
@requiere_admin
def admin_editar_nivel(nivel_id):
    nivel = db.session.get(Nivel, nivel_id)
    if not nivel:
        return jsonify({"error": "Ese nivel no existe"}), 404
    datos = request.get_json(silent=True) or {}

    nombre = (datos.get('nombre') or '').strip()
    if not nombre:
        return jsonify({"error": "El nombre no puede estar vacío"}), 400
    try:
        precio = round(float(datos.get('precio')), 2)
    except (TypeError, ValueError):
        return jsonify({"error": "El precio debe ser un número"}), 400
    if precio <= 0:
        return jsonify({"error": "El precio debe ser mayor que cero"}), 400

    nivel.nombre = nombre
    nivel.precio = precio
    nivel.descripcion = (datos.get('descripcion') or '').strip()
    db.session.commit()
    return jsonify({"nivel": nivel.a_dict()})


@app.route('/api/admin/asignaturas', methods=['POST'])
@requiere_admin
def admin_crear_asignatura():
    datos = request.get_json(silent=True) or {}
    nombre = (datos.get('nombre') or '').strip()
    nivel_id = datos.get('nivel_id')
    if not nombre or not (isinstance(nivel_id, int) and db.session.get(Nivel, nivel_id)):
        return jsonify({"error": "Hacen falta un nombre y un nivel válido"}), 400
    asignatura = Asignatura(nivel_id=nivel_id, nombre=nombre)
    db.session.add(asignatura)
    db.session.commit()
    return jsonify({"asignatura": asignatura.a_dict()}), 201


@app.route('/api/admin/asignaturas/<int:asignatura_id>', methods=['PUT'])
@requiere_admin
def admin_renombrar_asignatura(asignatura_id):
    asignatura = db.session.get(Asignatura, asignatura_id)
    if not asignatura:
        return jsonify({"error": "Esa asignatura no existe"}), 404
    nombre = ((request.get_json(silent=True) or {}).get('nombre') or '').strip()
    if not nombre:
        return jsonify({"error": "El nombre no puede estar vacío"}), 400
    asignatura.nombre = nombre
    db.session.commit()
    return jsonify({"asignatura": asignatura.a_dict()})


@app.route('/api/admin/asignaturas/<int:asignatura_id>', methods=['DELETE'])
@requiere_admin
def admin_borrar_asignatura(asignatura_id):
    asignatura = db.session.get(Asignatura, asignatura_id)
    if not asignatura:
        return jsonify({"error": "Esa asignatura no existe"}), 404
    # El cascade de las relaciones arrastra sus temas y materiales
    db.session.delete(asignatura)
    db.session.commit()
    return jsonify({"ok": True})


@app.route('/api/admin/asignaturas/<int:asignatura_id>/temas', methods=['POST'])
@requiere_admin
def admin_crear_tema(asignatura_id):
    asignatura = db.session.get(Asignatura, asignatura_id)
    if not asignatura:
        return jsonify({"error": "Esa asignatura no existe"}), 404
    datos = request.get_json(silent=True) or {}
    titulo = (datos.get('titulo') or '').strip()
    if not titulo:
        return jsonify({"error": "El título es obligatorio"}), 400
    ultimo_orden = max((t.orden for t in asignatura.temas), default=0)
    tema = Tema(
        asignatura_id=asignatura_id,
        orden=ultimo_orden + 1,
        titulo=titulo,
        descripcion=(datos.get('descripcion') or '').strip(),
    )
    db.session.add(tema)
    db.session.commit()
    return jsonify({"tema": tema.a_dict()}), 201


@app.route('/api/admin/temas/<int:tema_id>', methods=['PUT'])
@requiere_admin
def admin_editar_tema(tema_id):
    tema = db.session.get(Tema, tema_id)
    if not tema:
        return jsonify({"error": "Ese tema no existe"}), 404
    datos = request.get_json(silent=True) or {}
    titulo = (datos.get('titulo') or '').strip()
    if not titulo:
        return jsonify({"error": "El título es obligatorio"}), 400
    tema.titulo = titulo
    tema.descripcion = (datos.get('descripcion') or '').strip()
    db.session.commit()
    return jsonify({"tema": tema.a_dict()})


@app.route('/api/admin/temas/<int:tema_id>/mover', methods=['POST'])
@requiere_admin
def admin_mover_tema(tema_id):
    tema = db.session.get(Tema, tema_id)
    if not tema:
        return jsonify({"error": "Ese tema no existe"}), 404
    direccion = (request.get_json(silent=True) or {}).get('direccion')
    if direccion not in ('subir', 'bajar'):
        return jsonify({"error": "La dirección debe ser 'subir' o 'bajar'"}), 400

    hermanos = sorted(tema.asignatura.temas, key=lambda t: t.orden)
    indice = hermanos.index(tema)
    vecino = indice - 1 if direccion == 'subir' else indice + 1
    if vecino < 0 or vecino >= len(hermanos):
        return jsonify({"error": "El tema ya está en el extremo"}), 400

    tema.orden, hermanos[vecino].orden = hermanos[vecino].orden, tema.orden
    db.session.commit()
    return jsonify({"ok": True})


@app.route('/api/admin/temas/<int:tema_id>/materiales', methods=['POST'])
@requiere_admin
def admin_crear_material(tema_id):
    tema = db.session.get(Tema, tema_id)
    if not tema:
        return jsonify({"error": "Ese tema no existe"}), 404
    datos = request.get_json(silent=True) or {}
    titulo = (datos.get('titulo') or '').strip()
    url = (datos.get('url') or '').strip()
    tipo = (datos.get('tipo') or 'enlace').strip()
    if not titulo or not url:
        return jsonify({"error": "El título y la URL son obligatorios"}), 400
    if tipo not in Material.TIPOS:
        return jsonify({"error": f"El tipo debe ser uno de: {', '.join(Material.TIPOS)}"}), 400

    ultimo_orden = max((m.orden for m in tema.materiales), default=0)
    material = Material(tema_id=tema_id, tipo=tipo, titulo=titulo, url=url, orden=ultimo_orden + 1)
    db.session.add(material)
    db.session.commit()
    return jsonify({"material": material.a_dict()}), 201


@app.route('/api/admin/materiales/<int:material_id>', methods=['DELETE'])
@requiere_admin
def admin_borrar_material(material_id):
    material = db.session.get(Material, material_id)
    if not material:
        return jsonify({"error": "Ese material no existe"}), 404
    db.session.delete(material)
    db.session.commit()
    return jsonify({"ok": True})


@app.route('/api/admin/temas/<int:tema_id>', methods=['DELETE'])
@requiere_admin
def admin_borrar_tema(tema_id):
    tema = db.session.get(Tema, tema_id)
    if not tema:
        return jsonify({"error": "Ese tema no existe"}), 404
    db.session.delete(tema)
    db.session.commit()
    return jsonify({"ok": True})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
