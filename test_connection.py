from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Cargar variables del archivo .env
load_dotenv()

# Leer la URL de conexión desde el .env
DB_URL = os.getenv("DB_URL")

if not DB_URL:
    print("❌ ERROR: No se encontró la variable DB_URL en el archivo .env")
    exit()

# Crear el motor de conexión
print(f"🔗 Intentando conectar a: {DB_URL}")
try:
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Conexión exitosa a la base de datos MySQL!")
        print("Resultado de prueba:", result.scalar())
except Exception as e:
    print("❌ Error al conectar a la base de datos:")
    print(e)
