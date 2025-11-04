from database import engine

try:
    with engine.connect() as conn:
        print("✅ Conexión exitosa a MySQL")
except Exception as e:
    print("❌ Error al conectar:", e)
