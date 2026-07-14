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
                       json={'titulo': 'Tema A editado', 'descripcion': 'x'},
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


def test_editar_nivel_y_precio(cliente):
    registrar(cliente, 'admin@test.com', nombre='Admin')
    token = token_de(cliente, 'admin@test.com')

    respuesta = cliente.put('/api/admin/niveles/1',
                            json={'nombre': 'ESO', 'precio': 5.49, 'descripcion': 'Todo ESO'},
                            headers=autorizado(token))
    assert respuesta.status_code == 200

    # El cambio se refleja en los datos públicos de la academia
    niveles = cliente.get('/api/datos_academia').get_json()['niveles']
    eso = next(n for n in niveles if n['id'] == 1)
    assert eso['price'] == 5.49
    assert eso['benefits'] == 'Todo ESO'

    # Validaciones
    assert cliente.put('/api/admin/niveles/1', json={'nombre': 'ESO', 'precio': 'gratis'},
                       headers=autorizado(token)).status_code == 400
    assert cliente.put('/api/admin/niveles/1', json={'nombre': 'ESO', 'precio': -1},
                       headers=autorizado(token)).status_code == 400
    assert cliente.put('/api/admin/niveles/99', json={'nombre': 'X', 'precio': 1},
                       headers=autorizado(token)).status_code == 404

    # Un usuario normal no puede
    registrar(cliente, 'raso@test.com')
    token_raso = token_de(cliente, 'raso@test.com')
    assert cliente.put('/api/admin/niveles/1', json={'nombre': 'Hack', 'precio': 0.01},
                       headers=autorizado(token_raso)).status_code == 403


def test_materiales_de_un_tema(cliente):
    registrar(cliente, 'admin@test.com', nombre='Admin')
    token = token_de(cliente, 'admin@test.com')

    asignatura_id = cliente.post('/api/admin/asignaturas', json={'nivel_id': 1, 'nombre': 'Historia'},
                                 headers=autorizado(token)).get_json()['asignatura']['id']
    tema_id = cliente.post(f'/api/admin/asignaturas/{asignatura_id}/temas', json={'titulo': 'La Edad Media'},
                           headers=autorizado(token)).get_json()['tema']['id']

    # Añadir un vídeo y unos apuntes
    respuesta = cliente.post(f'/api/admin/temas/{tema_id}/materiales',
                             json={'tipo': 'video', 'titulo': 'Clase en vídeo', 'url': 'https://youtu.be/x'},
                             headers=autorizado(token))
    assert respuesta.status_code == 201
    material_id = respuesta.get_json()['material']['id']
    assert cliente.post(f'/api/admin/temas/{tema_id}/materiales',
                        json={'tipo': 'apuntes', 'titulo': 'Apuntes del tema', 'url': 'https://drive.x/y'},
                        headers=autorizado(token)).status_code == 201

    # Tipo inválido y campos vacíos rechazados
    assert cliente.post(f'/api/admin/temas/{tema_id}/materiales',
                        json={'tipo': 'podcast', 'titulo': 'X', 'url': 'https://x'},
                        headers=autorizado(token)).status_code == 400
    assert cliente.post(f'/api/admin/temas/{tema_id}/materiales',
                        json={'tipo': 'video', 'titulo': '', 'url': ''},
                        headers=autorizado(token)).status_code == 400

    # El contenido del nivel devuelve los materiales en orden
    contenido = cliente.get('/api/niveles/1/contenido', headers=autorizado(token)).get_json()
    historia = next(a for a in contenido['asignaturas'] if a['nombre'] == 'Historia')
    materiales = historia['temas'][0]['materiales']
    assert [m['tipo'] for m in materiales] == ['video', 'apuntes']

    # Borrar un material
    assert cliente.delete(f'/api/admin/materiales/{material_id}',
                          headers=autorizado(token)).status_code == 200

    # Borrar la asignatura arrastra temas y materiales sin errores
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
