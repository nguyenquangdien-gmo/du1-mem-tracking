import logging
from datetime import datetime, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import and_, not_
from ..database import SessionLocal
from ..models.settings import SystemSettings
from ..models.member import Member
from ..models.project import Project
from ..models.task import Task
from ..models.assignment import TaskMember
from .chatops import send_chatops_message

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def run_idle_report(db, group_id):
    if not group_id: return
    
    # Get all active members
    active_members = db.query(Member).filter(Member.is_deleted == 0).all()
    
    idle_members = []
    for member in active_members:
        # Check if member has active tasks
        active_tasks = db.query(Task).join(TaskMember, Task.id == TaskMember.task_id)\
            .filter(
                TaskMember.member_id == member.id,
                Task.status.notin_(['done', 'completed', 'cancelled', 'archived'])
            ).count()
            
        if active_tasks == 0:
            idle_members.append(member.full_name)
            
    if idle_members:
        # Sort by the last word (first name in VN)
        idle_members.sort(key=lambda x: x.strip().split()[-1].lower() if x.strip().split() else "")
        
        message = f"🚨 **Báo cáo thành viên rảnh rỗi ({datetime.now().strftime('%d/%m/%Y %H:%M')})**\n\n"
        message += "Các thành viên sau hiện không có task nào đang active:\n"
        for name in idle_members:
            message += f"- {name}\n"
            
        message += "Đề nghị các bạn TL/PM sắp xếp task cho các bạn.\n"
        success = await send_chatops_message(group_id, message)
        logger.info(f"Sent idle report for {len(idle_members)} members")
        return success
    return True

async def run_late_tasks_report(db, group_id):
    if not group_id: return False
    
    today = date.today()
    
    # Find late tasks in important projects
    late_tasks = db.query(Task, Project).join(Project, Task.project_id == Project.id)\
        .filter(
            Project.is_important == 1,
            Project.is_deleted == 0,
            Task.deadline < today,
            Task.status.notin_(['done', 'completed', 'cancelled', 'archived'])
        ).all()
        
    if late_tasks:
        message = f"⚠️ **Báo cáo Task trễ hạn - Dự án quan trọng ({today.strftime('%d/%m/%Y')})**\n\n"
        
        # Group by project
        proj_tasks = {}
        for task, proj in late_tasks:
            if proj.name not in proj_tasks:
                proj_tasks[proj.name] = []
            proj_tasks[proj.name].append(task)
            
        for p_name, tasks in proj_tasks.items():
            message += f"**{p_name}**:\n"
            for t in tasks:
                assignee_names = [m.member.full_name for m in t.members] if t.members else []
                # Sort by the last word (first name in VN)
                assignee_names.sort(key=lambda x: x.strip().split()[-1].lower() if x.strip().split() else "")
                assignees = ", ".join(assignee_names) if assignee_names else "Chưa assign"
                message += f"- [{t.status.upper()}] {t.name} (Deadline: {t.deadline.strftime('%d/%m/%Y')}) - Assignee: {assignees}\n"
            message += "\n"
            
        success = await send_chatops_message(group_id, message)
        logger.info(f"Sent late tasks report for {len(late_tasks)} tasks")
        return success
    return True

async def check_and_run_reports():
    db = SessionLocal()
    try:
        settings = db.query(SystemSettings).first()
        if not settings:
            return
            
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        
        # Idle report
        if settings.idle_report_enabled and now.weekday() < 5: # Mon-Fri
            if current_time_str == settings.idle_report_morning_time or current_time_str == settings.idle_report_evening_time:
                await run_idle_report(db, settings.chatops_pm_group_id)
                
        # Late tasks report
        if settings.late_report_enabled:
            if current_time_str == settings.late_report_time:
                await run_late_tasks_report(db, settings.chatops_pm_group_id)
                
    except Exception as e:
        logger.error(f"Error in scheduler check: {e}")
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(check_and_run_reports, 'cron', minute='*')
    scheduler.start()
    logger.info("Scheduler started.")
