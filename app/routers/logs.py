# app/routers/logs.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Optional, List, Dict, Any
from sqlmodel import select
from datetime import datetime
from app.database import get_session
from app.models import WorkoutLog
from sqlmodel import Session
from sqlalchemy import func

# optional import for PR tracking
try:
    from app.models import PRTracker
except Exception:
    PRTracker = None

router = APIRouter(prefix="/api/logs", tags=["logs"])

def parse_datetime_val(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    s = str(val).strip()
    try:
        if ' ' in s and 'T' not in s:
            s = s.replace(' ', 'T')
        return datetime.fromisoformat(s)
    except Exception:
        pass
    # fallback numeric timestamp
    try:
        n = float(s)
        if n > 1e12:
            return datetime.fromtimestamp(n / 1000.0)
        return datetime.fromtimestamp(n)
    except Exception:
        return None

def to_number_loose(val) -> Optional[float]:
    if val is None:
        return None
    try:
        s = str(val).strip()
        cleaned = ''.join(ch for ch in s if (ch.isdigit() or ch in '.-'))
        if cleaned in ('', '.', '-', '-.'):
            return None
        return float(cleaned)
    except Exception:
        return None

def to_int_loose(val) -> Optional[int]:
    n = to_number_loose(val)
    if n is None:
        return None
    try:
        return int(round(n))
    except Exception:
        return None

@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_log(req: Request, session: Session = Depends(get_session)):
    body: Dict[str, Any] = await req.json()
    keys = {k.lower(): v for k, v in body.items()}

    exercise = keys.get("exercise") or keys.get("name") or keys.get("exercise_name")
    if not exercise:
        raise HTTPException(status_code=400, detail="Missing exercise name")

    weight = to_number_loose(keys.get("weight") or keys.get("w") or keys.get("weight_kg") or keys.get("kg"))
    sets = to_int_loose(keys.get("sets") or keys.get("set") or keys.get("s"))
    reps = to_int_loose(keys.get("reps") or keys.get("rep") or keys.get("r"))

    perf = parse_datetime_val(keys.get("performed_at") or keys.get("performedat") or keys.get("datetime") or keys.get("created_at") or keys.get("createdat") or keys.get("date"))

    if weight is None:
        weight = 0.0
    if sets is None:
        sets = 0
    if reps is None:
        reps = 0
    if perf is None:
        perf = datetime.utcnow()

    log = WorkoutLog(
        exercise=str(exercise),
        weight=weight,
        sets=sets,
        reps=reps,
        performed_at=perf,
        datetime=perf
    )

    session.add(log)
    session.commit()
    session.refresh(log)

    # update PR
    if PRTracker is not None:
        try:
            stmt = select(PRTracker).where(PRTracker.exercise == log.exercise)
            existing = session.exec(stmt).first()
            if existing:
                if log.weight > existing.best_weight:
                    existing.best_weight = log.weight
                    existing.best_date = log.performed_at
                    session.add(existing)
                    session.commit()
            else:
                pr = PRTracker(exercise=log.exercise, best_weight=log.weight, best_date=log.performed_at)
                session.add(pr)
                session.commit()
        except Exception:
            session.rollback()

    return {"status": "ok", "log_id": log.id, "log": {
        "exercise": log.exercise, "weight": log.weight, "sets": log.sets, "reps": log.reps,
        "performed_at": log.performed_at.isoformat()
    }}

@router.get("/", response_model=List[Dict[str, Any]])
def get_logs(exercise: Optional[str] = None, session: Session = Depends(get_session)):
    stmt = select(WorkoutLog)
    if exercise:
        try:
            stmt = stmt.where(WorkoutLog.exercise.ilike(f"%{exercise}%"))
        except Exception:
            stmt = stmt.where(func.lower(WorkoutLog.exercise) == exercise.lower())
    stmt = stmt.order_by(WorkoutLog.performed_at)
    rows = session.exec(stmt).all()
    out = []
    for r in rows:
        out.append({
            "id": r.id,
            "exercise": r.exercise,
            "weight": r.weight,
            "sets": r.sets,
            "reps": r.reps,
            "performed_at": r.performed_at.isoformat() if getattr(r, "performed_at", None) else None
        })
    return out

@router.get("/progress")
def get_progress(exercise: Optional[str] = None, from_date: Optional[str] = None, to_date: Optional[str] = None, session: Session = Depends(get_session)):
    stmt = select(WorkoutLog)
    if exercise:
        try:
            stmt = stmt.where(WorkoutLog.exercise.ilike(f"%{exercise}%"))
        except Exception:
            stmt = stmt.where(func.lower(WorkoutLog.exercise) == exercise.lower())
    stmt = stmt.order_by(WorkoutLog.performed_at)
    rows = session.exec(stmt).all()

    if from_date:
        try:
            fd = parse_datetime_val(from_date)
            rows = [r for r in rows if getattr(r, "performed_at", None) and getattr(r, "performed_at") >= fd]
        except Exception:
            pass
    if to_date:
        try:
            td = parse_datetime_val(to_date)
            rows = [r for r in rows if getattr(r, "performed_at", None) and getattr(r, "performed_at") <= td]
        except Exception:
            pass

    daily = {}
    for r in rows:
        d = getattr(r, "performed_at", None)
        if not d:
            continue
        day = d.date().isoformat()
        w = float(getattr(r, "weight", 0) or 0)
        s = int(getattr(r, "sets", 0) or 0)
        rp = int(getattr(r, "reps", 0) or 0)
        vol = w * s * rp
        daily[day] = daily.get(day, 0) + vol

    labels = sorted(daily.keys())
    volumes = [round(daily[d] + 0.0, 3) for d in labels]

    pr_data = None
    if PRTracker is not None and exercise:
        try:
            pr_stmt = select(PRTracker).where(PRTracker.exercise == exercise)
            pr = session.exec(pr_stmt).first()
            if pr:
                pr_data = {"best_weight": pr.best_weight, "best_date": pr.best_date.isoformat() if pr.best_date else None}
        except Exception:
            pr_data = None

    return {"labels": labels, "datasets": {"volume": volumes}, "pr": pr_data}
