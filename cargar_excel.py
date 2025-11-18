#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from db_connection import get_connection
from datetime import datetime

# 📂 Ruta del archivo Excel
ruta_excel = r"C:\Users\USUARIO\Documents\Gestion_APP\LGDO-AG2_EOP_noviembre2025.xlsm"

# --- 🔧 Funciones auxiliares ---

def limpiar_texto(valor):
    """Limpia texto: elimina NaN, None, espacios vacíos, etc."""
    if pd.isna(valor) or str(valor).strip().lower() in ["nan", "none", "nat"]:
        return None
    return str(valor).strip()

def limpiar_float(valor):
    """Convierte valores a float de forma segura."""
    if pd.isna(valor) or str(valor).strip() in ["", "nan", "None"]:
        return 0.0
    try:
        return float(str(valor).replace("%", "").replace(",", "."))
    except:
        return 0.0

def limpiar_hora(valor):
    """Convierte a formato 'HH:MM:SS' o None."""
    if pd.isna(valor) or str(valor).strip() in ["", "nan", "None"]:
        return None
    try:
        t = pd.to_datetime(valor, errors="coerce")
        if pd.isna(t):
            return None
        return t.strftime("%H:%M:%S")
    except:
        return None

def limpiar_fecha(valor):
    """Convierte fechas a formato SQL (YYYY-MM-DD) o None."""
    if pd.isna(valor) or str(valor).strip() == "":
        return None
    try:
        d = pd.to_datetime(valor, errors="coerce")
        if pd.isna(d):
            return None
        return d.strftime("%Y-%m-%d")
    except:
        return None


# --- 🔌 Conexión a la base de datos ---
conexion = get_connection()
cursor = conexion.cursor()

# --- 📊 Cargar Excel ---
excel = pd.read_excel(ruta_excel, sheet_name=None, engine="openpyxl")
total_insertadas = 0
total_omitidas = 0

try:
    for nombre_hoja, df in excel.items():
        if df.empty:
            print(f"⚠️ Hoja vacía: {nombre_hoja}")
            continue

        print(f"\n📄 Procesando hoja: {nombre_hoja} ({len(df)} filas)")

        # Normalizar nombres de columnas
        df.columns = [str(c).strip().upper() for c in df.columns]
        df = df.rename(columns={
            "AUXILIAR": "AUXILIAR",
            "FECHA DE PRODUCCIÓN": "FECHA_PRODUCCION",
            "FECHA PRODUCCION": "FECHA_PRODUCCION",
            "EMPRESA": "EMPRESA",
            "ACTIVIDAD": "ACTIVIDAD",
            "UNIDAD DE MEDIDA": "UNIDAD_MEDIDA",
            "HORA INIC H:M": "HORA_INICIO",
            "HORA INICIO": "HORA_INICIO",
            "HORA FIN H:M": "HORA_FIN",
            "HORA FIN": "HORA_FIN",
            "CANTIDAD EJECUTADA": "CANTIDAD_EJECUTADA",
            "% CUMPLIMIENTO": "PORCENTAJE_CUMPLIMIENTO",
            "# CAJA/MANTIS": "CAJA_MANTIS",
            "OBSERVACIONES": "OBSERVACIONES"
        })

        for i, fila in df.iterrows():
            try:
                auxiliar = limpiar_texto(nombre_hoja)
                fecha = limpiar_fecha(fila.get("FECHA_PRODUCCION"))
                empresa = limpiar_texto(fila.get("EMPRESA"))
                actividad = limpiar_texto(fila.get("ACTIVIDAD"))

                # 🔍 Evitar duplicados
                cursor.execute("""
                    SELECT COUNT(*) FROM produccion_auxiliar
                    WHERE auxiliar=%s AND fecha_produccion=%s AND empresa=%s AND actividad=%s
                """, (auxiliar, fecha, empresa, actividad))
                existe = cursor.fetchone()[0]
                if existe > 0:
                    total_omitidas += 1
                    continue

                # ✅ Insertar registro
                sql = """
                INSERT INTO produccion_auxiliar
                (auxiliar, fecha_produccion, empresa, actividad, unidad_medida,
                hora_inicio, hora_fin, cantidad_ejecutada, porcentaje_cumplimiento,
                caja_mantis, observaciones)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                valores = (
                    auxiliar,
                    fecha,
                    empresa,
                    actividad,  # ✅ agregado
                    limpiar_texto(fila.get("UNIDAD_MEDIDA")),
                    limpiar_hora(fila.get("HORA_INICIO")),
                    limpiar_hora(fila.get("HORA_FIN")),
                    limpiar_float(fila.get("CANTIDAD_EJECUTADA")),
                    limpiar_float(fila.get("PORCENTAJE_CUMPLIMIENTO")),
                    limpiar_texto(fila.get("CAJA_MANTIS")),
                    limpiar_texto(fila.get("OBSERVACIONES"))
                )

                cursor.execute(sql, valores)
                total_insertadas += 1

                # ⏳ Mostrar progreso cada 500 filas
                if i % 500 == 0 and i > 0:
                    print(f"   → Procesadas {i} filas...")

            except Exception as e:
                print(f"⚠️ Error en hoja '{nombre_hoja}', fila {i}: {e}")

    conexion.commit()
    print(f"\n✅ Carga finalizada: {total_insertadas} insertadas, {total_omitidas} omitidas.")

except Exception as e:
    print(f"❌ Error general: {e}")

finally:
    cursor.close()
    conexion.close()
    print("🔒 Conexión cerrada.")
