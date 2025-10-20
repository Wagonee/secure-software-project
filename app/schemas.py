from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class SetBase(BaseModel):
    reps: int = Field(..., gt=0)
    weight: float = Field(..., ge=0)


class SetCreate(SetBase):
    exercise_id: str


class SetRead(SetBase):
    id: str
    exercise_name: str


class ExerciseBase(BaseModel):
    name: str
    description: Optional[str] = None


class ExerciseCreate(ExerciseBase):
    pass


class ExerciseRead(ExerciseBase):
    id: str


class WorkoutBase(BaseModel):
    workout_date: date
    note: Optional[str] = None


class WorkoutCreate(WorkoutBase):
    pass


class WorkoutRead(WorkoutBase):
    id: str
    sets: List[SetRead] = []
