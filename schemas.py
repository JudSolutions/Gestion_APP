from pydantic import BaseModel
from datetime import date, time, datetime
from typing import Optional, List

class CuadroControlBase(BaseModel):
    cedula: str
    nombre: str
    tipologia_finca: Optional[str]
    fecha_publicacion: Optional[date]
    fecha_indizacion: Optional[date]
    fecha_insercion_fisica: Optional[date]
    finca: Optional[str]
    numero_tarea_wm: Optional[str]
    tipo: Optional[str]
    observacion: Optional[str]

class CuadroControlCreate(CuadroControlBase):
    pass

class ProduccionBase(BaseModel):
    auxiliar_id: int
    fecha_produccion: date
    empresa: Optional[str]
    actividad: Optional[str]
    unidad_medida: Optional[str]
    hora_inicio: Optional[time]
    hora_fin: Optional[time]
    cantidad_ejecutada: Optional[float]
    porcentaje_cumplimiento: Optional[float]
    observaciones: Optional[str]
    deber_ejecutar: Optional[float]
    horas_ejecutadas: Optional[float]
    estandar_h: Optional[float]

class ProduccionCreate(ProduccionBase):
    pass
