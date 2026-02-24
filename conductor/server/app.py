import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from conductor.api.routes import router, registry
from conductor.utils.config import HOST, PORT, PASSWORD, PID_FILE, ensure_dirs


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_dirs()
    PID_FILE.write_text(str(os.getpid()))
    yield
    await registry.cleanup_all()
    PID_FILE.unlink(missing_ok=True)


def create_app() -> FastAPI:
    app = FastAPI(title="Conductor", version="0.1.0", lifespan=lifespan)

    # Optional password protection
    if PASSWORD:

        @app.middleware("http")
        async def check_password(request: Request, call_next):
            # Allow static assets and the root page without auth
            if request.url.path == "/" or request.url.path.startswith("/static"):
                return await call_next(request)
            # Check bearer token
            auth = request.headers.get("Authorization", "")
            token = request.query_params.get("token", "")
            if auth == f"Bearer {PASSWORD}" or token == PASSWORD:
                return await call_next(request)
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    app.include_router(router)

    # Serve dashboard
    static_dir = Path(__file__).parent.parent.parent / "static"
    if static_dir.exists():

        @app.get("/")
        async def dashboard():
            return FileResponse(static_dir / "index.html")

        app.mount(
            "/static",
            StaticFiles(directory=str(static_dir)),
            name="static",
        )

    return app


app = create_app()


def run_server(host: str = HOST, port: int = PORT):
    import uvicorn

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
