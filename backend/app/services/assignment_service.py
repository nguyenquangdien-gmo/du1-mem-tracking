from datetime import date

from sqlalchemy.orm import Session

from ..core.errors import already_assigned, not_found, validation_error
from ..models import Member, Project, ProjectMember, Task, TaskMember


def _ensure_member_active(db: Session, member_id: int) -> Member:
    m = db.query(Member).filter(Member.id == member_id, Member.is_deleted == 0).first()
    if not m:
        raise not_found("Member")
    return m


def assign_project_member(
    db: Session,
    project_id: int,
    member_id: int,
    role: str,
    expected_end_date: date | None,
    description: str | None = None,
) -> tuple[ProjectMember, str]:
    project = db.query(Project).filter(Project.id == project_id, Project.is_deleted == 0).first()
    if not project:
        raise not_found("Project")
    _ensure_member_active(db, member_id)

    existing = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.member_id == member_id)
        .first()
    )
    if existing:
        if not existing.is_hidden:
            raise already_assigned("Member đã có trong project này")
        existing.is_hidden = 0
        existing.hidden_reason = None
        existing.role = role
        existing.description = description
        existing.expected_end_date = expected_end_date
        db.flush()
        return existing, "unhidden"

    new_pm = ProjectMember(
        project_id=project_id,
        member_id=member_id,
        role=role,
        description=description,
        expected_end_date=expected_end_date,
    )
    db.add(new_pm)
    db.flush()
    return new_pm, "created"


def hide_project_member(
    db: Session, project_id: int, member_id: int, reason: str | None = None
) -> ProjectMember:
    pm = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.member_id == member_id)
        .first()
    )
    if not pm:
        raise not_found("Assignment")
    pm.is_hidden = 1
    pm.hidden_reason = reason
    db.flush()
    return pm


def update_project_member(
    db: Session,
    project_id: int,
    member_id: int,
    role: str | None = None,
    description: str | None = None,
    expected_end_date: date | None = None,
    is_hidden: bool | None = None,
    hidden_reason: str | None = None,
) -> ProjectMember:
    pm = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.member_id == member_id)
        .first()
    )
    if not pm:
        raise not_found("Assignment")
    if role is not None:
        pm.role = role
    if description is not None:
        pm.description = description
    if expected_end_date is not None:
        pm.expected_end_date = expected_end_date
    if is_hidden is not None:
        pm.is_hidden = 1 if is_hidden else 0
        if not is_hidden:
            pm.hidden_reason = None
    if hidden_reason is not None:
        pm.hidden_reason = hidden_reason
    db.flush()
    return pm


def assign_task_member(
    db: Session,
    task_id: int,
    member_id: int,
    role: str,
    expected_end_date: date | None,
    enforce_project_membership: bool = False,
) -> tuple[TaskMember, str]:
    task = db.query(Task).filter(Task.id == task_id, Task.is_deleted == 0).first()
    if not task:
        raise not_found("Task")
    _ensure_member_active(db, member_id)

    if enforce_project_membership:
        pm = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == task.project_id,
                ProjectMember.member_id == member_id,
                ProjectMember.is_hidden == 0,
            )
            .first()
        )
        if not pm:
            raise validation_error("Member chưa thuộc project chứa task này")

    existing = (
        db.query(TaskMember)
        .filter(TaskMember.task_id == task_id, TaskMember.member_id == member_id)
        .first()
    )
    if existing:
        if not existing.is_hidden:
            raise already_assigned("Member đã có trong task này")
        existing.is_hidden = 0
        existing.hidden_reason = None
        existing.role = role
        existing.expected_end_date = expected_end_date
        db.flush()
        return existing, "unhidden"

    new_tm = TaskMember(
        task_id=task_id,
        member_id=member_id,
        role=role,
        expected_end_date=expected_end_date,
    )
    db.add(new_tm)
    db.flush()
    return new_tm, "created"


def hide_task_member(
    db: Session, task_id: int, member_id: int, reason: str | None = None
) -> TaskMember:
    tm = (
        db.query(TaskMember)
        .filter(TaskMember.task_id == task_id, TaskMember.member_id == member_id)
        .first()
    )
    if not tm:
        raise not_found("Assignment")
    tm.is_hidden = 1
    tm.hidden_reason = reason
    db.flush()
    return tm


def update_task_member(
    db: Session,
    task_id: int,
    member_id: int,
    role: str | None = None,
    expected_end_date: date | None = None,
    is_hidden: bool | None = None,
    hidden_reason: str | None = None,
) -> TaskMember:
    tm = (
        db.query(TaskMember)
        .filter(TaskMember.task_id == task_id, TaskMember.member_id == member_id)
        .first()
    )
    if not tm:
        raise not_found("Assignment")
    if role is not None:
        tm.role = role
    if expected_end_date is not None:
        tm.expected_end_date = expected_end_date
    if is_hidden is not None:
        tm.is_hidden = 1 if is_hidden else 0
        if not is_hidden:
            tm.hidden_reason = None
    if hidden_reason is not None:
        tm.hidden_reason = hidden_reason
    db.flush()
    return tm
