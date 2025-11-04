from sqlalchemy import Column, Integer, String, Float, Date, Time, DateTime, Text, ForeignKey, Boolean, DECIMAL, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Auxiliar(Base):
    __tablename__ = "auxiliares"
    id_auxiliar = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100))
    cedula = Column(String(20))
    correo = Column(String(120))
    hoja_excel = Column(String(100))
    capacidad_hora = Column(Float)  # equivalente a DECIMAL(5,2)
    activo = Column(Boolean, default=True)
    producciones = relationship("Produccion", back_populates="auxiliar")

class CuadroControl(Base):
    __tablename__ = "cuadro_control"
    id = Column(Integer, primary_key=True, index=True)
    cedula = Column(String(20), nullable=False)
    apellidos_nombres = Column(String(150), nullable=False)
    tipologia_finca = Column(String(150))
    folios = Column(Integer)
    semana = Column(Integer)
    fecha_publicacion = Column(Date)
    fecha_indexacion = Column(Date)
    ans_indexacion = Column(Integer)
    fecha_ins_fisica = Column(Date)
    ans_ins_fisica = Column(Integer)
    finca = Column(String(50))
    numero_tarea_wm = Column(String(50))
    tipo = Column(String(50))
    observacion = Column(Text)
    mes = Column(String(20))
    fecha_carga = Column(DateTime, default=datetime.now)

class Produccion(Base):
    __tablename__ = "produccion_auxiliar"
    id = Column(Integer, primary_key=True, autoincrement=True)
    auxiliar = Column(String(100), nullable=False)
    fecha_produccion = Column(Date, nullable=False)
    empresa = Column(String(100))
    actividad = Column(Text)
    unidad_medida = Column(String(50))
    hora_inicio = Column(Time)
    hora_fin = Column(Time)
    cantidad_ejecutada = Column(Float)
    porcentaje_cumplimiento = Column(Float)
    caja_mantis = Column(String(20))
    observaciones = Column(Text)
    deber_ejecutar = Column(Float)
    horas_ejecutadas = Column(Float)
    estandar_h = Column(Float)
    creado_en = Column(DateTime, default=datetime.now)

    # Si quisieras relacionarla con la tabla Auxiliares
    auxiliar_id = Column(Integer, ForeignKey("auxiliares.id_auxiliar"))
    auxiliar = relationship("Auxiliar", back_populates="producciones")

