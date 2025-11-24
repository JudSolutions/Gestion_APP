#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from datetime import date, timedelta, datetime

from flask import Flask, render_template, jsonify
from db_connection import get_connection   # ya lo tienes creado

app = Flask(__name__)

# ================== CARGAR FESTIVOS COLOMBIA ==================
RUTA_BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_FESTIVOS = os.path.join(RUTA_BASE, "festivos_colombia.json")

FESTIVOS = set()
if os.path.exists(RUTA_FESTIVOS):
    try:
        with open(RUTA_FESTIVOS, "r", encoding="utf-8") as f:
            data_festivos = json.load(f)
        # suponemos lista de "YYYY-MM-DD"
        for s in data_festivos:
            try:
                FESTIVOS.add(date.fromisoformat(s))
            except Exception:
                pass
    except Exception as e:
        print("⚠️ No se pudieron cargar festivos_colombia.json:", e)
else:
    print("⚠️ No se encontró festivos_colombia.json, se contarán solo días hábiles sin festivos.")


# ================== HELPERS BD ==================
def query_one(sql, params=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


def query_all(sql, params=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ================== HELPERS FECHAS ==================
def business_days_between(d1: date, d2: date) -> int:
    """
    Días hábiles entre d1 y d2 (sin incluir d1, incluyendo d2 si aplica).
    No cuenta sábados, domingos ni festivos.
    Si d2 < d1 devuelve número negativo.
    """
    if d1 is None or d2 is None:
        return 0

    sign = 1
    if d2 < d1:
        d1, d2 = d2, d1
        sign = -1

    days = 0
    current = d1 + timedelta(days=1)  # empezamos después de d1
    while current <= d2:
        if current.weekday() < 5 and current not in FESTIVOS:
            days += 1
        current += timedelta(days=1)
    return sign * days


def hoy():
    return date.today()


# ================== VISTA PRINCIPAL ==================
@app.route("/")
def dashboard():
    # usa templates/dashboard.html (ya lo tienes)
    return render_template("dashboard.html")


# ================== LÓGICA TAREAS PENDIENTES (CUADRO CONTROL) ==================
def obtener_tareas_pendientes():
    """
    Lee cuadro_control y calcula:
      - días hábiles transcurridos desde FECHA_PUBLICACION
      - días restantes hasta el vencimiento (por defecto ans=5 si viene NULL)
      - define estado: 'proxima', 'vencida', 'ok'
    Solo considera registros donde:
      - numero_tarea_wm NO ES NULL
      - (fecha_indexacion IS NULL o fecha_ins_fisica IS NULL)
    """

    rows = query_all("""
        SELECT 
            id,
            cedula,
            apellidos_nombres,
            tipologia_finca,
            folios,
            semana,
            fecha_publicacion,
            fecha_indexacion,
            ans_indexacion,
            fecha_ins_fisica,
            ans_ins_fisica,
            finca,
            numero_tarea_wm,
            tipo
        FROM cuadro_control
        WHERE numero_tarea_wm IS NOT NULL
          AND (fecha_indexacion IS NULL OR fecha_ins_fisica IS NULL)
    """)

    hoy_d = hoy()
    tareas = []

    for r in rows:
        (
            id_cc,
            cedula,
            nombres,
            tipologia_finca,
            folios,
            semana,
            f_pub,
            f_index,
            ans_idx,
            f_fisica,
            ans_fis,
            finca,
            num_tarea,
            tipo
        ) = r

        # Convertir fechas a date
        if isinstance(f_pub, datetime):
            f_pub = f_pub.date()
        if isinstance(f_index, datetime):
            f_index = f_index.date()
        if isinstance(f_fisica, datetime):
            f_fisica = f_fisica.date()

        # ANS: si viene NULL, tomamos 5 por defecto
        ans_idx = ans_idx or 5
        ans_fis = ans_fis or 5

        # Vencimientos teóricos
        venc_index = f_pub + timedelta(days=ans_idx) if f_pub else None
        venc_fisica = f_pub + timedelta(days=ans_fis) if f_pub else None

        # Días hábiles transcurridos desde FECHA_PUBLICACION
        dias_habiles_trans = business_days_between(f_pub, hoy_d) if f_pub else 0

        # Días restantes a cada ANS
        dias_rest_index = business_days_between(hoy_d, venc_index) if venc_index else 0
        dias_rest_fis = business_days_between(hoy_d, venc_fisica) if venc_fisica else 0

        # Tomamos el peor caso (el más crítico)
        dias_restantes = min(dias_rest_index, dias_rest_fis)

        if dias_restantes < 0:
            estado = "vencida"
        elif dias_restantes <= 2:
            estado = "proxima"
        else:
            estado = "ok"

        tareas.append({
            "id": id_cc,
            "cedula": cedula,
            "nombres": nombres,
            "tipologia_finca": tipologia_finca,
            "folios": folios,
            "semana": semana,
            "fecha_publicacion": f_pub.strftime("%d/%m/%Y") if f_pub else "",
            "fecha_indexacion": f_index.strftime("%d/%m/%Y") if f_index else "",
            "fecha_ins_fisica": f_fisica.strftime("%d/%m/%Y") if f_fisica else "",
            "ans_indexacion": ans_idx,
            "ans_ins_fisica": ans_fis,
            "finca": finca,
            "numero_tarea_wm": num_tarea,
            "tipo": tipo,
            "dias_habiles_transcurridos": dias_habiles_trans,
            "dias_restantes": dias_restantes,
            "estado": estado
        })

    return tareas


# ================== API: TARJETAS RESUMEN DASHBOARD ==================
@app.route("/api/dashboard_cards")
def dashboard_cards():
    cards = {}

    # 1) Próximas a vencer: tareas del cuadro de control con estado "proxima"
    tareas = obtener_tareas_pendientes()
    cards["proximas_vencer"] = sum(1 for t in tareas if t["estado"] == "proxima")

    # 2) En proceso: cantidad de registros de produccion_auxiliar de hoy sin hora_fin
    cards["en_proceso"] = query_one("""
        SELECT COUNT(*) FROM produccion_auxiliar
        WHERE fecha_produccion = CURDATE()
          AND (hora_fin IS NULL OR hora_fin = '00:00:00')
    """) or 0

    # 3) Finalizadas hoy: produccion_auxiliar de hoy con hora_fin llena
    cards["finalizadas_hoy"] = query_one("""
        SELECT COUNT(*) FROM produccion_auxiliar
        WHERE fecha_produccion = CURDATE()
          AND hora_fin IS NOT NULL
          AND hora_fin <> '00:00:00'
    """) or 0

    # 4) Auxiliares activos últimos 7 días
    cards["auxiliares_activos"] = query_one("""
        SELECT COUNT(DISTINCT auxiliar)
        FROM produccion_auxiliar
        WHERE fecha_produccion >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
    """) or 0

    return jsonify(cards)


# ================== API: TAREAS PENDIENTES DETALLADAS ==================
@app.route("/api/tareas_pendientes")
def api_tareas_pendientes():
    """
    Devuelve la lista de tareas de cuadro_control que aún no tienen
    fecha_indexacion o fecha_ins_fisica, con días hábiles y estado.
    Esto lo puedes mostrar en una tabla tipo 'Tareas críticas'.
    """
    tareas = obtener_tareas_pendientes()

    # ordenamos por estado y luego por días_restantes
    tareas = sorted(
        tareas,
        key=lambda t: (0 if t["estado"] == "vencida" else 1 if t["estado"] == "proxima" else 2,
                       t["dias_restantes"])
    )
    return jsonify(tareas)


# ================== API: GRAFICO POR TIPOLOGIA (USANDO PRODUCCION) ==================
@app.route("/api/chart_tipologia")
def chart_tipologia():
    """
    Usa produccion_auxiliar.actividad para clasificar en:
    ALTAS, BAJAS, INSERCIONES, OTROS
    """
    rows = query_all("""
        SELECT LOWER(actividad)
        FROM produccion_auxiliar
        WHERE fecha_produccion >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    """)

    altas = bajas = inserciones = otros = 0
    for (actividad,) in rows:
        if not actividad:
            continue
        if "alta" in actividad:
            altas += 1
        elif "baja" in actividad:
            bajas += 1
        elif "insercion" in actividad or "inserción" in actividad:
            inserciones += 1
        else:
            otros += 1

    return jsonify({
        "labels": ["ALTAS", "BAJAS", "INSERCIONES", "OTROS"],
        "data": [altas, bajas, inserciones, otros]
    })


# ================== API: GRAFICO CARGA POR AUXILIAR ==================
@app.route("/api/chart_carga_auxiliar")
def chart_carga_auxiliar():
    rows = query_all("""
        SELECT auxiliar, SUM(cantidad_ejecutada)
        FROM produccion_auxiliar
        WHERE fecha_produccion = CURDATE()
        GROUP BY auxiliar
        ORDER BY SUM(cantidad_ejecutada) DESC
        LIMIT 6
    """)

    return jsonify({
        "labels": [r[0] for r in rows],
        "data": [float(r[1]) if r[1] else 0 for r in rows]
    })


# ================== API: TAREAS CRÍTICAS (BARRA INFERIOR) ==================
@app.route("/api/tareas_criticas")
def tareas_criticas():
    """
    Tareas del cuadro de control que ya están vencidas o
    muy cerca de vencerse (estado 'vencida' o 'proxima'),
    ordenadas por mayor criticidad.
    """
    tareas = obtener_tareas_pendientes()
    criticas = [t for t in tareas if t["estado"] in ("vencida", "proxima")]

    # limitamos por si quieres mostrar solo las 10 más críticas
    criticas = sorted(criticas, key=lambda t: (t["estado"] != "vencida", t["dias_restantes"]))[:10]

    # adaptamos estructura simple para el front
    resp = []
    for t in criticas:
        resp.append({
            "id": t["id"],
            "numero_tarea": t["numero_tarea_wm"],
            "tipo": t["tipo"],
            "tipologia_finca": t["tipologia_finca"],
            "fecha_publicacion": t["fecha_publicacion"],
            "finca": t["finca"],
            "estado": t["estado"],
            "dias_restantes": t["dias_restantes"],
        })

    return jsonify(resp)


# ================== API: AUXILIARES ACTIVOS ==================
@app.route("/api/auxiliares_activos")
def api_auxiliares_activos():
    rows = query_all("""
        SELECT auxiliar, COUNT(*) AS total
        FROM produccion_auxiliar
        WHERE fecha_produccion >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY auxiliar
        ORDER BY total DESC
    """)
    return jsonify([
        {"auxiliar": r[0], "total": int(r[1])}
        for r in rows if r[0]
    ])


# ================== API: TAREAS POR AUXILIAR ==================
@app.route("/api/tareas_auxiliar/<nombre>")
def api_tareas_auxiliar(nombre):
    rows = query_all("""
        SELECT fecha_produccion, actividad, cantidad_ejecutada, porcentaje_cumplimiento
        FROM produccion_auxiliar
        WHERE auxiliar = %s
          AND fecha_produccion >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        ORDER BY fecha_produccion DESC
    """, (nombre,))

    tareas = []
    for r in rows:
        f = r[0]
        if isinstance(f, datetime):
            f = f.date()
        tareas.append({
            "fecha": f.strftime("%d/%m/%Y") if f else "",
            "actividad": r[1] or "",
            "cantidad": float(r[2]) if r[2] else 0,
            "porcentaje": float(r[3]) if r[3] else 0
        })

    return jsonify(tareas)


# ================== MAIN ==================
if __name__ == "__main__":
    # puedes cambiar a host="0.0.0.0" si lo vas a ver en otra máquina
    app.run(debug=True, host="0.0.0.0", port=5000)
