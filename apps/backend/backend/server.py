from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from backend.database import create_test_dyad, engine
from py_database.database import create_db_and_tables
from backend.routers import dyad


@asynccontextmanager
async def server_lifespan(app: FastAPI):
    print("Server launched.")
    await create_db_and_tables(engine)
    await create_test_dyad()

    yield

    # Cleanup logic will come below.

app = FastAPI(lifespan=server_lifespan)

# Setup routers
app.include_router(
    dyad.router,
    prefix="/api/v1/dyad"
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
    # or logger.error(f'{exc}')
    print(request, exc_str)
    content = {'status_code': 10422, 'message': exc_str, 'data': None}
    return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

# Setup middlewares
origins = [
    "http://localhost:3000",
    "localhost:3000",
    "http://localhost:8000",
    "localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-processing-time", "X-request-id", "X-context-id"]
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = perf_counter()
    response = await call_next(request)
    end = perf_counter()
    response.headers["X-processing-time"] = str(end - start)
    return response


@app.middleware("http")
async def pass_request_ids_header(request: Request, call_next):
    response = await call_next(request)

    if "X-request-id" in request.headers:
        response.headers["X-request-id"] = request.headers["x-request-id"]

    if "X-context-id" in request.headers:
        response.headers["X-context-id"] = request.headers["x-context-id"]

    return response

@app.get("/ping")
def ping()->str:
    return "Server is working."