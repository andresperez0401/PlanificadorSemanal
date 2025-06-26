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
from datetime import timedelta, datetime, date


load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True) # Permite solicitudes desde otros orígenes (React)

# Twilio y OpenAI desde .env
TW_SID   = os.getenv('TWILIO_ACCOUNT_SID')
TW_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TW_FROM  = os.getenv('TWILIO_WHATSAPP_NUMBER')
openai.api_key = os.getenv('OPENAI_API_KEY')
twilio = TwilioClient(TW_SID, TW_TOKEN)

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


#Ruta para ver si existe el telefono
@app.route('/usuario/telefono/<string:telefono>', methods=['GET'])
def verificar_telefono(telefono):
    # Verificamos si el teléfono ya existe
    usuario = Usuario.query.filter_by(telefono=telefono).first()
    
    if usuario:
        return jsonify({'existe': True, 'usuario': usuario.serialize()}), 200
    else:
        return jsonify({'existe': False}), 404
    

#Ruta para devolver tareas de un usuario por numero de teléfono
@app.route('/usuario/telefono/<string:telefono>/tareas', methods=['GET'])
def obtener_tareas_por_telefono(telefono):
    # Verificamos si el teléfono ya existe
    usuario = Usuario.query.filter_by(telefono=telefono).first()
    
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    # Obtenemos las tareas del usuario
    tareas = usuario.tareas
    return jsonify([t.serialize() for t in tareas]), 200


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



# --------------------------------------------------------------------------- WEBHOOK WHATSAPP ---------------------------------------------------------------------

# ── helpers ────────────────────────────────────────────────────────────────
def send_whatsapp(to, body):
    twilio.messages.create(
        from_=f"whatsapp:{TW_FROM}",
        to=f"whatsapp:{to}",
        body=body
    )

def classify_task(text):
    r = openai.ChatCompletion.create(
        model='gpt-4',
        messages=[
          {'role':'system','content':'Categorizador: Trabajo, Personal, Descanso, Estudio, Salud.'},
          {'role':'user','content':text}
        ]
    )
    return r.choices[0].message.content.strip()

def parse_task_with_ai(text):
    prompt = (
      "Devuélveme JSON con title, fecha(YYYY-MM-DD), "
      "horaInicio(HH:MM), horaFin(HH:MM) para: " + text
    )
    r = openai.ChatCompletion.create(
      model='gpt-4',
      messages=[{'role':'user','content':prompt}]
    )
    return json.loads(r.choices[0].message.content)

# ── webhook ────────────────────────────────────────────────────────────────
@app.route('/api/whatsapp', methods=['POST'])
def whatsapp_webhook():
    raw_from = request.values.get('From','')   # "whatsapp:+123..."
    phone    = raw_from.replace('whatsapp:','')# "+123..."
    body     = request.values.get('Body','').strip()

    # 1) REGISTRAR
    if body.upper().startswith('REGISTRAR '):
        parts = body.split()
        if len(parts)==3:
            email, pwd = parts[1], parts[2]
            if Usuario.query.filter_by(email=email).first():
                send_whatsapp(phone, "❌ Email ya registrado.")
            else:
                u = Usuario(
                  nombre=email.split('@')[0],
                  email=email,
                  clave=pwd,
                  telefono=phone
                )
                db.session.add(u); db.session.commit()
                send_whatsapp(phone, "✅ ¡Registrado! Bienvenido.")
        else:
            send_whatsapp(phone, "ℹ️ Usa: REGISTRAR tu_email tu_contraseña")
        return ('',200)

    # 2) ¿Usuario existe?
    u = Usuario.query.filter_by(telefono=phone).first()
    if not u:
        send_whatsapp(phone,
          "❌ No estás registrado. Envía:\n"
          "REGISTRAR tu_email@ejemplo.com tu_contraseña"
        )
        return ('',200)

    cmd = body.upper()
    # 3) TAREAS HOY / SEMANA
    if cmd in ('TAREAS HOY','TAREAS SEMANA'):
        hoy = date.today()
        tareas = u.tareas
        if cmd=='TAREAS HOY':
            filt = [t for t in tareas if t.fecha==hoy]
        else:
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            filt = [t for t in tareas
                    if inicio_semana<=t.fecha<inicio_semana+timedelta(7)]
        if not filt:
            send_whatsapp(phone, "ℹ️ No tienes tareas en este período.")
        else:
            lines = [f"{t.fecha} {t.horaInicio}-{t.horaFin}: {t.titulo}"
                     for t in filt]
            send_whatsapp(phone, "🗓️ Tus tareas:\n"+"\n".join(lines))
        return ('',200)

    # 4) TEXTO LIBRE → CREAR TAREA por IA
    categ = classify_task(body)
    try:
        d = parse_task_with_ai(body)
        hi = datetime.strptime(d['horaInicio'],'%H:%M').time()
        hf = datetime.strptime(d['horaFin'   ],'%H:%M').time()
        # mínimo 1h
        if (datetime.combine(hoy,hf)-datetime.combine(hoy,hi)).seconds<3600:
            hf = (datetime.combine(hoy,hi)+timedelta(hours=1)).time()
        tarea = Tarea(
          titulo=d['title'],
          fecha=datetime.strptime(d['fecha'],'%Y-%m-%d').date(),
          horaInicio=hi, horaFin=hf,
          etiqueta=categ, idUsuario=u.idUsuario
        )
        db.session.add(tarea); db.session.commit()
        send_whatsapp(phone,
          f"✅ Tarea '{tarea.titulo}' en '{categ}' "
          f"para {tarea.fecha} {tarea.horaInicio}-{tarea.horaFin}"
        )
    except Exception:
        send_whatsapp(phone,
          "❓ No entendí tu mensaje. Usa:\n"
          "Título para YYYY-MM-DD HH:MM-HH:MM"
        )
    return ('',200)



if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
