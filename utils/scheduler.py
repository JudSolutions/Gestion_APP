import time
import threading
from db_connection import get_connection
from services.prediccion_service import calcular_prediccion
from services.reasignacion_service import reasignar
from services.notificacion_service import enviar_notificacion

def ciclo():
    while True:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        # Tareas activas
        cur.execute("SELECT id_asignacion, id_auxiliar FROM asignaciones WHERE completada = 0")
        tareas = cur.fetchall()

        cur.close()
        conn.close()

        for t in tareas:
            pred = calcular_prediccion(t["id_asignacion"])

            if pred["riesgo"] == 1:
                reasignar(t["id_asignacion"], t["id_auxiliar"])

        time.sleep(600)  # 10 minutos

def iniciar_cron():
    hilo = threading.Thread(target=ciclo, daemon=True)
    hilo.start()
