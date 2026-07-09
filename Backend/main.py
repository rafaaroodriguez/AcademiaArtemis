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

    def a_dict(self):
        return {"id": self.id, "nombre": self.nombre, "email": self.email}


with app.app_context():
    db.create_all()


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


@app.route('/api/perfil', methods=['GET'])
@jwt_required()
def perfil():
    usuario = db.session.get(Usuario, int(get_jwt_identity()))
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify({"usuario": usuario.a_dict()})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
