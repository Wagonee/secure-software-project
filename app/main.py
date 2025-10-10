from typing import List
from uuid import UUID

from app.middleware import RateLimiter
from fastapi import FastAPI, HTTPException, status

from .models import Exercise, ExerciseBase, Set, SetBase, Workout, WorkoutBase

app = FastAPI(
    title="Workout Log API",
    description="API для отслеживания тренировок и упражнений.",
    version="0.1.0",
)
app.middleware("http")(RateLimiter())

db_workouts: List[Workout] = []
db_exercises: List[Exercise] = []


@app.get("/health", summary="Корневой эндпоинт")
def read_root():
    return {"message": "Welcome to Workout Log API!"}


@app.post(
    "/workouts/",
    response_model=Workout,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую тренировку",
)
def create_workout(workout_in: WorkoutBase):
    new_workout = Workout(**workout_in.model_dump())
    db_workouts.append(new_workout)
    return new_workout


@app.get(
    "/workouts/",
    response_model=List[Workout],
    summary="Получить список всех тренировок",
)
def get_all_workouts():
    return db_workouts


@app.get(
    "/workouts/{workout_id}",
    response_model=Workout,
    summary="Получить одну тренировку по ID",
)
def get_workout_by_id(workout_id: UUID):
    for workout in db_workouts:
        if workout.id == workout_id:
            return workout
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found"
    )


@app.post(
    "/workouts/{workout_id}/sets",
    response_model=Workout,
    summary="Добавить подход в тренировку",
)
def add_set_to_workout(workout_id: UUID, set_in: SetBase, exercise_id: UUID):
    workout = None
    for w in db_workouts:
        if w.id == workout_id:
            workout = w
            break
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found"
        )

    exercise = None
    for ex in db_exercises:
        if ex.id == exercise_id:
            exercise = ex
            break
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found to add set",
        )

    new_set = Set(**set_in.model_dump(), exercise_name=exercise.name)
    workout.sets.append(new_set)
    return workout


@app.post(
    "/exercises/",
    response_model=Exercise,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новое упражнение",
)
def create_exercise(exercise_in: ExerciseBase):
    new_exercise = Exercise(**exercise_in.model_dump())
    db_exercises.append(new_exercise)
    return new_exercise


@app.get(
    "/exercises/",
    response_model=List[Exercise],
    summary="Получить список всех упражнений",
)
def get_all_exercises():
    return db_exercises
