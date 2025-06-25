import os
from flask import Flask, jsonify, request
from flask_migrate import Migrate, upgrade
from flask_cors import CORS
from dotenv import load_dotenv
from api.models import db, Usuario  

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

#---------------------------------------------------- Termina la BD configuración -----------------------------------------------------


#----------------------------------------------------- Rutas --------------------------------------------------------------------------

#Ruta base
@app.route('/')
def index():
    return jsonify({"mensaje": "Hola desde Flask!"})

#Ruta para agregar un usuario
@app.route('/usuarios', methods=['POST'])
def crear_usuario():
    data = request.get_json()

    nuevo_usuario = Usuario(
        nombre=data.get('nombre'),
        email=data.get('email'),
        clave=data.get('clave'),
        telefono=data.get('telefono'),
        tipo=data.get('tipo')
    )

    db.session.add(nuevo_usuario)
    db.session.commit()

    return jsonify({"mensaje": "Usuario creado exitosamente", "usuario": nuevo_usuario.serialize()}), 201


# Ruta para obtener todos los usuarios
@app.route('/usuarios', methods=['GET'])
def obtener_usuarios():
    usuarios = Usuario.query.all()
    return jsonify([u.serialize() for u in usuarios]), 200



if __name__ == '__main__':
    app.run(debug=True, port=5000)  # Ejecuta la aplicación en el puerto 5000	
