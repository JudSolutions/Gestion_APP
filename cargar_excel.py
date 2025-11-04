import pandas as pd
from db_connection import get_connection

# Ruta del archivo Excel
ruta_excel = "C:\Users\USUARIO\Documents\Gestion_APP\LGDO-AG2_EOP_noviembre2025"

# Leer todas las hojas (una por auxiliar)
excel = pd.read_excel(ruta_excel, sheet_name=None)

conexion = get_connection()
cursor = conexion.cursor()

for nombre_hoja, df in excel.items():
    df = df.rename(columns={
        "AUXILIAR": "auxiliar",
        "FECHA DE PRODUCCIÓN": "fecha_produccion",
        "EMPRESA": "empresa",
        "ACTIVIDAD": "actividad",
        "UNIDAD DE MEDIDA": "unidad_medida",
        "HORA INIC H:M": "hora_inicio",
        "HORA FIN H:M": "hora_fin",
        "CANTIDAD EJECUTADA": "cantidad_ejecutada",
        "% CUMPLIMIENTO": "porcentaje_cumplimiento",
        "# CAJ/MANT": "caj_mantenimiento",
        "OBSERVACIONES": "observaciones",
        "DEBER EJECUTAR": "deber_ejecutar",
        "HORAS EJECUTADAS": "horas_ejecutadas",
        "ESTANDAR": "estandar"
    })

    for _, fila in df.iterrows():
        sql = """
        INSERT INTO produccion_auxiliar
        (auxiliar, fecha_produccion, empresa, actividad, unidad_medida, hora_inicio,
         hora_fin, cantidad_ejecutada, porcentaje_cumplimiento, caj_mantenimiento,
         observaciones, deber_ejecutar, horas_ejecutadas, estandar)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        valores = (
            str(fila.get("auxiliar")),
            fila.get("fecha_produccion"),
            str(fila.get("empresa")),
            str(fila.get("actividad")),
            str(fila.get("unidad_medida")),
            str(fila.get("hora_inicio")),
            str(fila.get("hora_fin")),
            float(fila.get("cantidad_ejecutada") or 0),
            float(str(fila.get("porcentaje_cumplimiento")).replace("%","") or 0),
            str(fila.get("caj_mantenimiento")),
            str(fila.get("observaciones")),
            float(fila.get("deber_ejecutar") or 0),
            float(fila.get("horas_ejecutadas") or 0),
            float(fila.get("estandar") or 0)
        )
        cursor.execute(sql, valores)

conexion.commit()
cursor.close()
conexion.close()
print("✅ Datos cargados correctamente en MySQL.")
