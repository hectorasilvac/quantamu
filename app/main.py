from fastapi import FastAPI
from app.api.endpoints import market_data

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "¡Bienvenido a la API!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Rutas para Market Data
app.include_router(market_data.router, prefix="/api", tags=["Market Data"])