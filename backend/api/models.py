from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Integer, Date, Time, ForeignKey, Boolean, Float
from datetime import date, time
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref
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

    idTarea: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(120), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(120), nullable=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    horaInicio: Mapped[time] = mapped_column(Time, nullable=False)
    horaFin: Mapped[time] = mapped_column(Time, nullable=False)
    etiqueta: Mapped[str] = mapped_column(String(50), nullable=False)
    imageUrl: Mapped[str] = mapped_column(String(120), nullable=True)
    idUsuario: Mapped[int] = mapped_column(Integer, ForeignKey('usuario.idUsuario'), nullable=False)
    
    usuario = relationship('Usuario', backref=backref('tareas', lazy=True))
    
    def serialize(self):
        return {
            'idTarea': self.idTarea,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'fecha': self.fecha.strftime('%Y-%m-%d'),
            'horaInicio': self.horaInicio.strftime('%H:%M'),
            'horaFin': self.horaFin.strftime('%H:%M'),
            'etiqueta': self.etiqueta,
            'imageUrl': self.imageUrl,
            'idUsuario': self.idUsuario
        }