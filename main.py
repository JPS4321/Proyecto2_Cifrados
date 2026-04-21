from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.database import get_db

app = FastAPI(title="Proyecto2 API")

@app.get("/")
def root():
    return {"message": "API funcionando correctamente"}

@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"message": "Conexión a PostgreSQL exitosa"}