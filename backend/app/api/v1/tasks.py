from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ...core.errors import not_found, validation_error
from ...core.response import ok
from ...database import get_db
from ...models import Department, Member, Project, Task, TaskMember
from ...schemas.task import TaskCreate, TaskUpdate
from ...services.chatops import send_chatops_message

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/{task_id}/notify")
async def notify_task_members(task_id: int, mode: str = Query("all", enum=["all", "new"]), db: Session = Depends(get_db)):
    t = db.query(Task).filter(Task.id == task_id).first()
    if not t:
        raise not_found("Task")
    
    project = db.query(Project).filter(Project.id == t.project_id).first()
    if not project or not project.chatops_group_id:
        # Return a custom error structure so the frontend can show a nice message
        return ok(None, success=False, error={"message": "Dự án chưa cấu hình ChatOps Group ID nên không thể gửi thông báo"})
    
    members_q = (
        db.query(TaskMember, Member)
        .join(Member, Member.id == TaskMember.member_id)
        .filter(TaskMember.task_id == t.id, TaskMember.is_hidden == 0)
    )
    
    if mode == "new":
        members_q = members_q.filter(TaskMember.notified == 0)
    
    members_list = members_q.all()
    if not members_list:
        return ok(None, message="Không có thành viên nào cần thông báo")

    results = []
    target = project.chatops_group_id
    prefix = "[New] "
    mention = ""
    for tm, m in members_list:
        if tm.notified:
            prefix = "[Update] "
        mention += "@" + m.email.replace("@", "-") + " "
        tm.notified = 1
        results.append(m.full_name)
        
    msg = f"{prefix}🔔 **Thông báo Task**\n\n"
    msg += f"👤 **Member**: {mention}\n"
    msg += f"📌 **Dự án**: {project.name}\n"
    msg += f"📝 **Task**: {t.name}\n"
    if t.description: msg += f"📄 **Mô tả**: {t.description}\n"
    msg += f"📅 **Bắt đầu**: {t.start_date.strftime('%d/%m/%Y') if t.start_date else 'N/A'}\n"
    msg += f"🏁 **Hạn chót**: {t.deadline.strftime('%d/%m/%Y') if t.deadline else 'N/A'}\n"
    if t.jira_link: msg += f"🔗 **Jira**: {t.jira_link}\n"
        
    await send_chatops_message(target, msg)
        
    db.commit()
    return ok(results, message=f"Đã gửi thông báo cho {len(results)} thành viên")


def _task_to_out(db: Session, t: Task) -> dict:
    dept = db.query(Department).filter(Department.id == t.department_id).first() if t.department_id else None
    pm = db.query(Member).filter(Member.id == t.pm_id).first() if t.pm_id else None
    project = db.query(Project).filter(Project.id == t.project_id).first()
    members_q = (
        db.query(TaskMember, Member)
        .join(Member, Member.id == TaskMember.member_id)
        .filter(TaskMember.task_id == t.id, TaskMember.is_hidden == 0)
    )
    members = []
    for tm, m in members_q.all():
        members.append({"id": m.id, "full_name": m.full_name})

    return {
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "project_id": t.project_id,
        "department_id": t.department_id,
        "pm_id": t.pm_id,
        "start_date": t.start_date,
        "deadline": t.deadline,
        "jira_link": t.jira_link,
        "priority": t.priority,
        "status": t.status,
        "is_deleted": t.is_deleted,
        "created_at": t.created_at,
        "updated_at": t.updated_at,
        "project_name": project.name if project else None,
        "department_name": dept.name if dept else None,
        "pm_name": pm.full_name if pm else None,
        "members": members,
        "active_member_count": len(members),
    }


@router.get("")
def list_tasks(
    project_id: int | None = None,
    status: str | None = None,
    priority: str | None = None,
    q: str | None = None,
    include_deleted: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(Task)
    if not include_deleted:
        query = query.filter(Task.is_deleted == 0)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if q:
        query = query.filter(Task.name.ilike(f"%{q}%"))
    items = query.order_by(Task.id.desc()).all()
    return ok([_task_to_out(db, t) for t in items], meta={"total": len(items)})


@router.post("", status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == payload.project_id, Project.is_deleted == 0).first()
    if not project:
        raise validation_error("Project không hợp lệ", field="project_id")
    
    t = Task(
        name=payload.name.strip(),
        description=payload.description,
        project_id=payload.project_id,
        department_id=payload.department_id or project.department_id,
        pm_id=payload.pm_id or project.pm_id,
        start_date=payload.start_date,
        deadline=payload.deadline,
        jira_link=payload.jira_link,
        priority=payload.priority,
        status=payload.status,
    )
    db.add(t)
    db.flush() # Get ID
    
    if payload.member_ids:
        for mid in payload.member_ids:
            tm = TaskMember(
                task_id=t.id,
                member_id=mid,
                role="Member", # Default role for task
            )
            db.add(tm)
            
    db.commit()
    db.refresh(t)
    return ok(_task_to_out(db, t), message="Tạo task thành công")


@router.get("/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    t = db.query(Task).filter(Task.id == task_id).first()
    if not t:
        raise not_found("Task")
    return ok(_task_to_out(db, t))


@router.patch("/{task_id}")
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    t = db.query(Task).filter(Task.id == task_id).first()
    if not t:
        raise not_found("Task")
    data = payload.model_dump(exclude_unset=True)
    if "department_id" in data:
        if not db.query(Department).filter(Department.id == data["department_id"]).first():
            raise validation_error("Bộ phận không tồn tại", field="department_id")
    if "pm_id" in data:
        if not db.query(Member).filter(Member.id == data["pm_id"], Member.is_deleted == 0).first():
            raise validation_error("PM không hợp lệ", field="pm_id")
    
    member_ids = data.pop("member_ids", None)
    
    for k, v in data.items():
        setattr(t, k, v)
    
    if member_ids is not None:
        # Sync members
        db.query(TaskMember).filter(TaskMember.task_id == task_id).delete()
        for mid in member_ids:
            tm = TaskMember(task_id=task_id, member_id=mid, role="Member")
            db.add(tm)

    db.commit()
    db.refresh(t)
    return ok(_task_to_out(db, t))


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    t = db.query(Task).filter(Task.id == task_id).first()
    if not t:
        raise not_found("Task")
    t.is_deleted = 1
    db.commit()
    return ok({"id": task_id}, message="Đã xóa task")


@router.get("/{task_id}/members")
def task_members(task_id: int, include_hidden: bool = False, db: Session = Depends(get_db)):
    t = db.query(Task).filter(Task.id == task_id).first()
    if not t:
        raise not_found("Task")
    q = (
        db.query(TaskMember, Member, Department)
        .join(Member, Member.id == TaskMember.member_id)
        .join(Department, Department.id == Member.department_id)
        .filter(TaskMember.task_id == task_id)
    )
    if not include_hidden:
        q = q.filter(TaskMember.is_hidden == 0)
    rows = q.order_by(TaskMember.assigned_at.desc()).all()
    result = []
    for tm, m, dept in rows:
        result.append(
            {
                "id": tm.id,
                "task_id": tm.task_id,
                "member_id": tm.member_id,
                "member_name": m.full_name,
                "member_email": m.email,
                "department_code": dept.code,
                "role": tm.role,
                "expected_end_date": tm.expected_end_date,
                "is_hidden": bool(tm.is_hidden),
                "hidden_reason": tm.hidden_reason,
                "assigned_at": tm.assigned_at,
                "updated_at": tm.updated_at,
            }
        )
    return ok(result)
