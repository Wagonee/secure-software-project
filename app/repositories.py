from typing import List, Optional

from sqlalchemy.orm import Session

from app import db_models


class ExerciseRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self, name: str, description: Optional[str] = None
    ) -> db_models.Exercise:
        ex = db_models.Exercise(name=name, description=description)
        self.db.add(ex)
        self.db.commit()
        self.db.refresh(ex)
        return ex

    def list(self) -> List[db_models.Exercise]:
        return self.db.query(db_models.Exercise).all()

    def get(self, ex_id: str) -> Optional[db_models.Exercise]:
        return (
            self.db.query(db_models.Exercise)
            .filter(db_models.Exercise.id == ex_id)
            .first()
        )


class WorkoutRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, workout_date, note=None) -> db_models.Workout:
        w = db_models.Workout(workout_date=workout_date, note=note)
        self.db.add(w)
        self.db.commit()
        self.db.refresh(w)
        return w

    def list(self) -> List[db_models.Workout]:
        return self.db.query(db_models.Workout).all()

    def get(self, workout_id: str) -> Optional[db_models.Workout]:
        return (
            self.db.query(db_models.Workout)
            .filter(db_models.Workout.id == workout_id)
            .first()
        )

    def add_set(
        self, workout: db_models.Workout, reps: int, weight: float, exercise_name: str
    ):
        new_set = db_models.Set(
            reps=reps, weight=weight, exercise_name=exercise_name, workout=workout
        )
        self.db.add(new_set)
        self.db.commit()
        self.db.refresh(workout)
        return workout
