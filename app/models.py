from datetime import date
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SetBase(BaseModel):
    reps: int = Field(..., gt=0, description="Количество повторений")
    weight: float = Field(..., ge=0, description="Вес в килограммах")


class Set(SetBase):
    id: UUID = Field(default_factory=uuid4)
    exercise_name: str


class ExerciseBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)


class Exercise(ExerciseBase):
    id: UUID = Field(default_factory=uuid4)


class WorkoutBase(BaseModel):
    workout_date: date
    note: str | None = None


class Workout(WorkoutBase):
    id: UUID = Field(default_factory=uuid4)
    sets: list[Set] = []
