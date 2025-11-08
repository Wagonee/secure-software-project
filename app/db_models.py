from uuid import uuid4

from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.db import Base


def gen_uuid():
    return str(uuid4())


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)


class Workout(Base):
    __tablename__ = "workouts"

    id = Column(String, primary_key=True, default=gen_uuid)
    workout_date = Column(Date, nullable=False)
    note = Column(String, nullable=True)
    sets = relationship("Set", back_populates="workout", cascade="all, delete-orphan")


class Set(Base):
    __tablename__ = "sets"

    id = Column(String, primary_key=True, default=gen_uuid)
    reps = Column(Integer, nullable=False)
    weight = Column(Numeric(6, 2), nullable=False)
    exercise_name = Column(String, nullable=False)
    workout_id = Column(String, ForeignKey("workouts.id"), nullable=False)
    workout = relationship("Workout", back_populates="sets")
