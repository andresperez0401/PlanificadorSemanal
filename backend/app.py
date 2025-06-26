import os
import openai
from twilio.rest import Client as TwilioClient
import json
from flask import Flask, jsonify, request
from flask_migrate import Migrate, upgrade
from flask_cors import CORS
from dotenv import load_dotenv
from api.models import db, Usuario, Tarea  
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from datetime import timedelta, datetime


load_dotenv()

# Ahora cargamos las variables Twilio y OpenAI
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True) # Permite solicitudes desde otros orígenes (React)


twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
openai.api_key   = OPENAI_API_KEY

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


# -------------------------------------------------------------------- HELPERS -------------------------------------------------------
def send_whatsapp(to: str, body: str):
    twilio_client.messages.create(
        from_=TWILIO_WHATSAPP_FROM,
        to=to,
        body=body
    )

def classify_task(text: str) -> str:
    resp = openai.ChatCompletion.create(
        model='gpt-4',
        messages=[
            { 'role': 'system',
              'content': 'Eres un categorizador: Trabajo, Personal, Descanso, Estudio, Salud.' },
            { 'role': 'user',
              'content': f"Clasifica esta tarea: '{text}'" }
        ]
    )
    return resp.choices[0].message.content.strip()


def parse_task_with_ai(text: str) -> dict:
    prompt = (
        "Devuélveme un JSON con keys: title, fecha(YYYY-MM-DD), "
        "horaInicio(HH:MM), horaFin(HH:MM) de este mensaje: " + text
    )
    resp = openai.ChatCompletion.create(
        model='gpt-4',
        messages=[{'role':'user','content':prompt}]
    )
    return json.loads(resp.choices[0].message.content)



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

        # Enviar mensaje de WhatsApp al usuario
        if user.telefono.startswith('+'):
            send_whatsapp(f'whatsapp:{user.telefono}',
                f"Nueva tarea: {nueva_tarea.titulo} ({nueva_tarea.etiqueta}) "
                f"para {nueva_tarea.fecha} {nueva_tarea.horaInicio}-{nueva_tarea.horaFin}"
            )


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



# ─── WEBHOOK WHATSAPP ──────────────────────────────────────────────────────────
@app.route('/api/whatsapp', methods=['POST'])
def whatsapp_webhook():
    from_number = request.values.get('From')   # ej: whatsapp:+521...
    body        = request.values.get('Body','').strip()

    # REGISTRAR
    if body.upper().startswith('REGISTRAR '):
        parts = body.split()
        if len(parts)==3:
            email, clave = parts[1], parts[2]
            if Usuario.query.filter_by(email=email).first():
                send_whatsapp(from_number,"Email ya registrado.")
            else:
                u = Usuario(
                    nombre   = email.split('@')[0],
                    email    = email,
                    clave    = clave,
                    telefono = from_number.replace('whatsapp:',''),
                )
                db.session.add(u); db.session.commit()
                send_whatsapp(from_number,"Usuario registrado con éxito.")
        else:
            send_whatsapp(from_number,"Usa: REGISTRAR email clave")
        return ('',200)

    # USUARIO EXISTENTE?
    u = Usuario.query.filter_by(telefono=from_number.replace('whatsapp:','')).first()
    if not u:
        send_whatsapp(from_number,"No estás registrado. Envía: REGISTRAR email clave")
        return ('',200)

    # CONSULTA TAREAS
    key = body.upper()
    if key in ('TAREAS HOY','TAREAS SEMANA'):
        hoy    = date.today()
        tareas = u.tareas
        if key=='TAREAS HOY':
            filt = [t for t in tareas if t.fecha==hoy]
        else:
            lunes = hoy - timedelta(days=hoy.weekday())
            filt  = [t for t in tareas if lunes<=t.fecha<lunes+timedelta(7)]
        if not filt:
            send_whatsapp(from_number,"No tienes tareas en ese periodo.")
        else:
            msg_lines = [f"{t.fecha} {t.horaInicio}-{t.horaFin}: {t.titulo}" for t in filt]
            send_whatsapp(from_number,"Tus tareas:\n"+ "\n".join(msg_lines))
        return ('',200)

    # TEXTO LIBRE -> CREAR TAREA
    categoria = classify_task(body)
    try:
        data = parse_task_with_ai(body)
        hi   = datetime.strptime(data['horaInicio'],'%H:%M').time()
        hf   = datetime.strptime(data['horaFin'],   '%H:%M').time()
        dur  = (datetime.combine(date.today(),hf)-datetime.combine(date.today(),hi)).seconds
        if dur<3600:
            hf = (datetime.combine(date.today(),hi)+timedelta(hours=1)).time()
        tarea = Tarea(
            titulo     = data['title'],
            fecha      = datetime.strptime(data['fecha'],'%Y-%m-%d').date(),
            horaInicio = hi,
            horaFin    = hf,
            etiqueta   = categoria,
            idUsuario  = u.idUsuario
        )
        db.session.add(tarea); db.session.commit()
        send_whatsapp(from_number,
            f"Tarea '{tarea.titulo}' agregada en '{categoria}' "
            f"para {tarea.fecha} {tarea.horaInicio}-{tarea.horaFin}"
        )
    except Exception:
        send_whatsapp(from_number,
            "No entendí tu mensaje. Usa: Título para YYYY-MM-DD HH:MM-HH:MM"
        )

    return ('',200)




if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
