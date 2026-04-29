from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.errors import not_found, validation_error
from ...core.response import ok
from ...database import get_db
from ...models import Department, Member, Project
from ...schemas.department import DepartmentCreate, DepartmentOut, DepartmentUpdate
from ..deps import admin_only

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("")
def list_departments(
    q: str | None = None,
    include_deleted: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(Department)
    if not include_deleted:
        query = query.filter(Department.is_deleted == 0)
    if q:
        like = f"%{q}%"
        query = query.filter((Department.name.ilike(like)) | (Department.code.ilike(like)))
    items = query.order_by(Department.id.desc()).all()
    return ok([DepartmentOut.model_validate(d) for d in items], meta={"total": len(items)})


@router.post("", status_code=201, dependencies=[Depends(admin_only)])
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db)):
    code = payload.code.strip().upper()
    exists = db.query(Department).filter(Department.code == code).first()
    if exists:
        raise validation_error("Code đã tồn tại", field="code")
    d = Department(name=payload.name.strip(), code=code)
    db.add(d)
    db.commit()
    db.refresh(d)
    return ok(DepartmentOut.model_validate(d), message="Tạo bộ phận thành công")


@router.get("/{dept_id}")
def get_department(dept_id: int, db: Session = Depends(get_db)):
    d = db.query(Department).filter(Department.id == dept_id).first()
    if not d:
        raise not_found("Department")
    return ok(DepartmentOut.model_validate(d))


@router.patch("/{dept_id}", dependencies=[Depends(admin_only)])
def update_department(dept_id: int, payload: DepartmentUpdate, db: Session = Depends(get_db)):
    d = db.query(Department).filter(Department.id == dept_id).first()
    if not d:
        raise not_found("Department")
    if payload.name is not None:
        d.name = payload.name.strip()
    if payload.code is not None:
        code = payload.code.strip().upper()
        other = db.query(Department).filter(Department.code == code, Department.id != dept_id).first()
        if other:
            raise validation_error("Code đã tồn tại", field="code")
        d.code = code
    db.commit()
    db.refresh(d)
    return ok(DepartmentOut.model_validate(d), message="Cập nhật thành công")


@router.delete("/{dept_id}", dependencies=[Depends(admin_only)])
def delete_department(dept_id: int, db: Session = Depends(get_db)):
    d = db.query(Department).filter(Department.id == dept_id).first()
    if not d:
        raise not_found("Department")
    has_members = (
        db.query(Member).filter(Member.department_id == dept_id, Member.is_deleted == 0).count()
    )
    has_projects = (
        db.query(Project).filter(Project.department_id == dept_id, Project.is_deleted == 0).count()
    )
    if has_members or has_projects:
        raise validation_error(
            "Không thể xóa bộ phận đang có member/project active"
        )
    d.is_deleted = 1
    db.commit()
    return ok({"id": dept_id}, message="Đã xóa")
