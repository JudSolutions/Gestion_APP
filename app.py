from flask import Flask, request, jsonify
from db_connection import get_connection

app = Flask(__name__)

@app.route("/produccion", methods=["GET"])
def obtener_produccion():
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM produccion_auxiliar")
    datos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return jsonify(datos)

@app.route("/produccion", methods=["POST"])
def agregar_produccion():
    data = request.get_json()
    conexion = get_connection()
    cursor = conexion.cursor()
    sql = """
    INSERT INTO produccion_auxiliar
    (auxiliar, fecha_produccion, empresa, actividad, unidad_medida, hora_inicio,
     hora_fin, cantidad_ejecutada, porcentaje_cumplimiento, caj_mantenimiento,
     observaciones, deber_ejecutar, horas_ejecutadas, estandar)
    VALUES (%(auxiliar)s, %(fecha_produccion)s, %(empresa)s, %(actividad)s,
            %(unidad_medida)s, %(hora_inicio)s, %(hora_fin)s, %(cantidad_ejecutada)s,
            %(porcentaje_cumplimiento)s, %(caj_mantenimiento)s, %(observaciones)s,
            %(deber_ejecutar)s, %(horas_ejecutadas)s, %(estandar)s)
    """
    cursor.execute(sql, data)
    conexion.commit()
    cursor.close()
    conexion.close()
    return jsonify({"mensaje": "Registro agregado correctamente"}), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
