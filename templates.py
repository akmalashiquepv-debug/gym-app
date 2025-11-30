# app/routers/templates.py
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any
from sqlmodel import select, Session
import json

from app.database import get_session
from app.models import WorkoutTemplate

router = APIRouter(prefix="/api/templates", tags=["templates"])

@router.get("/")
def list_templates(session: Session = Depends(get_session)):
    q = select(WorkoutTemplate).order_by(WorkoutTemplate.created_at.desc())
    return session.exec(q).all()

@router.post("/")
def create_template(payload: dict = Body(...), session: Session = Depends(get_session)):
    title = payload.get("title") or payload.get("name")
    exercises_text = payload.get("exercises_text")
    exercises = payload.get("exercises")
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    if exercises is None and exercises_text:
        lines = [line.strip() for line in exercises_text.splitlines() if line.strip()]
        exercises = [{"name": l} for l in lines]
    if exercises is None:
        exercises = []
    try:
        exercises_json = json.dumps(exercises)
    except Exception:
        exercises_json = "[]"
    tpl = WorkoutTemplate(title=title, exercises=exercises_json)
    session.add(tpl)
    session.commit()
    session.refresh(tpl)
    return {"status":"ok", "id": tpl.id, "template": {"title": tpl.title, "exercises": exercises}}
