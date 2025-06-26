import os
from flask import Flask, jsonify, request
from flask_migrate import Migrate, upgrade
from flask_cors import CORS
from dotenv import load_dotenv
from api.models import db, Usuario, Tarea  
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from datetime import timedelta, datetime

load_dotenv()

app = Flask(__name__)
CORS(app)  # Permite solicitudes desde otros orígenes (React)


#----------------------------------------------------- Base de Datos -----------------------------------------------------------------

# 1) Armamos la ruta al archivo SQLite
base_dir = os.path.dirname(os.path.realpath(__file__))  # carpeta backend/
ruta_sqlite = os.path.join(base_dir, "sqlite", "database.db")
default_uri = f"sqlite:///{ruta_sqlite}"

# 2) Usa DATABASE_URL si está definido, si no, SQLite local
db_uri = os.getenv("DATABASE_URL", default_uri).replace("postgres://", "postgresql://")
app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
Migrate(app, db, compare_type=True)

# Configuraciones de JWT
app.config["JWT_SECRET_KEY"] = "clave-secreta"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

jwt = JWTManager(app)

#---------------------------------------------------- Termina la BD configuración -----------------------------------------------------


#----------------------------------------------------- Rutas --------------------------------------------------------------------------

#Ruta base
@app.route('/')
def index():
    return jsonify({"mensaje": "Hola desde Flask!"})

#------------------------------------------------------ Usuario -------------------------------------------------------------------------
#Ruta para crear un usuario
@app.route('/usuario', methods=['POST'])
def crear_usuario():

    data = request.get_json() or {}
    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400
    
    # Campos requeridos
    required_fields = ['nombre', 'email', 'clave', 'telefono']
    empty_fields = [f for f in required_fields if not data.get(f)]
    if empty_fields:
        return jsonify({
            'error': 'Algunos campos están vacíos o faltan',
            'Campos vacíos o faltantes': empty_fields
        }), 400
    
    # Verificar si el email ya existe
    if Usuario.query.filter_by(email=data.get('email')).first():
        return jsonify({'error': 'El email ya está en uso'}), 400
    
    # Verificar si el teléfono ya existe
    if Usuario.query.filter_by(telefono=data.get('telefono')).first():
        return jsonify({'error': 'El teléfono ya está en uso'}), 400
    

    nuevo_usuario = Usuario(
        nombre=data.get('nombre'),
        email=data.get('email'),
        clave=data.get('clave'),
        telefono=data.get('telefono'),
    )

    db.session.add(nuevo_usuario)
    db.session.commit()

    return jsonify({"msj": "Usuario creado exitosamente", "usuario": nuevo_usuario.serialize()}), 201



# Ruta para obtener todos los usuarios
@app.route('/usuarios', methods=['GET'])
def obtener_usuarios():
    usuarios = Usuario.query.all()
    return jsonify([u.serialize() for u in usuarios]), 200



#Ruta para logear un usuario
@app.route('/login', methods=['POST'])
def login_usuario():

    data = request.get_json() or {}
    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400
    
    # Campos requeridos
    required_fields = ['email', 'clave']

    # Verificamos que no falte ninguno de los campos requeridos ni que estén vacíos
    empty_fields = [field for field in required_fields if not data.get(field)]

    if empty_fields:
        return jsonify({
            'error': 'Algunos campos están vacíos o faltan',
            'Campos vacíos o faltantes': empty_fields
        }), 400
    
    # Verificamos si el usuario existe
    usuario = Usuario.query.filter_by(email=data.get('email'), clave=data.get('clave')).first()

    if not usuario:
        return jsonify({'error': 'Usuario o contraseña incorrectos'}), 401
    
    # Generamos el token de acceso
    access_token = create_access_token(
        identity=usuario.email,
        expires_delta=timedelta(hours=1),
        additional_claims={"telefono": usuario.telefono, "nombre": usuario.nombre}
    )
    return jsonify({'msg' : 'Usuario Logeado Exitosamente', 'usuario' : usuario.serialize(), 'token': access_token}), 200



