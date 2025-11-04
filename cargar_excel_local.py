#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import math
import pandas as pd
import winsound
from datetime import datetime, time
from plyer import notification  # pip install plyer

# --- Intentar usar tu módulo de conexión existente ---
try:
    from db_connection import get_connection
    HAS_DB_MODULE = True
except Exception:
    HAS_DB_MODULE = False

# --- Ruta del archivo Excel ---
ruta_excel = r"C:\Users\USUARIO\Documents\Gestion_APP\LGDO-AG2_EOP_noviembre2025.xlsm"

if not os.path.exists(ruta_excel):
    print(f"❌ El archivo no existe: {ruta_excel}")
    sys.exit(1)
else:
    print(f"✅ Archivo encontrado: {ruta_excel}")

TABLA = "produccion_auxiliar"

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLA} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    auxiliar VARCHAR(100) NOT NULL,
    fecha_produccion DATE,
    empresa VARCHAR(100),
    actividad TEXT,
    unidad_medida VARCHAR(50),
    hora_inicio TIME,
    hora_fin TIME,
    cantidad_ejecutada DECIMAL(10,2),
    porcentaje_cumplimiento DECIMAL(5,2),
    caja_mantis VARCHAR(20),
    observaciones TEXT,
    deber_ejecutar DECIMAL(10,2),
    horas_ejecutadas DECIMAL(10,2),
    estandar_h DECIMAL(10,2),
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# --- Conexión MySQL desde variables de entorno ---
def get_conn_from_env():
    import pymysql
    host = os.environ.get("MYSQL_HOST", "localhost")
    port = int(os.environ.get("MYSQL_PORT", 3306))
    user = os.environ.get("MYSQL_USER", "gestion_Admin")
    password = os.environ.get("MYSQL_PASSWORD", "Ag123456")
    db = os.environ.get("MYSQL_DB", "Gestion_Documental_AG")
    return pymysql.connect(host=host, port=port, user=user, password=password, database=db, charset='utf8mb4')

# --- Funciones auxiliares ---
def safe_parse_date(val):
    if pd.isna(val):
        return None
    if isinstance(val, (pd.Timestamp, datetime)):
        return val.date()
    try:
        d = pd.to_datetime(val, errors="coerce")
        if pd.isna(d):
            return None
        return d.date()
    except Exception:
        return None

def safe_parse_time(val):
    if pd.isna(val):
        return None
    if isinstance(val, time):
        return val
    try:
        t = pd.to_datetime(val, errors="coerce")
        if pd.isna(t):
            return None
        return t.time()
    except Exception:
        return None

def parse_percent(val):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return 0.0
    s = str(val).strip().replace("%", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0

# --- Notificaciones ---
def notificar_exito():
    winsound.MessageBeep(winsound.MB_ICONASTERISK)
    notification.notify(
        title="✅ Sincronización Exitosa",
        message="El archivo Excel se sincronizó con la base de datos.",
        timeout=5
    )

def notificar_error(error_msg):
    winsound.MessageBeep(winsound.MB_ICONHAND)
    notification.notify(
        title="❌ Error en sincronización",
        message=error_msg,
        timeout=6
    )

# --- Proceso principal ---
def sincronizar_excel_bd():
    print("📘 Leyendo hojas del archivo Excel...")
    excel = pd.read_excel(ruta_excel, sheet_name=None, engine="openpyxl")

    conn = get_connection() if HAS_DB_MODULE else get_conn_from_env()
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_SQL)
    conn.commit()

    insert_sql = f"""
    INSERT INTO {TABLA}
    (auxiliar, fecha_produccion, empresa, actividad, unidad_medida, hora_inicio,
    hora_fin, cantidad_ejecutada, porcentaje_cumplimiento, caja_mantis,
    observaciones, deber_ejecutar, horas_ejecutadas, estandar_h)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    total_insertadas = 0

    for nombre_hoja, df in excel.items():
        print(f"🔹 Procesando hoja '{nombre_hoja}' ({len(df)} filas)")

        if df.empty:
            print(f"⚠️ Hoja '{nombre_hoja}' vacía, se omite.")
            continue

        df.columns = [str(c).strip().upper() for c in df.columns]
        df["AUXILIAR"] = nombre_hoja

        mapping = {
            "FECHA DE PRODUCCIÓN": "FECHA_DE_PRODUCCION",
            "FECHA PRODUCCION": "FECHA_DE_PRODUCCION",
            "EMPRESA": "EMPRESA",
            "ACTIVIDAD": "ACTIVIDAD",
            "UNIDAD DE MEDIDA": "UNIDAD_DE_MEDIDA",
            "HORA INIC H:M": "HORA_INICIO",
            "HORA INICIO": "HORA_INICIO",
            "HORA FIN H:M": "HORA_FIN",
            "HORA FIN": "HORA_FIN",
            "CANTIDAD EJECUTADA": "CANTIDAD_EJECUTADA",
            "% CUMPLIMIENTO": "PORCENTAJE_CUMPLIMIENTO",
            "PORCENTAJE CUMPLIMIENTO": "PORCENTAJE_CUMPLIMIENTO",
            "# CAJ/MANT": "CAJA_MANTIS",
            "CAJ MANT": "CAJA_MANTIS",
            "OBSERVACIONES": "OBSERVACIONES",
            "DEBER EJECUTAR": "DEBER_EJECUTAR",
            "HORAS EJECUTADAS": "HORAS_EJECUTADAS",
            "ESTANDAR": "ESTANDAR_H"
        }

        df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
        inserts_hoja = 0

        for _, fila in df.iterrows():
            try:
                cursor.execute(insert_sql, (
                    nombre_hoja,
                    safe_parse_date(fila.get("FECHA_DE_PRODUCCION")),
                    fila.get("EMPRESA"),
                    fila.get("ACTIVIDAD"),
                    fila.get("UNIDAD_DE_MEDIDA"),
                    safe_parse_time(fila.get("HORA_INICIO")),
                    safe_parse_time(fila.get("HORA_FIN")),
                    float(fila.get("CANTIDAD_EJECUTADA") or 0),
                    parse_percent(fila.get("PORCENTAJE_CUMPLIMIENTO")),
                    fila.get("CAJA_MANTIS"),
                    fila.get("OBSERVACIONES"),
                    float(fila.get("DEBER_EJECUTAR") or 0),
                    float(fila.get("HORAS_EJECUTADAS") or 0),
                    float(fila.get("ESTANDAR_H") or 0)
                ))
                inserts_hoja += 1
            except Exception as e:
                print(f"⚠️ ERROR hoja={nombre_hoja} fila={_}: {e}")

        conn.commit()
        print(f"✅ Hoja '{nombre_hoja}': {inserts_hoja} filas insertadas.")
        total_insertadas += inserts_hoja

    cursor.close()
    conn.close()
    print(f"🎯 Total filas insertadas en MySQL: {total_insertadas}")

# --- Ejecución con notificaciones ---
if __name__ == "__main__":
    try:
        print("🔄 Sincronizando Excel con la base de datos...")
        sincronizar_excel_bd()
        notificar_exito()
    except Exception as e:
        print(f"❌ Error durante la sincronización: {e}")
        notificar_error(str(e))

