# app/routers/workouts.py
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from sqlmodel import select, Session
from datetime import datetime
import json

from app.database import get_session
from app.models import ScheduledWorkout, WorkoutTemplate

router = APIRouter(prefix="/api/workouts", tags=["workouts"])

@router.post("/schedule")
async def create_workout(payload: Dict[str, Any] = Body(...), session: Session = Depends(get_session)):
    title = payload.get("title") or payload.get("name")
    datetime_str = payload.get("datetime") or payload.get("scheduled_at")
    notes = payload.get("notes")
    user_id = payload.get("userId", 1)
    template_id = payload.get("templateId")

    if not title or not datetime_str:
        raise HTTPException(status_code=400, detail="title and datetime are required")

    try:
        if isinstance(datetime_str, str) and ' ' in datetime_str and 'T' not in datetime_str:
            datetime_str = datetime_str.replace(' ', 'T')
        sched = datetime.fromisoformat(datetime_str)
    except Exception:
        try:
            sched = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=400, detail="invalid datetime format")

    if template_id:
        tpl = session.get(WorkoutTemplate, int(template_id))
        if tpl:
            try:
                exercises = json.loads(tpl.exercises) if tpl.exercises else []
                summary = "; ".join([e.get("name", "") for e in exercises])
                notes = (notes or "") + f"\nTemplate: {tpl.title} | {summary}"
            except Exception:
                pass

    workout = ScheduledWorkout(
        user_id=user_id,
        title=title,
        scheduled_at=sched,
        datetime=sched,
        notes=notes
    )
    session.add(workout)
    session.commit()
    session.refresh(workout)
    return {"status":"ok", "id": workout.id, "item": {"title": workout.title, "scheduled_at": workout.scheduled_at.isoformat(), "notes": workout.notes}}

@router.get("/schedule")
def list_workouts(from_dt: Optional[datetime] = Query(None), to_dt: Optional[datetime] = Query(None), session: Session = Depends(get_session)):
    q = select(ScheduledWorkout)
    if from_dt:
        q = q.where(ScheduledWorkout.scheduled_at >= from_dt)
    if to_dt:
        q = q.where(ScheduledWorkout.scheduled_at <= to_dt)
    q = q.order_by(ScheduledWorkout.scheduled_at)
    rows = session.exec(q).all()
    out = []
    for r in rows:
        out.append({
            "id": r.id,
            "title": r.title,
            "scheduled_at": r.scheduled_at.isoformat() if r.scheduled_at else None,
            "notes": r.notes,
            "status": r.status
        })
    return out

@router.patch("/schedule/{workout_id}")
def update_workout_status(workout_id: int, status: Optional[str] = Query(None), session: Session = Depends(get_session)):
    w = session.get(ScheduledWorkout, workout_id)
    if not w:
        raise HTTPException(status_code=404, detail="Workout not found")
    if status:
        w.status = status
    session.add(w)
    session.commit()
    session.refresh(w)
    return {"status":"ok", "id": w.id, "item": {"title": w.title, "scheduled_at": w.scheduled_at.isoformat(), "status": w.status}}
