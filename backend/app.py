import os
import requests
from openai import OpenAI
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
CORS(app,
     resources={r"/*": {"origins": "https://planificador-semanal-omega.vercel.app"}},
     supports_credentials=False,
     allow_headers=["Content-Type", "Authorization"],
     expose_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])


# Twilio y OpenAI desde .env
TW_SID   = os.getenv('TWILIO_ACCOUNT_SID')
TW_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TW_FROM  = os.getenv('TWILIO_WHATSAPP_NUMBER')
OPENAI_API_KEY = os.getenv("OPENAI_APIKEY")
OPENAI_PROJECT_ID = os.getenv("OPENAI_PROJECT_ID")

# print(f"TW_SID: {TW_SID}, TW_FROM: {TW_FROM}, OPENAI_API_KEY: {OPENAI_API_KEY}, TW_TOKEN: {TW_TOKEN}")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# print(f"TW_SID: {TW_SID}, TW_FROM: {TW_FROM}, OPENAI_API_KEY: {OPENAI_API_KEY}")
openai_client = OpenAI(api_key=OPENAI_API_KEY,project=OPENAI_PROJECT_ID)
twilio_client = TwilioClient(TW_SID, TW_TOKEN)

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

    numero = telefono.replace('whatsapp:', '')  # Normalizamos el número eliminando el '+'
    usuario = Usuario.query.filter_by(telefono=numero).first()
    
    if usuario:
        return jsonify({'existe': True, 'usuario': usuario.serialize()}), 200
    else:
        return jsonify({'existe': False}), 200
    

