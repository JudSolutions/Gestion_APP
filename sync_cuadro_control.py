#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import pandas as pd
import winsound
from plyer import notification
from datetime import datetime

# ===================== IMPORT DB =====================
try:
    from db_connection import get_connection
    HAS_DB = True
except:
    HAS_DB = False


def get_conn_alt():
    import pymysql
    return pymysql.connect(
        host="localhost",
        user="root",
        password="Jg1395*:",
        database="Gestion_Documental_AG",
        charset="utf8mb4"
    )


# ===================== ARCHIVO =====================

EXCEL_PATH = r"C:\Users\USUARIO\Documents\Gestion_APP\CONTROL MESES 2025.xlsx"

if not os.path.exists(EXCEL_PATH):
    print("❌ No existe el archivo:", EXCEL_PATH)
    sys.exit(1)

print("📘 Archivo encontrado:", EXCEL_PATH)

TABLA = "cuadro_control"

# ===================== MAPEO CORRECTO =====================

COLUMN_MAP = {
    "CEDULA": "cedula",
    "APELLIDOS Y NOMBRES": "apellidos_nombres",
    "TIPOLOGIA FINCA": "tipologia_finca",
    "FOLIOS": "folios",
    "SEMANA": "semana",
    "FECHA PUBLICACIÓN": "fecha_publicacion",
    "FECHA PUBLICACION": "fecha_publicacion",
    "INDEXACIÓN WM": "fecha_indexacion",
    "INDEXACION WM": "fecha_indexacion",
    "FECHA INS. FISICA (FIN)": "fecha_ins_fisica",
    "ANS": "ans_indexacion",
    "ANS FISICA": "ans_ins_fisica",
    "FINCA": "finca",
    "NUMERO TARES WM": "numero_tarea_wm",
    "NUMERO TAREA WM": "numero_tarea_wm",
    "TIPO": "tipo",
    "OBSERVACION": "observacion",
    "OBSERVACIÓN": "observacion",
}

MESES = [
    "ENERO","FEBRERO","MARZO","ABRIL","MAYO","JUNIO",
    "JULIO","AGOSTO","SEPTIEMBRE","OCTUBRE","NOVIEMBRE","DICIEMBRE"
]

# ===================== UTILS =====================

def safe_date(val):
    try:
        d = pd.to_datetime(val, errors="coerce")
        return None if pd.isna(d) else d.date()
    except:
        return None


# ===================== SINCRONIZACIÓN =====================

def sync_cuadro_control():
    excel = pd.read_excel(EXCEL_PATH, sheet_name=None, engine="openpyxl")

    conn = get_connection() if HAS_DB else get_conn_alt()
    cur = conn.cursor()

    # Hacer tabla única por tarea + cédula
    cur.execute(f"""
        ALTER TABLE {TABLA}
        ADD UNIQUE KEY idx_unique (numero_tarea_wm, cedula);
    """)
    try:
        conn.commit()
    except:
        pass

    total_insert = 0
    total_update = 0

    for hoja, df in excel.items():
        if hoja.upper() not in MESES:
            continue

        print(f"\n🔹 Procesando hoja {hoja} ({len(df)} filas)")

        df.columns = [str(c).strip().upper() for c in df.columns]
        

        df = df.iloc[9:].dropna(how='all').reset_index(drop=True)

        df = df.rename(columns={k.upper(): v for k,v in COLUMN_MAP.items() if k.upper() in df.columns})

        for i, row in df.iterrows():

            ced = str(row.get("cedula") or "").strip()
            tarea = str(row.get("numero_tarea_wm") or "").strip()

            # Si no tiene cédula ni tarea, saltar
            if ced == "" and tarea == "":
                continue

            # Verificar si ya existe el registro
            cur.execute(f"""
                SELECT id FROM {TABLA}
                WHERE numero_tarea_wm=%s AND cedula=%s
            """, (tarea, ced))
            existe = cur.fetchone()

            datos = (
                ced,
                row.get("apellidos_nombres"),
                row.get("tipologia_finca"),
                int(row.get("folios") or 0),
                int(row.get("semana") or 0),
                safe_date(row.get("fecha_publicacion")),
                safe_date(row.get("fecha_indexacion")),
                int(row.get("ans_indexacion") or 0),
                safe_date(row.get("fecha_ins_fisica")),
                int(row.get("ans_ins_fisica") or 0),
                row.get("finca"),
                tarea,
                row.get("tipo"),
                row.get("observacion"),
                hoja
            )
            print("\n----------------------------------------------")
            print("🧪 ENCABEZADOS ENCONTRADOS EN HOJA:", hoja)
            print(df.columns.tolist())
            print("----------------------------------------------")
            # ==========================================
            # INSERTAR O ACTUALIZAR
            # ==========================================
            if not existe:
                cur.execute(f"""
                    INSERT INTO {TABLA}
                    (cedula, apellidos_nombres, tipologia_finca, folios, semana,
                     fecha_publicacion, fecha_indexacion, ans_indexacion,
                     fecha_ins_fisica, ans_ins_fisica, finca, numero_tarea_wm,
                     tipo, observacion, mes)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, datos)
                total_insert += 1
            else:
                cur.execute(f"""
                    UPDATE {TABLA}
                    SET apellidos_nombres=%s, tipologia_finca=%s, folios=%s, semana=%s,
                        fecha_publicacion=%s, fecha_indexacion=%s, ans_indexacion=%s,
                        fecha_ins_fisica=%s, ans_ins_fisica=%s, finca=%s, tipo=%s,
                        observacion=%s, mes=%s
                    WHERE numero_tarea_wm=%s AND cedula=%s
                """, (
                    datos[1], datos[2], datos[3], datos[4], datos[5], datos[6],
                    datos[7], datos[8], datos[9], datos[10], datos[12], datos[13], datos[14],
                    tarea, ced
                ))
                total_update += 1

        conn.commit()
        print(f"✔ Hoja {hoja} OK")

    cur.close()
    conn.close()

    print("\n-------------------------------------")
    print(f"✔ INSERTADOS: {total_insert}")
    print(f"✔ ACTUALIZADOS: {total_update}")
    print("-------------------------------------")

    return total_insert, total_update


# ===================== EJECUCIÓN =====================

if __name__ == "__main__":
    try:
        ins, upd = sync_cuadro_control()
        notification.notify(
            title="✔ Cuadro Control sincronizado",
            message=f"Insertados: {ins} | Actualizados: {upd}",
            timeout=5
        )
        winsound.Beep(800, 300)
    except Exception as e:
        print("❌ ERROR:", e)
        notification.notify(
            title="❌ Error en sincronización",
            message=str(e),
            timeout=8
        )
        winsound.Beep(400, 600)
