from sqlalchemy.orm import Session
import models, schemas

# ----- Cuadro de control -----
def crear_cuadro(db: Session, item: schemas.CuadroControlCreate):
    data = models.CuadroControl(**item.dict())
    db.add(data)
    db.commit()
    db.refresh(data)
    return data

def listar_cuadro(db: Session):
    return db.query(models.CuadroControl).all()

# ----- Producción -----
def crear_produccion(db: Session, item: schemas.ProduccionCreate):
    data = models.Produccion(**item.dict())
    db.add(data)
    db.commit()
    db.refresh(data)
    return data

def listar_produccion(db: Session):
    return db.query(models.Produccion).all()