#Ruta para devolver tareas de un usuario por numero de teléfono
@app.route('/usuario/telefono/<string:telefono>/tareas', methods=['GET'])
def obtener_tareas_por_telefono(telefono):
    # Verificamos si el teléfono ya existe

    numero = telefono.replace('whatsapp:', '')
    usuario = Usuario.query.filter_by(telefono=numero).first()
    
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
    return jsonify({
        "success": True,
        "tareas": [t.serialize() for t in tareas]  # Envuelve en objeto
    }), 200


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
        

        #Verificaamos si hay descripción, si no la hay, la dejamos en None
        descripcion = data.get('descripcion', "Descripcion de la tarea" + data.get('titulo', ''))

        #Verificamos qe haya imagen
        imageUrl = data.get('imageUrl', "")
        
        nueva_tarea = Tarea(
            titulo=data.get('titulo'),
            descripcion=descripcion,
            imageUrl=imageUrl,
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
            texto_whatsapp = (
                "🆕 *Nueva Tarea Creada*\n\n"
                f"📌 *Título:* {nueva_tarea.titulo}\n"
                f"🗂️ *Categoría:* {nueva_tarea.etiqueta}\n"
                f"📅 *Fecha:* {nueva_tarea.fecha.strftime('%Y-%m-%d')}\n"
                f"⏰ *Hora:* {nueva_tarea.horaInicio.strftime('%H:%M')} - {nueva_tarea.horaFin.strftime('%H:%M')}\n"
            )
            send_message(user.telefono, texto_whatsapp)


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


# ---- Para enviar enviar mensajes de WhatsApp
def send_message(to, body):
    twilio_client.messages.create(
        from_=TW_FROM,
        to=f"whatsapp:{to}",
        body=body
    )


# Ruta para recibir mensajes de WhatsApp
@app.route("/whatsapp-webhook", methods=["POST"])
def whatsapp_webhook():
    from_number = request.form.get('From', '').replace('whatsapp:', '')
    body = request.form.get('Body', '').strip().lower()

    if not from_number or not body:
        return "Faltan datos", 400

    user = Usuario.query.filter_by(telefono=from_number).first()
    if not user:
        send_message(from_number, "🚫 No estás registrado. Por favor regístrate para usar el Organizapp.")
        return "Usuario no registrado", 200

    if body in ["hola", "menu", "opciones", "que tal", "buenas", "buenas tardes", "buenas noches", "Hola"]:
        send_message(from_number,
            "👋 Hola " + user.nombre + "! , elige una opción:\n1️⃣ Crear tarea (Deshabilitada - en desarrollo) \n2️⃣ Ver tareas pendientes\n\nResponde con 1 o 2.")
        return "Menú enviado", 200

    elif body.startswith("1") or "crear tarea" in body:
        send_message(from_number, "✍️ Por favor describe la tarea. Ejemplo:\n'Agendar paseo con el perro mañana a las 10 AM'")
        return "Esperando descripción", 200
    
    # elif body.startswith("3") or "registrar usuario" in body or "Registrar" in body:

    elif any(word in body for word in ["mañana", "pasado", "am", "pm", "agendar", "a las", "para el", "el ", "día "]):
        task_data = extract_task_fields_from_prompt(body)
        if not task_data:
            send_message(from_number, "❌ No pude entender la tarea. Intenta describirla de otra forma.")
            return "Error IA", 200
        
        if not es_fecha_valida(task_data["date"]):
            send_message(from_number, "❌ No pude entender la fecha. Intentá usar frases como 'mañana', 'el 2 de julio', etc.")
            return "Fecha inválida", 200

        new_task = Tarea(
            idUsuario=user.idUsuario,
            titulo=task_data["title"],
            descripcion = task_data["description"],
            imageUrl = ("", None),
            fecha=datetime.strptime(task_data["date"], "%Y-%m-%d").date(),
            horaInicio=datetime.strptime(task_data["hour"], "%H:%M").time(),
            horaFin=datetime.strptime(task_data["endHour"], "%H:%M").time(),
            etiqueta=task_data["category"]
        )
        db.session.add(new_task)
        db.session.commit()

        fecha_formateada = new_task.fecha.strftime("%A %d de %B")
        hora_formateada  = new_task.horaInicio.strftime("%H:%M")
        msg = f"✅ Tarea creada:\n📌 {new_task.titulo}\n📅 {fecha_formateada} 🕒 {hora_formateada}\n📂 {new_task.etiqueta}"

        send_message(from_number, msg)
        return "Tarea creada", 201

    elif body.startswith("2") or "ver tarea" in body or "pendiente" in body:
        tasks = Tarea.query.filter_by(idUsuario=user.idUsuario).all()
        if not tasks:
            send_message(from_number, "📭 No tienes tareas pendientes.")
        else:
            listado = "\n".join([
                f"📌 {t.titulo} ({t.fecha.strftime('%d/%m')} a las {t.horaInicio.strftime('%H:%M')})"
                for t in tasks
            ])
            send_message(from_number, f"📋 Tus tareas pendientes:\n{listado}")
        return "Tareas listadas", 200

    else:
        send_message(from_number, "🤖 No entendí. Escribí 'menu' para comenzar.")
        return "Sin coincidencia", 200
    

# Funcion para categorizar y  obtener datos con IA Deepseek
# def extract_task_fields_from_prompt(text):
#     try:
#         today = datetime.now().date()
#         prompt = f"""
#             Sos un asistente que transforma descripciones de tareas en objetos JSON con formato preciso. Recibís frases informales, en español o spanglish, y devolvés exclusivamente un JSON con estos campos:

#             - "title": título corto de la tarea
#             - "date": fecha en formato YYYY-MM-DD (puede inferirse de palabras como "mañana", "pasado mañana", "lunes", "el 28", etc.)
#             - "hour": hora de inicio en formato 24h HH:MM (ejemplo: 14:30)
#             - "endHour": hora de finalización en formato 24h HH:MM. Si no está clara, sumá 1 hora a "hour"
#             - "category": elegí una sola categoría de esta lista exacta (en mayúscula inicial): Personal, Trabajo, Estudio, Hogar, Salud, Otros

#             ⚠️ Reglas clave:
#             - No uses fechas anteriores a {today}.
#             - Convertí palabras como "mañana", "pasado mañana" a fechas reales:
#                 - "mañana" → {today + timedelta(days=1)}
#                 - "pasado mañana" → {today + timedelta(days=2)}
#             - Si dicen solo la hora ("a las 9"), asumí que es AM. Si dicen "a la noche", asumí PM.
#             - Si falta hora fin, sumá 1 hora a la de inicio (pero nunca menor).
#             - No incluyas ningún texto explicativo. Solo el JSON válido.
#             - El JSON debe estar bien formado, sin comentarios ni saltos innecesarios.

#             ✍️ Ejemplos:

#             Entrada: "Tengo que ir al médico mañana a las 10"
#             → JSON:
#             {{
#             "title": "Ir al médico",
#             "date": "{(today + timedelta(days=1)).strftime('%Y-%m-%d')}",
#             "hour": "10:00",
#             "endHour": "11:00",
#             "category": "Salud"
#             }}

#             Entrada: "Clase de inglés el sábado a las 15"
#             → JSON:
#             {{
#             "title": "Clase de inglés",
#             "date": "[calculá la próxima fecha que sea sábado]",
#             "hour": "15:00",
#             "endHour": "16:00",
#             "category": "Estudio"
#             }}

#             Descripción original: "{text}"
#             """

#         # Configuración para DeepSeek API
#         url = "https://api.deepseek.com/v1/chat/completions"
#         headers = {
#             "Authorization": f"Bearer {DEEPSEEK_API_KEY}",  # Usa la variable con f-string
#             "Content-Type": "application/json"
#         }
#         data = {
#             "model": "deepseek-chat",
#             "messages": [{"role": "user", "content": prompt}],
#             "max_tokens": 150,
#             "temperature": 0.2,
#             "stream": False
#         }

#         response = requests.post(url, headers=headers, json=data)
#         if response.status_code != 200:
#             print(f"Error en DeepSeek API: {response.status_code} - {response.text}")
#             return None
        
#         response_data = response.json()

#         if not response_data.get('choices') or not response_data['choices']:
#             print("Respuesta sin choices:", response_data)
#             return None
        
#         # Extraer el contenido del JSON
#         content = response_data['choices'][0]['message']['content']
        
#         # Limpiar posibles espacios y saltos de línea
#         content = content.strip()
        
#         # Manejar casos donde la respuesta pueda incluir texto adicional
#         if content.startswith('{') and content.endswith('}'):
#             return json.loads(content)
#         else:
#             # Intentar extraer solo el JSON si hay texto adicional
#             start = content.find('{')
#             end = content.rfind('}') + 1
#             if start != -1 and end != 0:
#                 json_str = content[start:end]
#                 return json.loads(json_str)
#             else:
#                 print(f"No se pudo extraer JSON de: {content}")
#                 return None

#     except Exception as e:
#         print(f"Error en DeepSeek: {e}")
#         return None


def es_fecha_valida(fecha_str):
    try:
        datetime.strptime(fecha_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

# Funcion para categorizar y  obtener datos con IA chatgpt
def extract_task_fields_from_prompt(text):
    try:
        today = datetime.now().date()
        prompt = f"""
            Sos un asistente que transforma descripciones de tareas en objetos JSON con formato preciso. Recibís frases informales, en español o spanglish, y devolvés exclusivamente un JSON con estos campos:

            - "title": título corto de la tarea
            - "date": fecha en formato YYYY-MM-DD (puede inferirse de palabras como "mañana", "pasado mañana", "lunes", "el 28", etc.)
            - "hour": hora de inicio en formato 24h HH:MM (ejemplo: 14:30)
            - "endHour": hora de finalización en formato 24h HH:MM. Si no está clara, sumá 1 hora a "hour"
            - "category": elegí una sola categoría de esta lista exacta (en mayúscula inicial): Personal, Trabajo, Estudio, Hogar, Salud, Otros

            ⚠️ Reglas clave:
            - No uses fechas anteriores a {today}.
            - Convertí palabras como "mañana", "pasado mañana" a fechas reales:
                - "mañana" → {today + timedelta(days=1)}
                - "pasado mañana" → {today + timedelta(days=2)}
            - Si dicen solo la hora ("a las 9"), asumí que es AM. Si dicen "a la noche", asumí PM.
            - Si falta hora fin, sumá 1 hora a la de inicio (pero nunca menor).
            - No incluyas ningún texto explicativo. Solo el JSON válido.
            - El JSON debe estar bien formado, sin comentarios ni saltos innecesarios.
            - Si te dicen proximo sabado, o proximo dia o lo que sea, tu encargate de devolver la fecha correcta, no pongas [calculá la próxima fecha que sea sábado] ni nada por el estilo. DEvuelve la fehca con el formato especififcado.
            - Intrepreta lo que te dicen, si faltan datos tu agregalo smanualmente calculando lo que falta, por ejemplo si te dicen "a las 10" vos poné "10:00" y "11:00" como hora de finalización, o si te dicen "el lunes a las 9" vos poné la fecha del próximo lunes y la hora de inicio y fin.
            - Necesito que siempre registres los datos completos.
            - Tambien necesito que ahora interpretes la descripcion, es decir que en base a lo que te digan devuelvas tambein un campo decripcion en base al titulo
            - Explciando un poco mejor la DESCRIPCION ES SUPER IMPORTANTE, por ejemplo si te dicen "Tengo que ir al médico mañana a las 10" vos poné "Ir al médico" como título y "Tengo que ir al médico" como descripción, o si te dicen "Clase de inglés el sábado a las 15" vos poné "Clase de inglés" como título y "Clase de inglés el sábado a las 15" como descripción.
            
            Entrada: "Clase de inglés el sábado a las 15"
            → JSON:
            {{
            "title": "Clase de inglés",
            "date": "2025-07-05",  # reemplazá por el próximo sábado dinámico
            "hour": "15:00",
            "endHour": "16:00",
            "category": "Estudio"
            "description": "Clase de inglés el sábado a las 15"
            }}

            - Si te piden un día como "sábado", devolvé la PRÓXIMA fecha real que sea sábado (en formato YYYY-MM-DD)
            ejemplo : next_saturday = next_weekday_date("sábado").strftime("%Y-%m-%d")

            Entrada: "Clase de inglés el sábado a las 15"
            → JSON:
            {{
            "title": "Clase de inglés",
            "date": "2025-07-05",  # reemplazá por el próximo sábado dinámico
            "hour": "15:00",
            "endHour": "16:00",
            "category": "Estudio"
            "description": "Clase de inglés el sábado a las 15"
            }}

            Necesito que sigas tal cual te digo 


            ✍️ Ejemplos:

            Entrada: "Tengo que ir al médico mañana a las 10"
            → JSON:
            {{
            "title": "Ir al médico",
            "date": "{(today + timedelta(days=1)).strftime('%Y-%m-%d')}",
            "hour": "10:00",
            "endHour": "11:00",
            "category": "Salud"
            "description": "Tengo que ir al médico mañana a las 10"	
            }}

            Entrada: "Clase de inglés el sábado a las 15"
            → JSON:
            {{
            "title": "Clase de inglés",
            "date": "[calculá la próxima fecha que sea sábado]",
            "hour": "15:00",
            "endHour": "16:00",
            "category": "Estudio"
            }}

            Descripción original: "{text}"
            """


        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.2
        )

        import json
        return json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        print(f"Error en OpenAI: {e}")
        return None
    

def next_weekday_date(dia_nombre):
    dias = {
        "lunes": 0, "martes": 1, "miércoles": 2,
        "jueves": 3, "viernes": 4, "sábado": 5, "domingo": 6
    }
    today = datetime.now().date()
    target = dias.get(dia_nombre.lower(), None)
    if target is None:
        return None
    days_a_sumar = (target - today.weekday() + 7) % 7
    return today + timedelta(days=days_a_sumar or 7)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
