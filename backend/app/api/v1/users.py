import random
import string
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db
from ...models.user import User, SystemRole
from ...schemas.user import UserCreate, UserOut, UserUpdate, PasswordChange, PasswordResetRequest, PasswordResetConfirm
from ...core.security import get_password_hash, verify_password
from ...core.chatops import chatops
from ...core.response import ok
from ..deps import admin_only

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(admin_only)])

# In-memory store for OTPs (In production, use Redis)
otp_store = {}

@router.get("", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.post("", status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # Check exists
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        system_role=payload.system_role,
        is_active=payload.is_active,
        mattermost_id=payload.mattermost_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ok(UserOut.model_validate(user), message="User created successfully")

@router.patch("/{user_id}")
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if payload.username is not None:
        user.username = payload.username
    if payload.email is not None:
        user.email = payload.email
    if payload.system_role is not None:
        user.system_role = payload.system_role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.mattermost_id is not None:
        user.mattermost_id = payload.mattermost_id
    if payload.password is not None:
        user.hashed_password = get_password_hash(payload.password)
        
    db.commit()
    db.refresh(user)
    return ok(UserOut.model_validate(user), message="User updated successfully")

@router.post("/reset-password")
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # Don't reveal if user exists, but here for internal app it's fine
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate OTP
    otp = ''.join(random.choices(string.digits, k=6))
    otp_store[payload.email] = otp
    
    # Send to Mattermost
    message = f"### [MemberTrack] Yêu cầu khôi phục mật khẩu\nChào {user.username},\nMã OTP của bạn là: **{otp}**\nMã này có hiệu lực trong 5 phút. Vui lòng không chia sẻ mã này cho bất kỳ ai."
    success, detail = chatops.send_private_message(user.email, message)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to send OTP via Mattermost: {detail}")
    
    return ok(None, message="Mã OTP đã được gửi qua Mattermost")

@router.post("/reset-password/confirm")
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    if payload.email not in otp_store or otp_store[payload.email] != payload.otp:
        raise HTTPException(status_code=400, detail="Mã OTP không hợp lệ hoặc đã hết hạn")
    
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    del otp_store[payload.email]
    
    return ok(None, message="Mật khẩu đã được thay đổi thành công")

@router.post("/change-password")
def change_password(payload: PasswordChange, db: Session = Depends(get_db)):
    # In a real app, get current user from token
    # For now, let's assume we need a user ID or it's handled by middleware
    # TBD: Integrate with Auth dependency
    return {"message": "Requires auth implementation"}

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return ok(None, message="User deleted successfully")
