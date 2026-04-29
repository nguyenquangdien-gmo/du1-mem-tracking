from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ...core.response import ok
from ...database import get_db
from ...models import Department, Member, Project, Task

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def global_search(
    q: str = Query(..., min_length=1),
    type: str = Query("all", pattern="^(all|member|project|task)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    like = f"%{q}%"
    result = {"members": [], "projects": [], "tasks": []}

    if type in ("all", "member"):
        members = (
            db.query(Member, Department)
            .outerjoin(Department, Department.id == Member.department_id)
            .filter(Member.is_deleted == 0)
            .filter(or_(Member.full_name.ilike(like), Member.email.ilike(like)))
            .limit(limit)
            .all()
        )
        result["members"] = [
            {
                "id": m.id,
                "full_name": m.full_name,
                "email": m.email,
                "department_code": d.code if d else "N/A",
                "default_role": m.default_role or "Member",
            }
            for m, d in members
        ]



    if type in ("all", "project"):
        projects = (
            db.query(Project)
            .filter(Project.is_deleted == 0)
            .filter(or_(Project.name.ilike(like), Project.description.ilike(like)))
            .limit(limit)
            .all()
        )
        result["projects"] = [
            {"id": p.id, "name": p.name, "status": p.status, "pm_id": p.pm_id}
            for p in projects
        ]

    if type in ("all", "task"):
        tasks = (
            db.query(Task)
            .filter(Task.is_deleted == 0)
            .filter(Task.name.ilike(like))
            .limit(limit)
            .all()
        )
        result["tasks"] = [
            {
                "id": t.id,
                "name": t.name,
                "project_id": t.project_id,
                "status": t.status,
                "priority": t.priority,
            }
            for t in tasks
        ]

    return ok(result)
