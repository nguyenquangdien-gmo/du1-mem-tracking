from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract, or_, and_
from typing import List, Optional
from pydantic import BaseModel
from datetime import date

from ...database import get_db
from ...models.calendar import WorkingCalendar
from ...models.member import Member
from ..deps import get_current_user

router = APIRouter(prefix="/calendar", tags=["Calendar"])

class CalendarEventCreate(BaseModel):
    calendar_date: date
    type: str
    member_id: Optional[int] = None
    description: Optional[str] = None

class CalendarEventUpdate(BaseModel):
    calendar_date: date
    type: str
    member_id: Optional[int] = None
    description: Optional[str] = None

from ...models.task import Task

@router.get("")
def list_events(year: int, month: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    events = db.query(WorkingCalendar).filter(
        extract('year', WorkingCalendar.calendar_date) == year,
        extract('month', WorkingCalendar.calendar_date) == month
    ).order_by(WorkingCalendar.calendar_date).all()
    
    tasks = db.query(Task).filter(
        extract('year', Task.deadline) == year,
        extract('month', Task.deadline) == month,
        Task.status.notin_(['done', 'completed', 'cancelled', 'archived'])
    ).all()
    
    data = []
    for e in events:
        data.append({
            "id": e.id,
            "calendar_date": e.calendar_date,
            "type": e.type,
            "member_id": e.member_id,
            "member_name": e.member.full_name if e.member else None,
            "description": e.description
        })
        
    for t in tasks:
        assignees = ", ".join([m.member.full_name for m in t.members]) if t.members else ""
        data.append({
            "id": f"task_{t.id}",
            "calendar_date": t.deadline,
            "type": "task_deadline",
            "member_id": None,
            "member_name": None,
            "description": f"[{t.project.name if getattr(t, 'project', None) else 'Dự án'}] {t.name}" + (f" - {assignees}" if assignees else ""),
            "is_task": True,
            "task_id": t.id,
            "project_id": t.project_id
        })
        
    return {"success": True, "data": data}

@router.post("")
def create_event(data: CalendarEventCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.system_role.value not in ['admin', 'pm']:
        raise HTTPException(status_code=403, detail="Permission denied")
        
    event = WorkingCalendar(
        calendar_date=data.calendar_date,
        type=data.type,
        member_id=data.member_id,
        description=data.description
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"success": True, "data": {"id": event.id}}

@router.put("/{event_id}")
def update_event(event_id: int, data: CalendarEventUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.system_role.value not in ['admin', 'pm']:
        raise HTTPException(status_code=403, detail="Permission denied")
        
    event = db.query(WorkingCalendar).filter(WorkingCalendar.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    event.calendar_date = data.calendar_date
    event.type = data.type
    event.member_id = data.member_id
    event.description = data.description
    
    db.commit()
    return {"success": True}

@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.system_role.value not in ['admin', 'pm']:
        raise HTTPException(status_code=403, detail="Permission denied")
        
    event = db.query(WorkingCalendar).filter(WorkingCalendar.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    db.delete(event)
    db.commit()
    return {"success": True}
