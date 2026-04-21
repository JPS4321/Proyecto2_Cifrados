from fastapi import FastAPI
from src.routes.auth import router as auth_router
from src.routes.users import router as users_router

app = FastAPI(title="Proyecto2 API")

app.include_router(auth_router)
app.include_router(users_router)

@app.get("/")
def root():
    return {"message": "API funcionando correctamente"}