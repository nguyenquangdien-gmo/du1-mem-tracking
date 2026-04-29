from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi.staticfiles import StaticFiles
import os

from .api.v1 import api_router
from .config import get_settings
from .database import Base

settings = get_settings()

# Auto-create tables on startup (legacy, now using Alembic).
# Base.metadata.create_all(bind=engine)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run DB Migrations
    from .database import Base, engine
    from . import models # Ensure models are registered
    Base.metadata.create_all(bind=engine)
    
    from .services.scheduler import start_scheduler
    start_scheduler()
    yield

app = FastAPI(title="Member Tracking API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": detail},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {"code": "HTTP_ERROR", "message": str(detail)},
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errs = exc.errors()
    first = errs[0] if errs else {}
    field = ".".join(str(x) for x in first.get("loc", []) if x != "body")
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": first.get("msg", "Input không hợp lệ"),
                "field": field or None,
                "errors": errs,
            },
        },
    )


@app.get("/health")
def health():
    from .database import engine
    from sqlalchemy import text
    
    db_status = "ok"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    return {
        "success": db_status == "ok", 
        "data": {
            "status": "ok" if db_status == "ok" else "degraded",
            "database": db_status
        }
    }

app.include_router(api_router)


# Serve Frontend Static Files
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

