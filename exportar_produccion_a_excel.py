"""
exportar_produccion_a_excel.py

Exporta registros de la tabla `produccion_auxiliar` (MySQL) a un libro Excel con
una hoja por auxiliar. Cada ejecución reemplaza la hoja del auxiliar con los
registros actuales (evita duplicados).

Requisitos:
 pip install pandas openpyxl mysql-connector-python python-dotenv

Uso:
 python exportar_produccion_a_excel.py
"""

import os
from datetime import datetime
import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()  # busca .env en la misma carpeta

# Configuración desde .env (o edita aquí directamente)
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASS = os.getenv("MYSQL_PASSWORD", "Jg1395*:")
DB_NAME = os.getenv("MYSQL_DB", "Gestion_Documental_AG")
EXCEL_PATH = os.getenv("EXCEL_PRODUCCION_PATH", "Produccion_Auxiliares.xlsx")
# Opcional: si quieres un backup por ejecución
BACKUP_FOLDER = os.getenv("EXCEL_BACKUP_FOLDER", "backups")

# Asegurarse que exista carpeta de backups
os.makedirs(BACKUP_FOLDER, exist_ok=True)

SQL_QUERY = """
SELECT
  id,
  auxiliar,
  fecha_produccion,
  empresa,
  actividad,
  unidad_medida,
  hora_inicio,
  hora_fin,
  cantidad_ejecutada,
  porcentaje_cumplimiento,
  caja_mantis,
  observaciones,
  deber_ejecutar,
  horas_ejecutadas,
  estandar_h
FROM produccion_auxiliar
ORDER BY auxiliar, fecha_produccion, hora_inicio;
"""

# Mapeo de columnas para Excel (orden y nombres que aparecerán)
COLUMNS_ORDER = [
    "auxiliar",
    "fecha_produccion",
    "empresa",
    "actividad",
    "unidad_medida",
    "hora_inicio",
    "hora_fin",
    "cantidad_ejecutada",
    "porcentaje_cumplimiento",
    "caja_mantis",
    "observaciones",
    "deber_ejecutar",
    "horas_ejecutadas",
    "estandar_h"
]

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            auth_plugin='mysql_native_password'  # opcional según tu MySQL
        )
        return conn
    except Error as e:
        print("Error conectando a la base de datos:", e)
        raise

def fetch_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(SQL_QUERY)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def normalize_dataframe(rows):
    # Convertir en DataFrame y normalizar nombres/formatos
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Convertir datetime/times a formatos legibles en Excel
    # Asumimos que fecha_produccion es date o datetime, hora_inicio/hora_fin time/datetime/str
    if "fecha_produccion" in df.columns:
        df["fecha_produccion"] = pd.to_datetime(df["fecha_produccion"]).dt.date

    if "hora_inicio" in df.columns:
        df["hora_inicio"] = pd.to_datetime(df["hora_inicio"], errors="coerce").dt.time

    if "hora_fin" in df.columns:
        df["hora_fin"] = pd.to_datetime(df["hora_fin"], errors="coerce").dt.time

    # Normalizar porcentaje (si viene como 0.96 -> mostrar 96)
    if "porcentaje_cumplimiento" in df.columns:
        # Si el porcentaje está en 0..1 lo convertimos a 0..100
        df["porcentaje_cumplimiento"] = df["porcentaje_cumplimiento"].apply(
            lambda x: (float(x) * 100) if (x is not None and 0 <= float(x) <= 1) else x
        )

    # Orden y columnas deseadas; si faltan columnas, llenar con NaN
    for col in COLUMNS_ORDER:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[COLUMNS_ORDER]

    return df

def sheet_name_from_aux(aux_name):
    # Excel limita 31 caracteres para el nombre de hoja
    if aux_name is None:
        return "SinNombre"
    name = str(aux_name).strip()
    return name[:31]

def export_to_excel(df):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Hacer backup del archivo existente (si existe)
    if os.path.exists(EXCEL_PATH):
        backup_name = os.path.join(BACKUP_FOLDER, f"Produccion_Auxiliares_{timestamp}.xlsx")
        try:
            # copiar archivo
            from shutil import copyfile
            copyfile(EXCEL_PATH, backup_name)
            print(f"Backup creado: {backup_name}")
        except Exception as e:
            print("No se pudo crear backup:", e)

    # Agrupar por auxiliar y escribir hoja por auxiliar
    if df.empty:
        print("No hay registros para exportar.")
        # aún así, crear (o mantener) el archivo vacío si no existe
        if not os.path.exists(EXCEL_PATH):
            pd.DataFrame(columns=COLUMNS_ORDER).to_excel(EXCEL_PATH, sheet_name="Resumen", index=False)
        return

    # Pandas >= 1.3 soporta if_sheet_exists. Usaremos mode='a' si queremos mantener otras hojas,
    # pero como queremos reemplazar cada hoja del auxiliar, lo más sencillo es: crear un nuevo libro
    # y escribir todas las hojas desde cero (evita problemas con hojas existentes).
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
        # Opcional: hoja resumen con conteos
        resumen = df.groupby("auxiliar").size().reset_index(name="registros")
        resumen.to_excel(writer, sheet_name="BD_Consolidado", index=False)

        for auxiliar, grupo in df.groupby("auxiliar"):
            sheet = sheet_name_from_aux(auxiliar)
            # Si quieres convertir tipos (por ejemplo % con símbolo), puedes prepararlo
            g = grupo.copy()
            # Formateos adicionales (por ejemplo, porcentaje con 2 decimales)
            if "porcentaje_cumplimiento" in g.columns:
                g["porcentaje_cumplimiento"] = g["porcentaje_cumplimiento"].apply(lambda x: round(float(x),2) if pd.notna(x) else x)

            g.to_excel(writer, sheet_name=sheet, index=False)

    print(f"✅ Archivo exportado correctamente: {EXCEL_PATH}")

def main():
    print("Consultando base de datos...")
    rows = fetch_data()
    df = normalize_dataframe(rows)
    export_to_excel(df)

if __name__ == "__main__":
    main()
