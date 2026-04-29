from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ...core.errors import member_has_active_assignments, not_found, validation_error
from ...core.response import ok
from ...core.security import get_password_hash
from ...database import get_db
from ...models import Department, Member, Project, ProjectMember, Task, TaskMember
from ...schemas.member import MemberCreate, MemberOut, MemberUpdate
from ..deps import pm_or_admin

router = APIRouter(prefix="/members", tags=["members"])


def _member_to_out(m: Member, dept: Department | None = None) -> MemberOut:
    data = {
        "id": m.id,
        "full_name": m.full_name,
        "email": m.email,
        "department_id": m.department_id,
        "phone": m.phone,
        "default_role": m.default_role,
        "other_roles": m.other_roles or [],
        "is_deleted": m.is_deleted,

        "created_at": m.created_at,
        "updated_at": m.updated_at,
        "department_name": dept.name if dept else (m.department.name if m.department else None),
        "department_code": dept.code if dept else (m.department.code if m.department else None),
    }
    return MemberOut.model_validate(data)


@router.get("")
def list_members(
    department_id: int | None = None,
    q: str | None = None,
    include_deleted: bool = False,
    available_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Member)
    if not include_deleted:
        query = query.filter(Member.is_deleted == 0)
    if department_id:
        query = query.filter(Member.department_id == department_id)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Member.full_name.ilike(like), Member.email.ilike(like)))
    if available_only:
        from datetime import datetime
        now = datetime.now()
        # Filter out members who have at least one assignment that is NOT HIDDEN and (NOT EXPIRED or has no end date)
        assigned_and_active = (
            db.query(ProjectMember.member_id)
            .filter(ProjectMember.is_hidden == 0)
            .filter(or_(ProjectMember.expected_end_date == None, ProjectMember.expected_end_date >= now))
        )
        query = query.filter(~Member.id.in_(assigned_and_active))
    total = query.count()
    items = (
        query.order_by(Member.full_name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ok(
        [_member_to_out(m) for m in items],
        meta={"page": page, "page_size": page_size, "total": total},
    )


@router.post("", status_code=201, dependencies=[Depends(pm_or_admin)])
def create_member(payload: MemberCreate, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    exists = db.query(Member).filter(Member.email == email).first()
    if exists:
        raise validation_error("Email đã tồn tại", field="email")
    dept = db.query(Department).filter(Department.id == payload.department_id).first()
    if not dept:
        raise validation_error("Bộ phận không tồn tại", field="department_id")
    m = Member(
        full_name=payload.full_name.strip(),
        email=email,
        department_id=payload.department_id,
        phone=payload.phone.strip() if payload.phone else None,
        default_role=payload.default_role,
        other_roles=payload.other_roles,
    )

    db.add(m)
    db.commit()
    db.refresh(m)
    return ok(_member_to_out(m, dept), message="Tạo member thành công")


@router.get("/search")
def search_members(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    like = f"%{q}%"
    items = (
        db.query(Member)
        .filter(Member.is_deleted == 0)
        .filter(or_(Member.full_name.ilike(like), Member.email.ilike(like)))
        .limit(limit)
        .all()
    )
    return ok([_member_to_out(m) for m in items])


@router.get("/{member_id}")
def get_member(member_id: int, db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise not_found("Member")
    return ok(_member_to_out(m))


@router.patch("/{member_id}", dependencies=[Depends(pm_or_admin)])
def update_member(member_id: int, payload: MemberUpdate, db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise not_found("Member")
    if payload.email is not None:
        email = payload.email.lower().strip()
        other = db.query(Member).filter(Member.email == email, Member.id != member_id).first()
        if other:
            raise validation_error("Email đã tồn tại", field="email")
        m.email = email
    if payload.full_name is not None:
        m.full_name = payload.full_name.strip()
    if payload.department_id is not None:
        dept = db.query(Department).filter(Department.id == payload.department_id).first()
        if not dept:
            raise validation_error("Bộ phận không tồn tại", field="department_id")
        m.department_id = payload.department_id
    if payload.default_role is not None:
        m.default_role = payload.default_role
    if payload.other_roles is not None:
        m.other_roles = payload.other_roles
    if payload.phone is not None:
        m.phone = payload.phone.strip() if payload.phone else None

    db.commit()
    db.refresh(m)
    return ok(_member_to_out(m))


@router.delete("/{member_id}", dependencies=[Depends(pm_or_admin)])
def delete_member(member_id: int, force: bool = False, db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise not_found("Member")
    active_proj = (
        db.query(ProjectMember)
        .filter(ProjectMember.member_id == member_id, ProjectMember.is_hidden == 0)
        .count()
    )
    active_task = (
        db.query(TaskMember)
        .filter(TaskMember.member_id == member_id, TaskMember.is_hidden == 0)
        .count()
    )
    if (active_proj or active_task) and not force:
        raise member_has_active_assignments()
    if force:
        db.query(ProjectMember).filter(ProjectMember.member_id == member_id).update(
            {"is_hidden": 1, "hidden_reason": "member deleted"}
        )
        db.query(TaskMember).filter(TaskMember.member_id == member_id).update(
            {"is_hidden": 1, "hidden_reason": "member deleted"}
        )
    m.is_deleted = 1
    db.commit()
    return ok({"id": member_id}, message="Đã xóa")


@router.get("/{member_id}/assignments")
def member_assignments(
    member_id: int, include_hidden: bool = False, db: Session = Depends(get_db)
):
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise not_found("Member")

    proj_q = (
        db.query(ProjectMember, Project, Department)
        .join(Project, Project.id == ProjectMember.project_id)
        .join(Department, Department.id == Project.department_id)
        .filter(ProjectMember.member_id == member_id, Project.is_deleted == 0)
    )
    if not include_hidden:
        proj_q = proj_q.filter(ProjectMember.is_hidden == 0)
    projects = []
    active_p = 0
    hidden_p = 0
    for pm, p, dept in proj_q.all():
        if pm.is_hidden:
            hidden_p += 1
        else:
            active_p += 1
        projects.append(
            {
                "id": pm.id,
                "project_id": p.id,
                "member_id": member_id,
                "project_name": p.name,
                "department_code": dept.code,
                "role": pm.role,
                "expected_end_date": pm.expected_end_date,
                "is_hidden": bool(pm.is_hidden),
                "hidden_reason": pm.hidden_reason,
                "assigned_at": pm.assigned_at,
                "updated_at": pm.updated_at,
            }
        )

    task_q = (
        db.query(TaskMember, Task, Project)
        .join(Task, Task.id == TaskMember.task_id)
        .join(Project, Project.id == Task.project_id)
        .filter(TaskMember.member_id == member_id, Task.is_deleted == 0)
    )
    if not include_hidden:
        task_q = task_q.filter(TaskMember.is_hidden == 0)
    tasks = []
    active_t = 0
    hidden_t = 0
    for tm, t, p in task_q.all():
        if tm.is_hidden:
            hidden_t += 1
        else:
            active_t += 1
        tasks.append(
            {
                "id": tm.id,
                "task_id": t.id,
                "member_id": member_id,
                "task_name": t.name,
                "project_id": p.id,
                "project_name": p.name,
                "role": tm.role,
                "expected_end_date": tm.expected_end_date,
                "is_hidden": bool(tm.is_hidden),
                "hidden_reason": tm.hidden_reason,
                "assigned_at": tm.assigned_at,
                "updated_at": tm.updated_at,
            }
        )

    return ok(
        {
            "member": _member_to_out(m).model_dump(),
            "projects": projects,
            "tasks": tasks,
            "stats": {
                "active_projects": active_p,
                "active_tasks": active_t,
                "hidden_projects": hidden_p,
                "hidden_tasks": hidden_t,
            },
        }
    )
