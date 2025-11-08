from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class SetBase(BaseModel):
    reps: int = Field(..., gt=0, le=1000)
    weight: Decimal = Field(..., ge=0, max_digits=6, decimal_places=2)


class SetCreate(SetBase):
    exercise_id: str


class SetRead(BaseModel):
    id: str
    reps: int
    weight: float
    exercise_name: str


class ExerciseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if any(ord(c) < 32 for c in v):
            raise ValueError("Name cannot contain control characters")
        return v.strip()


class ExerciseCreate(ExerciseBase):
    pass


class ExerciseRead(ExerciseBase):
    id: str


class WorkoutBase(BaseModel):
    workout_date: date
    note: str | None = Field(None, max_length=1000)

    @field_validator("note")
    @classmethod
    def validate_note(cls, v: str | None) -> str | None:
        if v is None:
            return v
        cleaned = "".join(c for c in v if ord(c) >= 32 or c in "\n\r\t")
        return cleaned.strip() if cleaned else None


class WorkoutCreate(WorkoutBase):
    pass


class WorkoutRead(WorkoutBase):
    id: str
    sets: list[SetRead] = []
