from fastapi import APIRouter

from . import assignments, auth, calendar, departments, members, projects, roles, search, settings, tasks, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(departments.router)
api_router.include_router(members.router)
api_router.include_router(projects.router)
api_router.include_router(tasks.router)
api_router.include_router(assignments.router)
api_router.include_router(roles.router)
api_router.include_router(search.router)
api_router.include_router(settings.router)
api_router.include_router(calendar.router)
