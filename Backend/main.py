import os
from datetime import timedelta

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///academia.db')
# En producción (Render) hay que definir JWT_SECRET_KEY como variable de entorno
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-solo-para-local')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

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

    def a_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "nivel_id": self.nivel_id,
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
    # Mini-migración: añade usuario.nivel_id a bases creadas antes de este cambio
    columnas = [c["name"] for c in db.inspect(db.engine).get_columns("usuario")]
    if "nivel_id" not in columnas:
        with db.engine.connect() as conexion:
            conexion.execute(db.text("ALTER TABLE usuario ADD COLUMN nivel_id INTEGER"))
            conexion.commit()
    if Asignatura.query.count() == 0:
        cargar_contenido_de_ejemplo()


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

    usuario = Usuario(nombre=nombre, email=email, password_hash=generate_password_hash(password))
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
    if usuario.nivel_id != nivel_id:
        return jsonify({"error": "Necesitas una suscripción a este nivel para ver su contenido"}), 403

    asignaturas = Asignatura.query.filter_by(nivel_id=nivel_id).order_by(Asignatura.nombre).all()
    return jsonify({
        "nivel": nivel,
        "asignaturas": [a.a_dict() for a in asignaturas],
    })


@app.route('/api/perfil', methods=['GET'])
@jwt_required()
def perfil():
    usuario = db.session.get(Usuario, int(get_jwt_identity()))
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify({"usuario": usuario.a_dict()})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
