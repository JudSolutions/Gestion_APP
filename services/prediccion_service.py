import datetime
from db_connection import get_connection

def calcular_prediccion(id_asignacion):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT a.id_asignacion, a.id_auxiliar, a.cantidad_asignada,
               COALESCE(SUM(p.cantidad_ejecutada),0) AS producido,
               ac.rendimiento_hora
        FROM asignaciones a
        LEFT JOIN produccion_auxiliar p 
            ON p.id_asignacion = a.id_asignacion
        JOIN actividades_definidas ac 
            ON ac.id_actividad = a.id_actividad
        WHERE a.id_asignacion = %s
    """, (id_asignacion,))

    row = cur.fetchone()

    producido = row["producido"]
    cant_total = row["cantidad_asignada"]
    rendimiento = row["rendimiento_hora"]

    # Jornada laboral 8.8 horas
    inicio_jornada = datetime.datetime.now().replace(hour=7, minute=0)
    ahora = datetime.datetime.now()

    horas_transcurridas = max((ahora - inicio_jornada).total_seconds() / 3600, 0.1)
    horas_restantes = max(8.8 - horas_transcurridas, 0.1)

    vel_actual = producido / horas_transcurridas
    faltante = cant_total - producido
    vel_requerida = faltante / horas_restantes

    riesgo = 1 if vel_actual < vel_requerida else 0

    cur.close()
    conn.close()

    return {
        "produccion": producido,
        "faltante": faltante,
        "vel_actual": vel_actual,
        "vel_requerida": vel_requerida,
        "riesgo": riesgo
    }
