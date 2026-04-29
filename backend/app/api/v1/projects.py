from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ...core.errors import not_found, validation_error
from ...core.response import ok
from ...database import get_db
from ...models import Department, Member, Project, ProjectMember, Task
from ...schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from ..deps import pm_or_admin

router = APIRouter(prefix="/projects", tags=["projects"])


def _project_to_out(db: Session, p: Project) -> dict:
    dept = db.query(Department).filter(Department.id == p.department_id).first()
    pm = db.query(Member).filter(Member.id == p.pm_id).first()
    task_count = db.query(Task).filter(Task.project_id == p.id, Task.is_deleted == 0).count()
    from datetime import date
    task_done = (
        db.query(Task)
        .filter(Task.project_id == p.id, Task.is_deleted == 0, Task.status == "done")
        .count()
    )
    task_overdue = (
        db.query(Task)
        .filter(Task.project_id == p.id, Task.is_deleted == 0, Task.status.notin_(["done", "archived"]), Task.deadline < date.today())
        .count()
    )
    member_count = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == p.id, ProjectMember.is_hidden == 0)
        .count()
    )
    return {
        "id": p.id,
        "name": p.name,
        "department_id": p.department_id,
        "pm_id": p.pm_id,
        "start_date": p.start_date,
        "expected_end_date": p.expected_end_date,
        "description": p.description,
        "status": p.status,
        "is_important": p.is_important,
        "chatops_group_id": p.chatops_group_id,
        "is_deleted": p.is_deleted,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
        "department_name": dept.name if dept else None,
        "pm_name": pm.full_name if pm else None,
        "task_count": task_count,
        "task_done_count": task_done,
        "overdue_task_count": task_overdue,
        "active_member_count": member_count,
    }


@router.get("")
def list_projects(
    department_id: int | None = None,
    pm_id: int | None = None,
    status: str | None = None,
    q: str | None = None,
    include_deleted: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(Project)
    if not include_deleted:
        query = query.filter(Project.is_deleted == 0)
    if department_id:
        query = query.filter(Project.department_id == department_id)
    if pm_id:
        query = query.filter(Project.pm_id == pm_id)
    if status:
        query = query.filter(Project.status == status)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Project.name.ilike(like), Project.description.ilike(like)))
    items = query.order_by(Project.id.desc()).all()
    return ok([_project_to_out(db, p) for p in items], meta={"total": len(items)})


@router.post("", status_code=201, dependencies=[Depends(pm_or_admin)])
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.id == payload.department_id).first()
    if not dept:
        raise validation_error("Bộ phận không tồn tại", field="department_id")
    pm = db.query(Member).filter(Member.id == payload.pm_id, Member.is_deleted == 0).first()
    if not pm:
        raise validation_error("PM không hợp lệ", field="pm_id")
    if (
        payload.start_date
        and payload.expected_end_date
        and payload.start_date > payload.expected_end_date
    ):
        raise validation_error("start_date phải <= expected_end_date")
    p = Project(
        name=payload.name.strip(),
        department_id=payload.department_id,
        pm_id=payload.pm_id,
        start_date=payload.start_date,
        expected_end_date=payload.expected_end_date,
        description=payload.description,
        status=payload.status,
        is_important=payload.is_important,
        chatops_group_id=payload.chatops_group_id,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return ok(_project_to_out(db, p), message="Tạo project thành công")


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise not_found("Project")
    return ok(_project_to_out(db, p))


@router.patch("/{project_id}", dependencies=[Depends(pm_or_admin)])
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise not_found("Project")
    data = payload.model_dump(exclude_unset=True)
    if "department_id" in data:
        if not db.query(Department).filter(Department.id == data["department_id"]).first():
            raise validation_error("Bộ phận không tồn tại", field="department_id")
    if "pm_id" in data:
        if not db.query(Member).filter(Member.id == data["pm_id"], Member.is_deleted == 0).first():
            raise validation_error("PM không hợp lệ", field="pm_id")
    for k, v in data.items():
        setattr(p, k, v)
    if p.start_date and p.expected_end_date and p.start_date > p.expected_end_date:
        raise validation_error("start_date phải <= expected_end_date")
    db.commit()
    db.refresh(p)
    return ok(_project_to_out(db, p))


@router.delete("/{project_id}", dependencies=[Depends(pm_or_admin)])
def delete_project(project_id: int, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise not_found("Project")
    p.is_deleted = 1
    db.query(Task).filter(Task.project_id == project_id).update({"is_deleted": 1})
    db.commit()
    return ok({"id": project_id}, message="Đã xóa project")


@router.get("/{project_id}/tasks")
def project_tasks(project_id: int, include_deleted: bool = False, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise not_found("Project")
    q = db.query(Task).filter(Task.project_id == project_id)
    if not include_deleted:
        q = q.filter(Task.is_deleted == 0)
    tasks = q.order_by(Task.id.desc()).all()
    result = []
    for t in tasks:
        pm = db.query(Member).filter(Member.id == t.pm_id).first()
        count = (
            db.query(ProjectMember)  # placeholder to keep import
            .filter(ProjectMember.project_id == p.id)
            .count()
        ) and None  # unused
        from ...models import TaskMember
        mem_count = (
            db.query(TaskMember)
            .filter(TaskMember.task_id == t.id, TaskMember.is_hidden == 0)
            .count()
        )
        result.append(
            {
                "id": t.id,
                "name": t.name,
                "project_id": t.project_id,
                "department_id": t.department_id,
                "pm_id": t.pm_id,
                "pm_name": pm.full_name if pm else None,
                "deadline": t.deadline,
                "priority": t.priority,
                "status": t.status,
                "is_deleted": t.is_deleted,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
                "active_member_count": mem_count,
            }
        )
    return ok(result)


@router.get("/{project_id}/members")
def project_members(
    project_id: int, include_hidden: bool = False, db: Session = Depends(get_db)
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise not_found("Project")
    q = (
        db.query(ProjectMember, Member, Department)
        .join(Member, Member.id == ProjectMember.member_id)
        .join(Department, Department.id == Member.department_id)
        .filter(ProjectMember.project_id == project_id)
    )
    if not include_hidden:
        q = q.filter(ProjectMember.is_hidden == 0)
    rows = q.order_by(ProjectMember.assigned_at.desc()).all()
    result = []
    for pm, m, dept in rows:
        result.append(
            {
                "id": pm.id,
                "project_id": pm.project_id,
                "member_id": pm.member_id,
                "member_name": m.full_name,
                "member_email": m.email,
                "department_code": dept.code,
                "role": pm.role,
                "description": pm.description,
                "expected_end_date": pm.expected_end_date,
                "is_hidden": bool(pm.is_hidden),
                "hidden_reason": pm.hidden_reason,
                "assigned_at": pm.assigned_at,
                "updated_at": pm.updated_at,
            }
        )
    return ok(result)
