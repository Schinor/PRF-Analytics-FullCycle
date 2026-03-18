from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

from routers.dashboard import dashboard_router
from routers.ml_model import ml_model_router

app.include_router(dashboard_router)
app.include_router(ml_model_router)