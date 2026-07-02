from fastapi import APIRouter, HTTPException

dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@dashboard_router.get("/")
async def hello_word():
    """
    Função para validar funcionamento da rota. Está rota é para pegar dados para montagem de dashboards.
    """
    return HTTPException(status_code=202, detail="Rota de dados da Dashboard")