# Ruta para eliminar un usuario por email
@app.route('/usuario/<string:email>', methods=['DELETE'])
@jwt_required()
def eliminar_usuario(email):
    
    # Verificamos si el usuario está autenticado
    email_user = get_jwt_identity()
    if not email_user:
        return jsonify({'error': 'Usuario no autenticado'}), 401
    
    # Buscamos el usuario por email
    usuario = Usuario.query.filter_by(email=email_user).first()
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    # Eliminamos el usuario
    db.session.delete(usuario)
    db.session.commit()     

    return jsonify({'msg': 'Usuario eliminado exitosamente'}), 200


#------------------------------------------------------- Finalizan las rutas de Usuario -------------------------------------------------------------------------



# ----------------------------------------------------------- Rutas para tareas ---------------------------------------------------------------------------------


#Ruta para obtener las tareas de un usuario
@app.route('/tareas', methods=['GET'])
@jwt_required()
def obtener_tareas():

    email_user = get_jwt_identity()
    if not email_user:
        return jsonify({'msg': 'Usuario no autenticado'}), 401  
    
        # Obtenemos el usuario autenticado
    user = Usuario.query.filter_by(email=email_user).first()
    if not user:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    
    # Obtenemos las tareas del usuario autenticado
    tareas = user.tareas
    return jsonify([t.serialize() for t in tareas]), 200


# Ruta para crear una nueva tarea
@app.route('/tarea', methods=['POST'])
@jwt_required()
def crear_tarea():

    try:
        data = request.get_json() or {}
        if not data:
            return jsonify({'msg': 'No se recibieron datos'}), 400
        
        # Campos requeridos
        required_fields = ['titulo', 'fecha', 'horaInicio', 'horaFin', 'etiqueta']
        empty_fields = [f for f in required_fields if not data.get(f)]
        if empty_fields:
            return jsonify({
                'msg': 'Algunos campos están vacíos o faltan',  
                'Campos vacíos o faltantes': empty_fields
            }), 400
        
        try:
            fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
            horaInicio = datetime.strptime(data['horaInicio'], '%H:%M').time()
            horaFin    = datetime.strptime(data['horaFin'],    '%H:%M').time()
        except ValueError as err:
            return jsonify({
                'msg':   'Formato de fecha/hora inválido',
                'error': str(err)
            }), 400

        # Verificamos si el usuario está autenticado
        email_user = get_jwt_identity()
        if not email_user:
            return jsonify({'msg': 'Usuario no autenticado'}), 401
        
        # Obtenemos el usuario autenticado
        user = Usuario.query.filter_by(email=email_user).first()
        if not user:
            return jsonify({'msg': 'Usuario no encontrado'}), 404
        
        nueva_tarea = Tarea(
            titulo=data.get('titulo'),
            fecha=fecha,
            horaInicio=horaInicio,
            horaFin=horaFin,
            etiqueta=data.get('etiqueta'),
            idUsuario=user.idUsuario
        )

        db.session.add(nueva_tarea)
        db.session.commit()
        return jsonify({"mensaje": "Tarea creada exitosamente", "tarea": nueva_tarea.serialize()}), 201

    except Exception as ex:
            # imprime en consola el traceback
            import traceback; traceback.print_exc()
            # siempre devolvemos JSON
            return jsonify({
                'msg':   'Error interno al crear tarea',
                'error': str(ex)
            }), 500




# Ruta para eliminar una tarea por ID
@app.route('/tarea/<int:id_tarea>', methods=['DELETE'])
@jwt_required()
def eliminar_tarea(id_tarea):
    # Verificamos si el usuario está autenticado
    email_user = get_jwt_identity()
    if not email_user:
        return jsonify({'msg': 'Usuario no autenticado'}), 401
        
    # Obtenemos el usuario autenticado
    user = Usuario.query.filter_by(email=email_user).first()
    if not user:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    
    # Buscamos la tarea por ID
    tarea = Tarea.query.filter_by(idTarea=id_tarea, idUsuario=user.idUsuario).first()
    if not tarea:
        return jsonify({'msg': 'Tarea no encontrada'}), 404
    
    # Eliminamos la tarea
    db.session.delete(tarea)
    db.session.commit()
    return jsonify({'msg': 'Tarea eliminada exitosamente'}), 200

# ----------------------------------------------------------- Finalizan las rutas para tareas -------------------------------------------------------------------------





if __name__ == '__main__':
    app.run(debug=True, port=5000)  # Ejecuta la aplicación en el puerto 5000	
