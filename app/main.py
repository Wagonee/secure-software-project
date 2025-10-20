from typing import List
from uuid import UUID

from fastapi import FastAPI, HTTPException, status

from app import schemas, services
from app.db import init_db
from app.middleware import RateLimiter
from contextlib import asynccontextmanager

app = FastAPI(
    title="Workout Log API",
    description="API для отслеживания тренировок и упражнений.",
    version="0.1.0",
)


app.middleware("http")(RateLimiter())


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
