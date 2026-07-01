from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.application.exceptions import ApplicationError
from app.core.config import settings
from app.core.database import close_mongodb_connection, connect_to_mongodb

from app.presentation.api.v1 import auth, chart_of_accounts, companies, reports, vouchers
from app.presentation.auth_dependencies import get_current_user

PUBLIC_OPERATIONS = {
    ("get", "/health"),
    ("post", f"{settings.API_V1_PREFIX}/auth/login"),
    ("post", f"{settings.API_V1_PREFIX}/auth/refresh"),
    ("post", f"{settings.API_V1_PREFIX}/user-registrations"),
}


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongodb()
    yield
    await close_mongodb_connection()


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

static_dir = Path(__file__).resolve().parent.parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.APP_TITLE,
        version=settings.APP_VERSION,
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }

    for path, path_item in openapi_schema.get("paths", {}).items():
        for method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue
            if (method.lower(), path) in PUBLIC_OPERATIONS:
                continue
            operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.exception_handler(ApplicationError)
async def application_error_handler(_: Request, exc: ApplicationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "success": False},
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.APP_TITLE, "version": settings.APP_VERSION}


protected = [Depends(get_current_user)]

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(companies.router, prefix=settings.API_V1_PREFIX, dependencies=protected)
app.include_router(chart_of_accounts.router, prefix=settings.API_V1_PREFIX, dependencies=protected)
app.include_router(vouchers.router, prefix=settings.API_V1_PREFIX, dependencies=protected)
app.include_router(reports.router, prefix=settings.API_V1_PREFIX, dependencies=protected)
