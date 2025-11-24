#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import math
import pandas as pd
import winsound
from datetime import datetime, time
from plyer import notification

# Intentar usar tu conexión
try:
    from db_connection import get_connection
    HAS_DB_MODULE = True
except:
    HAS_DB_MODULE = False

# Ruta del Excel
ruta_excel = r"C:\Users\USUARIO\Documents\Gestion_APP\LGDO-AG2_EOP_noviembre2025.xlsm"
ruta_excel=  r"C:\Users\USUARIO\Documents\Gestion_APP\LGDO-AG1_EOP_noviembre2025.xlsm"   

if not os.path.exists(ruta_excel):
    print(f"❌ Archivo no encontrado: {ruta_excel}")
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
);
"""

def get_conn_from_env():
    import pymysql
    return pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "localhost"),
        port=int(os.environ.get("MYSQL_PORT", 3306)),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", "Jg1395*:"),
        database=os.environ.get("MYSQL_DB", "Gestion_Documental_AG"),
        charset="utf8mb4"
    )

# ---- Parseos seguros ----
def safe_parse_date(val):
    if pd.isna(val):
        return None
    try:
        return pd.to_datetime(val, errors="coerce").date()
    except:
        return None

def safe_parse_time(val):
    if pd.isna(val):
        return None
    try:
        return pd.to_datetime(val, errors="coerce").time()
    except:
        return None

def parse_percent(val):
    if pd.isna(val):
        return 0.0
    try:
        return float(str(val).replace("%","").replace(",","."))
    except:
        return 0.0

# ---- Notificaciones ----
def notificar_exito():
    winsound.MessageBeep(winsound.MB_ICONASTERISK)
    notification.notify(title="Sincronización exitosa", message="Excel → MySQL actualizados correctamente", timeout=5)

def notificar_error(msg):
    winsound.MessageBeep(winsound.MB_ICONHAND)
    notification.notify(title="Error sincronizando", message=msg, timeout=6)

# ---- PROCESO PRINCIPAL ----
def sincronizar_excel_bd():
    print("📘 Leyendo Excel...")
    libro = pd.read_excel(ruta_excel, sheet_name=None, engine="openpyxl")

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

    for nombre_hoja, df in libro.items():
        print(f"\n🔹 Procesando hoja '{nombre_hoja}' ({len(df)} filas)")

        if df.empty:
            print("⚠️ Hoja vacía, omitida.")
            continue

        # ---- LIMPIEZA DE COLUMNAS ----
        df.columns = (
            df.columns.astype(str)
            .str.strip()
            .str.upper()
            .str.replace("\n", " ")
        )

        df = df.loc[:, ~df.columns.str.contains("UNNAMED", case=False)]
        df = df.loc[:, ~df.columns.str.contains("NAN", case=False)]
        df = df.loc[:, df.columns.notnull()]
        df = df.loc[:, df.columns != ""]

        # ---- RENOMBRE FINAL ----
        rename_map = {
            "FECHA DE PRODUCCIÓN": "FECHA_DE_PRODUCCION",
            "FECHA PRODUCCION": "FECHA_DE_PRODUCCION",
            "UNIDAD DE MEDIDA": "UNIDAD_DE_MEDIDA",
            "UNIDAD DE  MEDIDA": "UNIDAD_DE_MEDIDA",
            "HORA INICIO H:M": "HORA_INICIO",
            "HORA FIN H:M": "HORA_FIN",
            "% CUMPLIMIENTO": "PORCENTAJE_CUMPLIMIENTO",
            "# CAJA/MANTIS": "CAJA_MANTIS",
            "DEBIO EJECUTAR": "DEBER_EJECUTAR",
            "ESTANDAR/HORA": "ESTANDAR_H",
        }
        df = df.rename(columns=rename_map)

        # Añadir auxiliar
        df["AUXILIAR"] = nombre_hoja

        inserts_hoja = 0

        for _, fila in df.iterrows():

            # saltar filas vacías
            if fila.isna().all():
                continue

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
    print(f"\n🎯 Total insertadas: {total_insertadas}")

if __name__ == "__main__":
    try:
        sincronizar_excel_bd()
        notificar_exito()
    except Exception as e:
        print(f"❌ Error: {e}")
        notificar_error(str(e))

