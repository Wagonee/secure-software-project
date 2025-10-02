from datetime import date
from typing import List, Optional
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
    description: Optional[str] = Field(None, max_length=500)


class Exercise(ExerciseBase):
    id: UUID = Field(default_factory=uuid4)


class WorkoutBase(BaseModel):
    workout_date: date
    note: Optional[str] = None


class Workout(WorkoutBase):
    id: UUID = Field(default_factory=uuid4)
    sets: List[Set] = []
