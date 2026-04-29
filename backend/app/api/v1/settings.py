from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...database import get_db
from ...models.settings import SystemSettings
from ..deps import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])

class SettingsUpdate(BaseModel):
    idle_report_enabled: bool
    idle_report_morning_time: str
    idle_report_evening_time: str
    late_report_enabled: bool
    late_report_time: str
    chatops_pm_group_id: str | None = None

@router.get("")
def get_settings(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # Settings should be viewable by anyone, or only admin?
    # Usually admin edits, but viewing could be restricted or not.
    # Let's restrict to system_role == 'admin' for write, but allow read for all authenticated users to see what's configured,
    # or just admin for both. The user said: "cho phép admin cấu hình" (allow admin to configure).
    settings = db.query(SystemSettings).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    return {
        "success": True,
        "data": {
            "idle_report_enabled": settings.idle_report_enabled,
            "idle_report_morning_time": settings.idle_report_morning_time,
            "idle_report_evening_time": settings.idle_report_evening_time,
            "late_report_enabled": settings.late_report_enabled,
            "late_report_time": settings.late_report_time,
            "chatops_pm_group_id": settings.chatops_pm_group_id,
        }
    }

@router.put("")
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.system_role.value != 'admin':
        raise HTTPException(status_code=403, detail="Chỉ admin mới có quyền cấu hình hệ thống")
        
    settings = db.query(SystemSettings).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
        
    settings.idle_report_enabled = data.idle_report_enabled
    settings.idle_report_morning_time = data.idle_report_morning_time
    settings.idle_report_evening_time = data.idle_report_evening_time
    settings.late_report_enabled = data.late_report_enabled
    settings.late_report_time = data.late_report_time
    settings.chatops_pm_group_id = data.chatops_pm_group_id
    
    db.commit()
    
    return {"success": True, "message": "Cập nhật cấu hình thành công"}

from ...services.scheduler import run_idle_report, run_late_tasks_report

@router.post("/run-idle-report")
async def api_run_idle_report(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.system_role.value != 'admin':
        raise HTTPException(status_code=403, detail="Chỉ admin mới có quyền thực thi")
    settings = db.query(SystemSettings).first()
    if not settings or not settings.chatops_pm_group_id:
        raise HTTPException(status_code=400, detail="Chưa cấu hình ChatOps Group ID")
        
    success = await run_idle_report(db, settings.chatops_pm_group_id)
    if not success:
        raise HTTPException(status_code=500, detail="Lỗi khi gửi ChatOps. Vui lòng kiểm tra lại Token hoặc ID nhóm.")
    return {"success": True, "message": "Đã gửi báo cáo thành viên rảnh rỗi"}

@router.post("/run-late-report")
async def api_run_late_report(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.system_role.value != 'admin':
        raise HTTPException(status_code=403, detail="Chỉ admin mới có quyền thực thi")
    settings = db.query(SystemSettings).first()
    if not settings or not settings.chatops_pm_group_id:
        raise HTTPException(status_code=400, detail="Chưa cấu hình ChatOps Group ID")
        
    success = await run_late_tasks_report(db, settings.chatops_pm_group_id)
    if not success:
        raise HTTPException(status_code=500, detail="Lỗi khi gửi ChatOps. Vui lòng kiểm tra lại Token hoặc ID nhóm.")
    return {"success": True, "message": "Đã gửi báo cáo task trễ hạn"}
