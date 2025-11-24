from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from db_connection import get_connection
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "super_secreto_cambialo"
CORS(app)  # si accedes desde otro dominio

# ---------- Helpers DB ----------
def query_all(sql, params=None, dict_cursor=False):
    conn = get_connection()
    cur = conn.cursor(dictionary=dict_cursor)
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def execute_sql(sql, params=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    last_id = cur.lastrowid
    cur.close()
    conn.close()
    return last_id

# ---------- LOGIN ----------
@app.post("/api/login")
def login():
    data = request.json
    usuario = data.get("usuario")
    password = data.get("password")

    rows = query_all(
        "SELECT * FROM auxiliares WHERE usuario=%s AND activo=1",
        (usuario,), dict_cursor=True
    )
    if not rows:
        return jsonify({"ok": False, "msg": "Usuario no encontrado"}), 401

    aux = rows[0]
    if not check_password_hash(aux["password_hash"], password):
        return jsonify({"ok": False, "msg": "Contraseña incorrecta"}), 401

    # guardamos en sesión
    session["id_auxiliar"] = aux["id"]
    session["nombre_aux"] = aux["nombre"]
    return jsonify({"ok": True, "nombre": aux["nombre"]})


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})

def require_login():
    if "id_auxiliar" not in session:
        return None
    return session["id_auxiliar"]

# ---------- TAREAS DISPONIBLES DESDE CUADRO_CONTROL ----------
@app.get("/api/tareas_disponibles")
def tareas_disponibles():
    id_aux = require_login()
    if not id_aux:
        return jsonify({"ok": False, "msg": "No autenticado"}), 401

    tipologia = request.args.get("tipologia")  # ALTA, BAJA, INSERCION, opcional

    sql = """
        SELECT id, numero_tarea_wm, tipo, tipologia_finca, finca, fecha_publicacion
        FROM cuadro_control
        WHERE (fecha_indexacion IS NULL OR fecha_ins_fisica IS NULL)
    """
    params = []
    if tipologia:
        sql += " AND tipo = %s"
        params.append(tipologia)

    sql += " ORDER BY fecha_publicacion ASC LIMIT 100"
    rows = query_all(sql, params, dict_cursor=True)
    return jsonify(rows)

# ---------- ACTIVIDADES POR TIPOLOGÍA ----------
@app.get("/api/actividades")
def actividades():
    id_aux = require_login()
    if not id_aux:
        return jsonify({"ok": False, "msg": "No autenticado"}), 401

    tipologia = request.args.get("tipologia")  # ALTA / BAJA / INSERCION
    rows = query_all(
        "SELECT id, codigo, nombre, alias_corto, rendimiento_hora "
        "FROM actividades_definidas WHERE tipologia=%s",
        (tipologia,), dict_cursor=True
    )
    return jsonify(rows)

# ---------- INICIAR REGISTRO DE ACTIVIDAD ----------
@app.post("/api/actividad/inicio")
def actividad_inicio():
    id_aux = require_login()
    if not id_aux:
        return jsonify({"ok": False, "msg": "No autenticado"}), 401

    data = request.json
    id_tarea = data["id_tarea_cuadro"]
    id_act = data["id_actividad"]

    # traemos info de la tarea para copiar a produccion_auxiliar
    tarea = query_all(
        "SELECT numero_tarea_wm, tipo, tipologia_finca, finca "
        "FROM cuadro_control WHERE id=%s",
        (id_tarea,), dict_cursor=True
    )
    if not tarea:
        return jsonify({"ok": False, "msg": "Tarea no encontrada"}), 400
    t = tarea[0]

    now = datetime.now()

    sql = """
    INSERT INTO produccion_auxiliar
    (auxiliar, id_auxiliar, id_actividad, id_tarea_cuadro,
     numero_tarea_wm, tipo, tipologia_finca,
     fecha_produccion, hora_inicio, empresa, actividad)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    # auxiliar (texto) = nombre, empresa puedes usar 'GR CHIA S.A.S.' o la que sea fija
    aux_nombre = session.get("nombre_aux")
    empresa = "GR CHIA S.A.S."

    # nombre de la actividad desde actividades_definidas
    act = query_all("SELECT alias_corto FROM actividades_definidas WHERE id=%s",
                    (id_act,), dict_cursor=True)[0]

    id_reg = execute_sql(sql, (
        aux_nombre,
        id_aux,
        id_act,
        id_tarea,
        t["numero_tarea_wm"],
        t["tipo"],
        t["tipologia_finca"],
        now.date(),
        now.time().replace(microsecond=0),
        empresa,
        act["alias_corto"]
    ))

    return jsonify({"ok": True, "id_registro": id_reg})

# ---------- CERRAR ACTIVIDAD ----------
@app.post("/api/actividad/fin")
def actividad_fin():
    id_aux = require_login()
    if not id_aux:
        return jsonify({"ok": False, "msg": "No autenticado"}), 401

    data = request.json
    id_reg = data["id_registro"]
    cantidad = float(data.get("cantidad", 0))

    # traemos la actividad para saber rendimiento_hora
    row = query_all(
        "SELECT pa.fecha_produccion, pa.hora_inicio, ad.rendimiento_hora "
        "FROM produccion_auxiliar pa "
        "JOIN actividades_definidas ad ON pa.id_actividad = ad.id "
        "WHERE pa.id=%s",
        (id_reg,), dict_cursor=True
    )

    if not row:
        return jsonify({"ok": False, "msg": "Registro no encontrado"}), 400

    r = row[0]
    now = datetime.now()
    # calculamos horas ejecutadas
    inicio_dt = datetime.combine(r["fecha_produccion"], r["hora_inicio"])
    horas_ej = (now - inicio_dt).total_seconds() / 3600.0
    deber = r["rendimiento_hora"] * horas_ej
    porc = 0 if deber == 0 else (cantidad / deber) * 100

    sql = """
    UPDATE produccion_auxiliar
    SET hora_fin=%s,
        cantidad_ejecutada=%s,
        horas_ejecutadas=%s,
        deber_ejecutar=%s,
        estandar_h=%s,
        porcentaje_cumplimiento=%s
    WHERE id=%s
    """

    execute_sql(sql, (
        now.time().replace(microsecond=0),
        cantidad,
        horas_ej,
        deber,
        r["rendimiento_hora"],
        porc,
        id_reg
    ))

    return jsonify({"ok": True, "porcentaje": porc})
