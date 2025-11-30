# app/models.py
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class ScheduledWorkout(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    scheduled_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[int] = None
    notes: Optional[str] = None
    status: Optional[str] = None  # e.g., "pending", "done"

class MealLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    calories: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WorkoutLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    exercise: str
    weight: float = 0.0
    sets: int = 0
    reps: int = 0
    performed_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

class PRTracker(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    exercise: str
    best_weight: float = 0.0
    best_date: Optional[datetime] = None

class WorkoutTemplate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    exercises: Optional[str] = None  # store JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
