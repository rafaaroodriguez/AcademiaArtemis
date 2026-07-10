import os
from datetime import timedelta
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash

# Carga Backend/.env si existe (ADMIN_EMAIL, JWT_SECRET_KEY, etc.)
load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///academia.db')
# En producción (Render) hay que definir JWT_SECRET_KEY como variable de entorno
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-solo-para-local')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

# El usuario con este email es administrador del panel
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', '').strip().lower()

# URL del frontend, usada en los enlaces de los emails
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173').rstrip('/')

CORS(app)
db = SQLAlchemy(app)
jwt = JWTManager(app)


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # Nivel contratado (1=ESO, 2=Bachillerato, 3=Universidad); None = sin suscripción
    nivel_id = db.Column(db.Integer, nullable=True)
    es_admin = db.Column(db.Boolean, nullable=False, default=False)

    def a_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "nivel_id": self.nivel_id,
            "es_admin": self.es_admin,
        }


class Asignatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 1 = ESO, 2 = Bachillerato, 3 = Universidad (ids de datos_academia["niveles"])
    nivel_id = db.Column(db.Integer, nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    temas = db.relationship('Tema', backref='asignatura', order_by='Tema.orden')

    def a_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "temas": [tema.a_dict() for tema in self.temas],
        }


class Tema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('asignatura.id'), nullable=False)
    orden = db.Column(db.Integer, nullable=False, default=0)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, default='')
    # Enlace al material (PDF, vídeo...); de momento puede quedar vacío
    material_url = db.Column(db.String(500), default='')

    def a_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "material_url": self.material_url,
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


with app.app_context():
    db.create_all()
    # Mini-migraciones: añaden columnas nuevas a bases ya existentes
    columnas = [c["name"] for c in db.inspect(db.engine).get_columns("usuario")]
    with db.engine.connect() as conexion:
        if "nivel_id" not in columnas:
            conexion.execute(db.text("ALTER TABLE usuario ADD COLUMN nivel_id INTEGER"))
        if "es_admin" not in columnas:
            conexion.execute(db.text("ALTER TABLE usuario ADD COLUMN es_admin BOOLEAN NOT NULL DEFAULT 0"))
        conexion.commit()
    if Asignatura.query.count() == 0:
        cargar_contenido_de_ejemplo()
    # Si el email de ADMIN_EMAIL ya tiene cuenta, se le hace administrador
    if ADMIN_EMAIL:
        admin = Usuario.query.filter_by(email=ADMIN_EMAIL).first()
        if admin and not admin.es_admin:
            admin.es_admin = True
            db.session.commit()


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


datos_academia = {
    "nombre": "Academia Artemis",
    "biografia": "academia 100% online con contenido para todos los niveles: ESO, Bachillerato y Universidad!",
    "niveles":
        [
            {"id": 1, "name": "ESO", "price": 4.99, "benefits": "Acceso a contenido sobre cursos de ESO"},
            {"id": 2, "name": "Bachillerato", "price": 9.99, "benefits": "Acceso a contenido sobre cursos de Bachillerato"},
            {"id": 3, "name": "Universidad", "price": 14.99, "benefits": "Acceso a contenido sobre cursos de Universidad"}
        ],
}


@app.route('/api/datos_academia', methods=['GET'])
def obtener_perfil():
    return jsonify(datos_academia)


@app.route('/api/registro', methods=['POST'])
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
def login():
    datos = request.get_json(silent=True) or {}
    email = (datos.get('email') or '').strip().lower()
    password = datos.get('password') or ''

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario or not check_password_hash(usuario.password_hash, password):
        return jsonify({"error": "Email o contraseña incorrectos"}), 401

    token = create_access_token(identity=str(usuario.id))
    return jsonify({"token": token, "usuario": usuario.a_dict()})


@app.route('/api/suscripcion', methods=['POST'])
@jwt_required()
def elegir_suscripcion():
    # TODO (paso 4): aquí irá el cobro con Stripe antes de activar el plan
    datos = request.get_json(silent=True) or {}
    nivel_id = datos.get('nivel_id')
    if not any(n["id"] == nivel_id for n in datos_academia["niveles"]):
        return jsonify({"error": "Ese nivel no existe"}), 404

    usuario = db.session.get(Usuario, int(get_jwt_identity()))
    usuario.nivel_id = nivel_id
    db.session.commit()
    return jsonify({"usuario": usuario.a_dict()})


@app.route('/api/niveles/<int:nivel_id>/contenido', methods=['GET'])
@jwt_required()
def contenido_nivel(nivel_id):
    nivel = next((n for n in datos_academia["niveles"] if n["id"] == nivel_id), None)
    if not nivel:
        return jsonify({"error": "Ese nivel no existe"}), 404

    usuario = db.session.get(Usuario, int(get_jwt_identity()))
    if not usuario.es_admin and usuario.nivel_id != nivel_id:
        return jsonify({"error": "Necesitas una suscripción a este nivel para ver su contenido"}), 403

    asignaturas = Asignatura.query.filter_by(nivel_id=nivel_id).order_by(Asignatura.nombre).all()
    return jsonify({
        "nivel": nivel,
        "asignaturas": [a.a_dict() for a in asignaturas],
    })


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


@app.route('/api/admin/asignaturas', methods=['POST'])
@requiere_admin
def admin_crear_asignatura():
    datos = request.get_json(silent=True) or {}
    nombre = (datos.get('nombre') or '').strip()
    nivel_id = datos.get('nivel_id')
    if not nombre or not any(n["id"] == nivel_id for n in datos_academia["niveles"]):
        return jsonify({"error": "Hacen falta un nombre y un nivel válido"}), 400
    asignatura = Asignatura(nivel_id=nivel_id, nombre=nombre)
    db.session.add(asignatura)
    db.session.commit()
    return jsonify({"asignatura": asignatura.a_dict()}), 201


@app.route('/api/admin/asignaturas/<int:asignatura_id>', methods=['DELETE'])
@requiere_admin
def admin_borrar_asignatura(asignatura_id):
    asignatura = db.session.get(Asignatura, asignatura_id)
    if not asignatura:
        return jsonify({"error": "Esa asignatura no existe"}), 404
    for tema in asignatura.temas:
        db.session.delete(tema)
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
        material_url=(datos.get('material_url') or '').strip(),
    )
    db.session.add(tema)
    db.session.commit()
    return jsonify({"tema": tema.a_dict()}), 201


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
