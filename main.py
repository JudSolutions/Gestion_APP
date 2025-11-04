import flet as ft
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import models, schemas, crud  # ✅ sin punto inicial
from database import engine, SessionLocal  # ✅ importación directa

# --- Inicializa la base de datos ---
models.Base.metadata.create_all(bind=engine)

# --- App FastAPI ---
app = FastAPI(title="Gestión Documental AG")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"mensaje": "App de Gestión conectada correctamente ✅"}

@app.get("/cuadro/", response_model=list[schemas.CuadroControlBase])
def listar_cuadro(db: Session = Depends(get_db)):
    return crud.listar_cuadro(db)

@app.post("/produccion/", response_model=schemas.ProduccionBase)
def crear_produccion(item: schemas.ProduccionCreate, db: Session = Depends(get_db)):
    return crud.crear_produccion(db, item)

@app.get("/produccion/", response_model=list[schemas.ProduccionBase])
def listar_produccion(db: Session = Depends(get_db)):
    return crud.listar_produccion(db)

# --- Interfaz Flet ---
def main(page: ft.Page):
    page.title = "Gestión Documental AG"
    page.add(
        ft.Text("Bienvenidos a Archivo de Gestión", color="green")
    )
    page.update()

# --- Ejecutar Flet ---
if __name__ == "__main__":
    ft.app(target=main)
