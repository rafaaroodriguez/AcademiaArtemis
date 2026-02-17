from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

datos_academia = {
    "nombre": "Academia Artemis",
    "biografia": "academia 100% online con contenido para todos los niveles: ESO, Bachillerato y Universidad!",
    "niveles": 
        [
            {"id": 1, "name": "ESO", "price": 5, "benefits": "Acceso a contenido sobre cursos de ESO"},
            {"id": 2, "name": "Bachillerato", "price": 10, "benefits": "Acceso a contenido sobre cursos de Bachillerato"},
            {"id": 3, "name": "Universidad", "price": 15, "benefits": "Acceso a contenido sobre cursos de Universidad"}
        ],
}

@app.route('/api/datos_academia', methods=['GET'])
def obtener_perfil():
    return jsonify(datos_academia)

if __name__ == '__main__':
    app.run(debug=True, port=5000)