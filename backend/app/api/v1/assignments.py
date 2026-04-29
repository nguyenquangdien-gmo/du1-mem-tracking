from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.response import ok
from ...database import get_db
from ...schemas.assignment import AssignmentCreate, AssignmentUpdate
from ...services import assignment_service as svc

router = APIRouter(tags=["assignments"])


# ============== PROJECT MEMBER ==============

@router.post("/projects/{project_id}/members", status_code=201)
def assign_to_project(
    project_id: int, payload: AssignmentCreate, db: Session = Depends(get_db)
):
    pm, action = svc.assign_project_member(
        db,
        project_id=project_id,
        member_id=payload.member_id,
        role=payload.role,
        expected_end_date=payload.expected_end_date,
        description=payload.description,
    )
    db.commit()
    db.refresh(pm)
    return ok(
        {
            "id": pm.id,
            "project_id": pm.project_id,
            "member_id": pm.member_id,
            "role": pm.role,
            "description": pm.description,
            "expected_end_date": pm.expected_end_date,
            "is_hidden": bool(pm.is_hidden),
            "action": action,
        },
        message=f"Assigned ({action})",
    )


@router.get("/projects/{project_id}/members/{member_id}")
def get_project_member(project_id: int, member_id: int, db: Session = Depends(get_db)):
    from ...models import ProjectMember
    pm = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.member_id == member_id)
        .first()
    )
    if not pm:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Assignment không tồn tại"})
    return ok(
        {
            "id": pm.id,
            "project_id": pm.project_id,
            "member_id": pm.member_id,
            "role": pm.role,
            "description": pm.description,
            "expected_end_date": pm.expected_end_date,
            "is_hidden": bool(pm.is_hidden),
            "hidden_reason": pm.hidden_reason,
        }
    )


@router.delete("/projects/{project_id}/members/{member_id}")
def remove_from_project(
    project_id: int,
    member_id: int,
    reason: str | None = Query(None),
    db: Session = Depends(get_db),
):
    pm = svc.hide_project_member(db, project_id, member_id, reason=reason)
    db.commit()
    return ok(
        {
            "id": pm.id,
            "project_id": pm.project_id,
            "member_id": pm.member_id,
            "is_hidden": bool(pm.is_hidden),
            "hidden_reason": pm.hidden_reason,
        },
        message="Đã remove (hide)",
    )


@router.patch("/projects/{project_id}/members/{member_id}")
def update_project_assignment(
    project_id: int,
    member_id: int,
    payload: AssignmentUpdate,
    db: Session = Depends(get_db),
):
    pm = svc.update_project_member(
        db,
        project_id=project_id,
        member_id=member_id,
        role=payload.role,
        description=payload.description,
        expected_end_date=payload.expected_end_date,
        is_hidden=payload.is_hidden,
        hidden_reason=payload.hidden_reason,
    )
    db.commit()
    return ok(
        {
            "id": pm.id,
            "project_id": pm.project_id,
            "member_id": pm.member_id,
            "role": pm.role,
            "description": pm.description,
            "expected_end_date": pm.expected_end_date,
            "is_hidden": bool(pm.is_hidden),
            "hidden_reason": pm.hidden_reason,
        }
    )


# ============== TASK MEMBER ==============

@router.post("/tasks/{task_id}/members", status_code=201)
def assign_to_task(task_id: int, payload: AssignmentCreate, db: Session = Depends(get_db)):
    tm, action = svc.assign_task_member(
        db,
        task_id=task_id,
        member_id=payload.member_id,
        role=payload.role,
        expected_end_date=payload.expected_end_date,
    )
    db.commit()
    db.refresh(tm)
    return ok(
        {
            "id": tm.id,
            "task_id": tm.task_id,
            "member_id": tm.member_id,
            "role": tm.role,
            "expected_end_date": tm.expected_end_date,
            "is_hidden": bool(tm.is_hidden),
            "action": action,
        },
        message=f"Assigned ({action})",
    )


@router.get("/tasks/{task_id}/members/{member_id}")
def get_task_member(task_id: int, member_id: int, db: Session = Depends(get_db)):
    from ...models import TaskMember
    tm = (
        db.query(TaskMember)
        .filter(TaskMember.task_id == task_id, TaskMember.member_id == member_id)
        .first()
    )
    if not tm:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Assignment không tồn tại"})
    return ok(
        {
            "id": tm.id,
            "task_id": tm.task_id,
            "member_id": tm.member_id,
            "role": tm.role,
            "expected_end_date": tm.expected_end_date,
            "is_hidden": bool(tm.is_hidden),
            "hidden_reason": tm.hidden_reason,
        }
    )


@router.delete("/tasks/{task_id}/members/{member_id}")
def remove_from_task(
    task_id: int,
    member_id: int,
    reason: str | None = Query(None),
    db: Session = Depends(get_db),
):
    tm = svc.hide_task_member(db, task_id, member_id, reason=reason)
    db.commit()
    return ok(
        {
            "id": tm.id,
            "task_id": tm.task_id,
            "member_id": tm.member_id,
            "is_hidden": bool(tm.is_hidden),
            "hidden_reason": tm.hidden_reason,
        },
        message="Đã remove (hide)",
    )


@router.patch("/tasks/{task_id}/members/{member_id}")
def update_task_assignment(
    task_id: int,
    member_id: int,
    payload: AssignmentUpdate,
    db: Session = Depends(get_db),
):
    tm = svc.update_task_member(
        db,
        task_id=task_id,
        member_id=member_id,
        role=payload.role,
        expected_end_date=payload.expected_end_date,
        is_hidden=payload.is_hidden,
        hidden_reason=payload.hidden_reason,
    )
    db.commit()
    return ok(
        {
            "id": tm.id,
            "task_id": tm.task_id,
            "member_id": tm.member_id,
            "role": tm.role,
            "expected_end_date": tm.expected_end_date,
            "is_hidden": bool(tm.is_hidden),
            "hidden_reason": tm.hidden_reason,
        }
    )
