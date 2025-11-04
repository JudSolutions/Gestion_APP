import time
import os
import winsound  # Para el sonido (solo Windows)
from plyer import notification  # Para notificaciones del sistema
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from cargar_excel_local import sincronizar_excel_bd
from dotenv import load_dotenv

load_dotenv()
EXCEL_CUADRO = os.getenv("EXCEL_CUADRO")

class ExcelHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".xlsx") or event.src_path.endswith(".xlsm"):
            print(f"📁 Archivo modificado: {event.src_path}")
            sincronizar_excel_bd()

def iniciar_vigilancia():
    path = os.path.dirname(EXCEL_CUADRO)
    observer = Observer()
    observer.schedule(ExcelHandler(), path=path, recursive=False)
    observer.start()
    print("👁️ Vigilando cambios en el archivo Excel...")

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    iniciar_vigilancia()


def notificar_exito():
    winsound.MessageBeep(winsound.MB_ICONASTERISK)
    notification.notify(
        title="✅ Sincronización Exitosa",
        message="El archivo Excel se sincronizó correctamente con la base de datos.",
        timeout=5
    )

def notificar_error(error_msg):
    winsound.MessageBeep(winsound.MB_ICONHAND)
    notification.notify(
        title="❌ Error en sincronización",
        message=error_msg,
        timeout=6
    )

if __name__ == "__main__":
    try:
        print("🔄 Sincronizando Excel con la base de datos...")
        main()
        notificar_exito()
        print("✅ Sincronización completada con éxito.")
    except Exception as e:
        print(f"❌ Error durante la sincronización: {e}")
        notificar_error(str(e))