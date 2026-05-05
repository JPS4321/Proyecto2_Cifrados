from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database import get_db
from src.routes.auth import router as auth_router
from src.routes.users import router as users_router
from src.routes.messages import router as messages_router

app = FastAPI(title="Proyecto2 API")

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(messages_router)

@app.get("/")
def root():
    return {"message": "API funcionando correctamente"}

@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"message": "Conexión a PostgreSQL exitosa"}