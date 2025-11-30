# app/routers/meals.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Optional, List, Dict, Any
from sqlmodel import select
from datetime import datetime
from app.database import get_session
from app.models import MealLog
from sqlmodel import Session

router = APIRouter(prefix="/api/meals", tags=["meals"])

def parse_datetime_val(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    try:
        if ' ' in val and 'T' not in val:
            val = val.replace(' ', 'T')
        return datetime.fromisoformat(val)
    except Exception:
        try:
            return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
        except Exception:
            try:
                n = float(val)
                if n > 1e12:
                    return datetime.fromtimestamp(n/1000.0)
                return datetime.fromtimestamp(n)
            except Exception:
                return None

@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_meal(req: Request, session: Session = Depends(get_session)):
    body: Dict[str, Any] = await req.json()
    name = body.get("name") or body.get("meal") or body.get("meal_name") or body.get("title")
    calories = body.get("calories") or body.get("kcal") or body.get("cal") or 0
    if name is None:
        raise HTTPException(status_code=400, detail="Missing meal name")
    try:
        calories_num = int(float(str(calories))) if calories is not None else 0
    except Exception:
        calories_num = 0
    dt = parse_datetime_val(body.get("datetime") or body.get("time") or body.get("created_at"))
    if dt is None:
        dt = datetime.utcnow()

    meal = MealLog(name=str(name), calories=calories_num, created_at=dt)
    session.add(meal)
    session.commit()
    session.refresh(meal)
    return {"status":"ok", "id": meal.id, "meal": {"name": meal.name, "calories": meal.calories, "created_at": meal.created_at.isoformat()}}

@router.get("/", response_model=List[Dict[str, Any]])
def list_meals(session: Session = Depends(get_session)):
    stmt = select(MealLog).order_by(MealLog.created_at.desc())
    rows = session.exec(stmt).all()
    out = []
    for r in rows:
        out.append({
            "id": r.id,
            "name": r.name,
            "calories": r.calories,
            "created_at": r.created_at.isoformat() if getattr(r,"created_at",None) else None
        })
    return out
