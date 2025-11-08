from contextlib import asynccontextmanager
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import schemas, services
from app.db import init_db
from app.logging_config import correlation_id_ctx, get_logger, setup_logging
from app.middleware import RateLimiter

setup_logging()
logger = get_logger("main")

app = FastAPI(
    title="Workout Log API",
    description="API for tracking workouts and exercises.",
    version="0.1.0",
)


app.middleware("http")(RateLimiter())


def problem(
    status_code: int,
    title: str,
    detail: str,
    type_: str = "about:blank",
    extras: dict | None = None,
):
    cid = str(uuid4())
    correlation_id_ctx.set(cid)
    payload = {
        "type": type_,
        "title": title,
        "status": status_code,
        "detail": detail,
        "correlation_id": cid,
    }
    if extras:
        payload.update(extras)

    logger.warning(f"HTTP Error {status_code}: {title} - {detail[:100]}")
    return JSONResponse(payload, status_code=status_code)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.info(f"HTTPException caught: {exc.status_code} - {exc.detail}")
    return problem(
        status_code=exc.status_code,
        title=exc.detail if isinstance(exc.detail, str) else "HTTP Error",
        detail=str(exc.detail),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    logger.info(f"Validation error: {len(errors)} error(s)")

    detail = str(errors)
    return problem(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        title="Validation Error",
        detail=detail,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler for unexpected exceptions - mask implementation details"""
    logger.error(f"Unexpected error: {type(exc).__name__}", exc_info=True)
    return problem(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        detail="An unexpected error occurred. Please contact support.",
    )


try:
    init_db()
except Exception as e:
    logger.warning(f"Database initialization failed at startup: {e}")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            init_db()
        except Exception as e:
            logger.warning(f"Database initialization failed in lifespan: {e}")
        yield

    app.router.lifespan_context = lifespan


exercise_service = services.ExerciseService()
workout_service = services.WorkoutService()


@app.get("/health", summary="Корневой эндпоинт")
def read_root():
    return {"message": "Welcome to Workout Log API!"}


@app.post(
    "/workouts/",
    response_model=schemas.WorkoutRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create new workout",
)
def create_workout(workout_in: schemas.WorkoutCreate):
    return workout_service.create_workout(workout_in)


@app.get(
    "/workouts/",
    response_model=list[schemas.WorkoutRead],
    summary="Get all workouts",
)
def get_all_workouts():
    return workout_service.list_workouts()


@app.get(
    "/workouts/{workout_id}",
    response_model=schemas.WorkoutRead,
    summary="Get workout by ID",
)
def get_workout_by_id(workout_id: UUID):
    w = workout_service.get_workout(str(workout_id))
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    return w


@app.post(
    "/workouts/{workout_id}/sets",
    response_model=schemas.WorkoutRead,
    summary="Add set to workout",
)
def add_set_to_workout(workout_id: UUID, set_in: schemas.SetBase, exercise_id: UUID):
    exercise_obj = exercise_service.get_exercise(str(exercise_id))
    if not exercise_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found to add set",
        )

    updated = workout_service.add_set(str(workout_id), set_in, exercise_obj.name)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    return updated


@app.post(
    "/exercises/",
    response_model=schemas.ExerciseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create new exercise",
)
def create_exercise(exercise_in: schemas.ExerciseCreate):
    return exercise_service.create_exercise(exercise_in)


@app.get(
    "/exercises/",
    response_model=list[schemas.ExerciseRead],
    summary="Get all exercises",
)
def get_all_exercises():
    return exercise_service.list_exercises()
