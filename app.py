from flask import Flask, jsonify, render_template
from db_connection import get_connection
from datetime import datetime, date
import threading
import time

app = Flask(__name__)


# ============================================================
# FUNCIONES BÁSICAS BD
# ============================================================
def query_all(sql, params=None, dictionary=False):
    conn = get_connection()
    cur = conn.cursor(dictionary=dictionary)
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def query_one(sql, params=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def execute(sql, params=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    cur.close()
    conn.close()


# ============================================================
# DASHBOARD PRINCIPAL
# ============================================================
@app.route("/")
def dashboard():
    return render_template("dashboard.html")


# ============================================================
# TARJETAS
# ============================================================
@app.route("/api/dashboard_cards")
def dashboard_cards():

    proximas = query_one("""
        SELECT COUNT(*) 
        FROM cuadro_control 
        WHERE fecha_indexacion IS NULL OR fecha_ins_fisica IS NULL
    """)

    en_proceso = query_one("""
        SELECT COUNT(*) 
        FROM produccion_auxiliar
        WHERE fin IS NULL
    """)

    finalizadas_hoy = query_one("""
        SELECT COUNT(*) 
        FROM produccion_auxiliar
        WHERE DATE(fin) = CURDATE()
    """)

    auxiliares_activos = query_one("""
        SELECT COUNT(DISTINCT id_auxiliar)
        FROM produccion_auxiliar
        WHERE inicio >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """)

    return jsonify({
        "proximas_vencer": proximas,
        "en_proceso": en_proceso,
        "finalizadas_hoy": finalizadas_hoy,
        "auxiliares_activos": auxiliares_activos
    })


# ============================================================
# PIE TIPOLÓGIA (CUADRO CONTROL)
# ============================================================
@app.route("/api/chart_tipologia")
def chart_tipologia():
    rows = query_all("""
        SELECT tipo, COUNT(*) AS total
        FROM cuadro_control
        WHERE tipo IN ('ALTA', 'BAJA', 'INSERCION')
        GROUP BY tipo
    """)

    tipos = {"ALTA": 0, "BAJA": 0, "INSERCION": 0}
    for r in rows:
        tipos[r["tipo"]] = r["total"]

    return jsonify({
        "labels": ["ALTA", "BAJA", "INSERCION"],
        "data": [tipos["ALTA"], tipos["BAJA"], tipos["INSERCION"]]
    })


# ============================================================
# BARRAS – CARGA POR AUXILIAR
# ============================================================
@app.route("/api/chart_carga_auxiliar")
def chart_carga_auxiliar():
    rows = query_all("""
        SELECT a.nombre, 
               SUM(p.cantidad_ejecutada) AS total
        FROM produccion_auxiliar p
        JOIN auxiliares a ON p.id_auxiliar = a.id_auxiliar
        GROUP BY p.id_auxiliar
        ORDER BY total DESC
    """)

    return jsonify({
        "labels": [r["nombre"] for r in rows],
        "data": [float(r["total"]) for r in rows]
    })


# ============================================================
# AUXILIARES ACTIVOS
# ============================================================
@app.route("/api/auxiliares_activos")
def api_auxiliares_activos():
    rows = query_all("""
        SELECT a.nombre, COUNT(*) AS total
        FROM produccion_auxiliar p
        JOIN auxiliares a ON p.id_auxiliar = a.id_auxiliar
        WHERE inicio >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY p.id_auxiliar
        ORDER BY total DESC
    """)

    return jsonify([{"auxiliar": r["nombre"], "total": int(r["total"])} for r in rows])


# ============================================================
# DETALLE TAREAS AUXILIAR
# ============================================================
@app.route("/api/tareas_auxiliar/<aux>")
def api_tareas_auxiliar(aux):

    rows = query_all("""
        SELECT inicio, fin, cantidad_ejecutada, porcentaje_cumplimiento
        FROM produccion_auxiliar
        JOIN auxiliares ON auxiliares.id_auxiliar = produccion_auxiliar.id_auxiliar
        WHERE auxiliares.nombre = %s
        ORDER BY inicio DESC
    """, (aux,), dictionary=True)

    return jsonify([
        {
            "fecha": r["inicio"].strftime("%d/%m/%Y"),
            "cantidad": float(r["cantidad_ejecutada"]),
            "porcentaje": float(r["porcentaje_cumplimiento"])
        }
        for r in rows
    ])


# ============================================================
# TAREAS PENDIENTES
# ============================================================
@app.get("/api/tareas_pendientes")
def api_tareas_pendientes():
    rows = query_all("""
        SELECT 
            id,
            numero_tarea_wm,
            tipo,
            tipologia_finca,
            finca,
            fecha_publicacion,
            fecha_indexacion,
            fecha_ins_fisica,
            ans_indexacion,
            ans_ins_fisica,
            folios
        FROM cuadro_control
        ORDER BY fecha_publicacion ASC
    """, dictionary=True)

    hoy = date.today()
    pendientes = []

    for r in rows:

        # Calcular días pendientes ANS (5 días)
        fecha_pub = r["fecha_publicacion"]
        dias_rest = None

        if fecha_pub:
            diff = (hoy - fecha_pub).days
            dias_rest = 5 - diff
            if dias_rest < 0:
                dias_rest = 0

        pendientes.append({
            "id": r["id"],
            "numero": r["numero_tarea_wm"],
            "tipo": r["tipo"],
            "tipologia": r["tipologia_finca"],
            "finca": r["finca"],
            "publicacion": fecha_pub.strftime("%Y-%m-%d") if fecha_pub else "",
            "dias": dias_rest,
            "folios": r["folios"]
        })

    return jsonify(pendientes)


# ============================================================
# TAREAS CRÍTICAS
# ============================================================
@app.route("/api/tareas_criticas")
def tareas_criticas():
    rows = query_all("""
        SELECT id_produccion, cantidad_ejecutada, porcentaje_cumplimiento, inicio
        FROM produccion_auxiliar
        WHERE DATE(inicio) = CURDATE()
        ORDER BY porcentaje_cumplimiento ASC
        LIMIT 5
    """, dictionary=True)

    return jsonify([
        {
            "id": r["id_produccion"],
            "actividad": "Progreso diario",
            "fecha": r["inicio"].strftime("%d/%m"),
            "porcentaje": float(r["porcentaje_cumplimiento"])
        }
        for r in rows
    ])


# ============================================================
# SISTEMA AUTOMÁTICO DE PREDICCIÓN + ALERTAS + REASIGNACIÓN
# ============================================================
def motor_automatico():
    while True:
        try:
            # 1. Revisar tareas próximas a vencer
            criticas = query_all("""
                SELECT id, numero_tarea_wm, fecha_publicacion
                FROM cuadro_control
                WHERE fecha_indexacion IS NULL 
                  AND DATEDIFF(NOW(), fecha_publicacion) >= 4
            """)

            # Generar notificaciones
            for t in criticas:
                execute("""
                    INSERT INTO notificaciones(tipo, mensaje)
                    VALUES ('URGENTE', %s)
                """, (f"Tarea {t['numero_tarea_wm']} está por vencer.",))

        except Exception as e:
            print("⚠ Error en motor automático:", e)

        time.sleep(60)  # 🔄 se ejecuta cada 1 minuto


def iniciar_motor():
    hilo = threading.Thread(target=motor_automatico, daemon=True)
    hilo.start()


# ============================================================
# INICIO APP
# ============================================================
if __name__ == "__main__":
    iniciar_motor()
    app.run(debug=True, host="0.0.0.0")
