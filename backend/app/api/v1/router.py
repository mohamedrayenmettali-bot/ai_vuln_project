from fastapi import APIRouter
from fastapi import Depends

from app.core.auth import get_current_user
from app.api.v1.endpoints import assignments, auth, defectdojo, epss, findings, health, llm, model, notifications, predict, projects

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(predict.router, dependencies=[Depends(get_current_user)])
api_router.include_router(model.router, dependencies=[Depends(get_current_user)])
api_router.include_router(epss.router, dependencies=[Depends(get_current_user)])
api_router.include_router(llm.router, dependencies=[Depends(get_current_user)])
api_router.include_router(defectdojo.router, dependencies=[Depends(get_current_user)])
api_router.include_router(notifications.router, dependencies=[Depends(get_current_user)])
api_router.include_router(projects.router, dependencies=[Depends(get_current_user)])
api_router.include_router(findings.router, dependencies=[Depends(get_current_user)])
api_router.include_router(assignments.router, dependencies=[Depends(get_current_user)])
