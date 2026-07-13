import pytest

import main


@pytest.fixture()
def cliente():
    return main.app.test_client()


def registrar(cliente, email, nombre='Test', password='secreto1'):
    return cliente.post('/api/registro', json={'nombre': nombre, 'email': email, 'password': password})


def token_de(cliente, email, password='secreto1'):
    respuesta = cliente.post('/api/login', json={'email': email, 'password': password})
    return respuesta.get_json()['token']


def autorizado(token):
    return {'Authorization': f'Bearer {token}'}


def test_datos_academia_son_publicos(cliente):
    respuesta = cliente.get('/api/datos_academia')
    assert respuesta.status_code == 200
    assert len(respuesta.get_json()['niveles']) == 3


def test_registro_y_login(cliente):
    assert registrar(cliente, 'ana@test.com', nombre='Ana').status_code == 201
    respuesta = cliente.post('/api/login', json={'email': 'ana@test.com', 'password': 'secreto1'})
    assert respuesta.status_code == 200
    assert respuesta.get_json()['usuario']['nombre'] == 'Ana'


def test_registro_duplicado(cliente):
    registrar(cliente, 'repe@test.com')
    assert registrar(cliente, 'repe@test.com').status_code == 409


def test_password_demasiado_corta(cliente):
    assert registrar(cliente, 'corta@test.com', password='123').status_code == 400


def test_login_incorrecto(cliente):
    registrar(cliente, 'seguro@test.com')
    respuesta = cliente.post('/api/login', json={'email': 'seguro@test.com', 'password': 'mala'})
    assert respuesta.status_code == 401


def test_perfil_requiere_token(cliente):
    assert cliente.get('/api/perfil').status_code == 401


def test_contenido_requiere_suscripcion(cliente):
    registrar(cliente, 'sinplan@test.com')
    token = token_de(cliente, 'sinplan@test.com')
    assert cliente.get('/api/niveles/1/contenido', headers=autorizado(token)).status_code == 403


def test_checkout_en_desarrollo_activa_el_plan(cliente):
    registrar(cliente, 'alumno@test.com')
    token = token_de(cliente, 'alumno@test.com')
    respuesta = cliente.post('/api/suscripcion/checkout', json={'nivel_id': 2}, headers=autorizado(token))
    assert respuesta.status_code == 200
    assert respuesta.get_json()['usuario']['nivel_id'] == 2
    # Su nivel sí; los demás no
    assert cliente.get('/api/niveles/2/contenido', headers=autorizado(token)).status_code == 200
    assert cliente.get('/api/niveles/1/contenido', headers=autorizado(token)).status_code == 403


def test_cancelar_suscripcion_en_desarrollo(cliente):
    registrar(cliente, 'cancela@test.com')
    token = token_de(cliente, 'cancela@test.com')
    cliente.post('/api/suscripcion/checkout', json={'nivel_id': 1}, headers=autorizado(token))
    respuesta = cliente.post('/api/suscripcion/cancelar', headers=autorizado(token))
    assert respuesta.status_code == 200
    assert respuesta.get_json()['usuario']['nivel_id'] is None
    # Sin plan no puede cancelar otra vez
    assert cliente.post('/api/suscripcion/cancelar', headers=autorizado(token)).status_code == 400


def test_zona_admin_protegida(cliente):
    registrar(cliente, 'normal@test.com')
    token = token_de(cliente, 'normal@test.com')
    assert cliente.get('/api/admin/alumnos', headers=autorizado(token)).status_code == 403

    registrar(cliente, 'admin@test.com', nombre='Admin')
    token_admin = token_de(cliente, 'admin@test.com')
    respuesta = cliente.get('/api/admin/alumnos', headers=autorizado(token_admin))
    assert respuesta.status_code == 200


def test_gestion_del_temario(cliente):
    registrar(cliente, 'admin@test.com', nombre='Admin')
    token = token_de(cliente, 'admin@test.com')

    # Crear asignatura y dos temas
    respuesta = cliente.post('/api/admin/asignaturas', json={'nivel_id': 1, 'nombre': 'Inglés'},
                             headers=autorizado(token))
    assert respuesta.status_code == 201
    asignatura_id = respuesta.get_json()['asignatura']['id']
    tema_a = cliente.post(f'/api/admin/asignaturas/{asignatura_id}/temas', json={'titulo': 'Tema A'},
                          headers=autorizado(token)).get_json()['tema']
    cliente.post(f'/api/admin/asignaturas/{asignatura_id}/temas', json={'titulo': 'Tema B'},
                 headers=autorizado(token))

    # Renombrar la asignatura y editar un tema
    assert cliente.put(f'/api/admin/asignaturas/{asignatura_id}', json={'nombre': 'Inglés B1'},
                       headers=autorizado(token)).status_code == 200
    assert cliente.put(f"/api/admin/temas/{tema_a['id']}",
                       json={'titulo': 'Tema A editado', 'descripcion': 'x', 'material_url': ''},
                       headers=autorizado(token)).status_code == 200

    # Mover: A estaba primero; tras bajar, queda segundo
    assert cliente.post(f"/api/admin/temas/{tema_a['id']}/mover", json={'direccion': 'bajar'},
                        headers=autorizado(token)).status_code == 200
    # En el extremo no se puede seguir moviendo
    assert cliente.post(f"/api/admin/temas/{tema_a['id']}/mover", json={'direccion': 'bajar'},
                        headers=autorizado(token)).status_code == 400

    # Borrar la asignatura arrastra sus temas
    assert cliente.delete(f'/api/admin/asignaturas/{asignatura_id}',
                          headers=autorizado(token)).status_code == 200


def test_webhook_sin_configurar(cliente):
    assert cliente.post('/api/stripe/webhook', data=b'{}').status_code == 503


def test_recuperacion_de_password(cliente):
    registrar(cliente, 'olvido@test.com')
    # La petición no revela si el email existe
    r1 = cliente.post('/api/recuperar', json={'email': 'olvido@test.com'})
    r2 = cliente.post('/api/recuperar', json={'email': 'noexiste@test.com'})
    assert r1.status_code == r2.status_code == 200
    assert r1.get_json() == r2.get_json()

    # Con un token válido se cambia la contraseña y el login funciona
    with main.app.app_context():
        usuario = main.Usuario.query.filter_by(email='olvido@test.com').first()
        token = main.serializador_recuperacion().dumps(usuario.id)
    respuesta = cliente.post('/api/restablecer', json={'token': token, 'password': 'nueva123'})
    assert respuesta.status_code == 200
    assert cliente.post('/api/login', json={'email': 'olvido@test.com', 'password': 'nueva123'}).status_code == 200

    # Token corrupto rechazado
    assert cliente.post('/api/restablecer', json={'token': 'basura', 'password': 'nueva123'}).status_code == 400
