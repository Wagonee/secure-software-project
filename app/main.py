from contextlib import asynccontextmanager
from typing import List
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import schemas, services
from app.db import init_db
from app.middleware import RateLimiter

app = FastAPI(
    title="Workout Log API",
    description="API для отслеживания тренировок и упражнений.",
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
    payload = {
        "type": type_,
        "title": title,
        "status": status_code,
        "detail": detail,
        "correlation_id": cid,
    }
    if extras:
        payload.update(extras)
    return JSONResponse(payload, status_code=status_code)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return problem(
        status_code=exc.status_code,
        title=exc.detail if isinstance(exc.detail, str) else "HTTP Error",
        detail=str(exc.detail),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # return RFC7807-like response with validation errors in detail
    detail = exc.errors()
    return problem(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        title="Validation Error",
        detail=str(detail),
    )


try:
    init_db()
except Exception:
    pass

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            init_db()
        except Exception:
            pass
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
    summary="Создать новую тренировку",
)
def create_workout(workout_in: schemas.WorkoutCreate):
    return workout_service.create_workout(workout_in)


@app.get(
    "/workouts/",
    response_model=List[schemas.WorkoutRead],
    summary="Получить список всех тренировок",
)
def get_all_workouts():
    return workout_service.list_workouts()


@app.get(
    "/workouts/{workout_id}",
    response_model=schemas.WorkoutRead,
    summary="Получить одну тренировку по ID",
)
def get_workout_by_id(workout_id: UUID):
    w = workout_service.get_workout(str(workout_id))
    if not w:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found"
        )
    return w


@app.post(
    "/workouts/{workout_id}/sets",
    response_model=schemas.WorkoutRead,
    summary="Добавить подход в тренировку",
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found"
        )
    return updated


@app.post(
    "/exercises/",
    response_model=schemas.ExerciseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новое упражнение",
)
def create_exercise(exercise_in: schemas.ExerciseCreate):
    return exercise_service.create_exercise(exercise_in)


@app.get(
    "/exercises/",
    response_model=List[schemas.ExerciseRead],
    summary="Получить список всех упражнений",
)
def get_all_exercises():
    return exercise_service.list_exercises()
