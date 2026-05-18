from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.database import engine, Base
from backend import models
from backend.routers import auth, accounts, categories, transactions
from backend.logging_config import configure_logging, get_logger
from backend.exceptions import AppException

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="Finance App API")

@app.on_event("startup")
def startup():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed", exc_info=True)
        raise


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(f"{exc.__class__.__name__}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.__class__.__name__, "detail": exc.detail},
    )



# Configurar CORS para React
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://zpenz.vercel.app"],  
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
