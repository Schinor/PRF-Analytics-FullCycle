from fastapi import APIRouter, HTTPException

ml_model_router = APIRouter(prefix="/ml_model", tags=["ml_model"])

@ml_model_router.get("/")
async def hello_word():
    """
    Função para validar funcionamento da rota. Rota para compartilhar dados para Machine Learning.
    """
    return HTTPException(status_code=202, detail="Rota de ML")