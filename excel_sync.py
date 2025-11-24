import pandas as pd
from db_connection import get_connection
from models import CuadroControl, Produccion
import os
from dotenv import load_dotenv

load_dotenv()

EXCEL_CUADRO = os.getenv("CONTROL MESES 2025.xlsx")
EXCEL_PRODUCCION = os.getenv("LGDO-AG2_EOP_noviembre2025.xlsm")


# --- Importar cuadro de control mensual ---
def importar_cuadro():
    db = SessionLocal()
    excel = pd.ExcelFile(EXCEL_CUADRO)

    for hoja in excel.sheet_names:
        df = pd.read_excel(excel, sheet_name=hoja)
        for _, row in df.iterrows():
            if pd.isna(row.get("CEDULA")):
                continue
            registro = CuadroControl(
                cedula=str(row.get("CEDULA")),
                nombre=row.get("APELLIDOS Y NOMBRES"),
                tipologia_finca=row.get("TIPOLOGIA FINCA"),
                fecha_publicacion=row.get("FECHA PUBLICACION"),
                fecha_indizacion=row.get("INDEZACION WM"),
                fecha_insercion_fisica=row.get("FECHA INS. FISICA (FIN)"),
                finca=row.get("FINCA"),
                numero_tarea_wm=row.get("NUMERO TARES WM"),
                tipo=row.get("TIPO"),
                observacion=row.get("OBSERVACION")
            )
            db.add(registro)
    db.commit()
    db.close()
    print("✅ Cuadro mensual importado correctamente.")


# --- Exportar producción por auxiliar ---
def exportar_produccion():
    db = SessionLocal()
    data = db.query(Produccion).all()
    if not data:
        print("⚠️ No hay datos de producción para exportar.")
        return

    df = pd.DataFrame([d.__dict__ for d in data])
    df = df.drop(columns=["_sa_instance_state"], errors="ignore")

    # Escribir una hoja por auxiliar
    with pd.ExcelWriter(EXCEL_PRODUCCION, engine="openpyxl") as writer:
        for auxiliar, datos in df.groupby("auxiliar_id"):
            nombre_hoja = str(auxiliar)[:30]
            datos.to_excel(writer, sheet_name=nombre_hoja, index=False)

    print(f"✅ Archivo Excel actualizado: {EXCEL_PRODUCCION}")


# --- Sincronización automática (opcional) ---
def sincronizar_excel_bd():
    try:
        importar_cuadro()
        exportar_produccion()
        print("🔄 Sincronización completa entre Excel y base de datos.")
    except Exception as e:
        print(f"❌ Error durante la sincronización: {e}")
