from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.errors import not_found
from ...core.response import ok
from ...database import get_db
from ...models import Role
from ...schemas.role import RoleCreate, RoleOut, RoleUpdate
from ..deps import admin_only

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("")
def list_roles(db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    return ok([RoleOut.model_validate(r) for r in roles])


@router.post("", status_code=201, dependencies=[Depends(admin_only)])
def create_role(payload: RoleCreate, db: Session = Depends(get_db)):
    r = Role(name=payload.name, description=payload.description)
    db.add(r)
    db.commit()
    db.refresh(r)
    return ok(RoleOut.model_validate(r))


@router.patch("/{role_id}", dependencies=[Depends(admin_only)])
def update_role(role_id: int, payload: RoleUpdate, db: Session = Depends(get_db)):
    r = db.query(Role).filter(Role.id == role_id).first()
    if not r:
        raise not_found("Role")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return ok(RoleOut.model_validate(r))


@router.delete("/{role_id}", dependencies=[Depends(admin_only)])
def delete_role(role_id: int, db: Session = Depends(get_db)):
    r = db.query(Role).filter(Role.id == role_id).first()
    if not r:
        raise not_found("Role")
    db.delete(r)
    db.commit()
    return ok({"id": role_id}, message="Đã xóa role")

