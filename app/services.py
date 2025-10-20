from typing import List

from app import schemas
from app.db import SessionLocal
from app.repositories import ExerciseRepository, WorkoutRepository


class ExerciseService:
    def create_exercise(self, data: schemas.ExerciseCreate) -> schemas.ExerciseRead:
        db = SessionLocal()
        try:
            repo = ExerciseRepository(db)
            ex = repo.create(name=data.name, description=data.description)
            return schemas.ExerciseRead(
                id=ex.id, name=ex.name, description=ex.description
            )
        finally:
            db.close()

    def list_exercises(self) -> List[schemas.ExerciseRead]:
        db = SessionLocal()
        try:
            items = ExerciseRepository(db).list()
            return [
                schemas.ExerciseRead(id=i.id, name=i.name, description=i.description)
                for i in items
            ]
        finally:
            db.close()

    def get_exercise(self, ex_id: str):
        db = SessionLocal()
        try:
            ex = ExerciseRepository(db).get(ex_id)
            if not ex:
                return None
            return schemas.ExerciseRead(
                id=ex.id, name=ex.name, description=ex.description
            )
        finally:
            db.close()


class WorkoutService:
    def create_workout(self, data: schemas.WorkoutCreate) -> schemas.WorkoutRead:
        db = SessionLocal()
        try:
            repo = WorkoutRepository(db)
            w = repo.create(workout_date=data.workout_date, note=data.note)
            return schemas.WorkoutRead(
                id=w.id, workout_date=w.workout_date, note=w.note, sets=[]
            )
        finally:
            db.close()

    def list_workouts(self) -> List[schemas.WorkoutRead]:
        db = SessionLocal()
        try:
            items = WorkoutRepository(db).list()
            result = []
            for w in items:
                sets = [
                    schemas.SetRead(
                        id=s.id,
                        reps=s.reps,
                        weight=s.weight,
                        exercise_name=s.exercise_name,
                    )
                    for s in w.sets
                ]
                result.append(
                    schemas.WorkoutRead(
                        id=w.id, workout_date=w.workout_date, note=w.note, sets=sets
                    )
                )
            return result
        finally:
            db.close()

    def get_workout(self, workout_id: str):
        db = SessionLocal()
        try:
            w = WorkoutRepository(db).get(workout_id)
            if not w:
                return None
            sets = [
                schemas.SetRead(
                    id=s.id, reps=s.reps, weight=s.weight, exercise_name=s.exercise_name
                )
                for s in w.sets
            ]
            return schemas.WorkoutRead(
                id=w.id, workout_date=w.workout_date, note=w.note, sets=sets
            )
        finally:
            db.close()

    def add_set(self, workout_id: str, set_in: schemas.SetBase, exercise_name: str):
        db = SessionLocal()
        try:
            repo = WorkoutRepository(db)
            w = repo.get(workout_id)
            if not w:
                return None
            updated = repo.add_set(
                w, reps=set_in.reps, weight=set_in.weight, exercise_name=exercise_name
            )
            sets = [
                schemas.SetRead(
                    id=s.id, reps=s.reps, weight=s.weight, exercise_name=s.exercise_name
                )
                for s in updated.sets
            ]
            return schemas.WorkoutRead(
                id=updated.id,
                workout_date=updated.workout_date,
                note=updated.note,
                sets=sets,
            )
        finally:
            db.close()
