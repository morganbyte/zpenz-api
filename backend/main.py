from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base
from backend import models
from backend.routers import auth, accounts, categories, transactions

app = FastAPI(title="Finance App API")

@app.on_event("startup")
def startup():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Fallo al iniciar la base de datos:", e)



# Configurar CORS para React
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://zpenz-94s6exdyu-morgancacm-gmailcoms-projects.vercel.app"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(transactions.router)

@app.get("/")
def read_root():
    return {"message": "Finance API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
