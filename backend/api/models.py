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
    telefono: Mapped[str] = mapped_column(String(20), nullable=False)
    tipo: Mapped[str] = mapped_column(String(80),nullable=False)

  
    def serialize(self):
        return {
            'idUsuario': self.idUsuario,
            'nombre': self.nombre,
            'email': self.email,
            'telefono': self.telefono,
            'tipo': self.tipo
        }