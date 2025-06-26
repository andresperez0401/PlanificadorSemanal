from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Integer, Date, Time, ForeignKey, Boolean, Float
from datetime import date, time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import LargeBinary
import uuid


db = SQLAlchemy()

# ---------------------------- Usuario ----------------------------
class Usuario(db.Model):
    __tablename__ = 'usuario'

    idUsuario: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    clave: Mapped[str] = mapped_column(String(120))
    telefono: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
  
    def serialize(self):
        return {
            'idUsuario': self.idUsuario,
            'nombre': self.nombre,
            'email': self.email,
            'telefono': self.telefono
        }
    

# ---------------------------- Tarea ----------------------------

class Tarea(db.Model):
    __tablename__ = 'tarea'

    idTarea = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(120), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    horaInicio = db.Column(db.Time, nullable=False)
    horaFin = db.Column(db.Time, nullable=False)
    etiqueta = db.Column(db.String(50), nullable=False)  # Trabajo, Personal, etc.
    idUsuario = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    
    # Relación con Usuario
    usuario = db.relationship('Usuario', backref=db.backref('tareas', lazy=True))
    
    def serialize(self):
        return {
            'idTarea': self.idTarea,
            'titulo': self.titulo,
            'fecha': self.fecha.isoformat(),
            'horaInicio': self.horaInicio.strftime('%H:%M'),
            'horaFin': self.horaFin.strftime('%H:%M'),
            'etiqueta': self.etiqueta,
            'idUsuario': self.idUsuario
        }
