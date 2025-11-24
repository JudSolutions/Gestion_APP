from db_connection import get_connection
from services.notificacion_service import enviar_notificacion

def reasignar(id_asignacion, id_actual_aux):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT id_auxiliar
        FROM auxiliares
        WHERE activo = 1 AND id_auxiliar <> %s
        ORDER BY capacidad_hora DESC
        LIMIT 1
    """, (id_actual_aux,))

    nuevo = cur.fetchone()

    if not nuevo:
        return False

    cur.execute("""
        UPDATE asignaciones
        SET id_auxiliar = %s
        WHERE id_asignacion = %s
    """, (nuevo["id_auxiliar"], id_asignacion))

    conn.commit()

    enviar_notificacion(
        id_actual_aux,
        "Tarea reasignada",
        "La tarea se reasignó por bajo rendimiento",
        "WARNING"
    )

    enviar_notificacion(
        nuevo["id_auxiliar"],
        "Nueva tarea asignada",
        "Se te asignó una tarea pendiente",
        "INFO"
    )

    cur.close()
    conn.close()
    return True
