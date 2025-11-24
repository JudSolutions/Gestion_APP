from db_connection import get_connection

def enviar_notificacion(id_auxiliar, titulo, mensaje, tipo="INFO"):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO notificaciones (id_auxiliar, titulo, mensaje, tipo)
        VALUES (%s, %s, %s, %s)
    """, (id_auxiliar, titulo, mensaje, tipo))

    conn.commit()
    cur.close()
    conn.close()
