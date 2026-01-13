from dotenv import load_dotenv
load_dotenv()   # ← SABSE PEHLE

from fastapi import FastAPI, Depends
from threading import Thread
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
init_db()       # ← MONGO INIT HERE (ONCE)

from .auth import router as auth_router
from .auth_guard import get_current_user
from .projects import router as project_router
from .logs import router as logs_router
from .incidents import router as incidents_router

from .incident_resolver import run_resolver

app = FastAPI(title="RADAR-AI API Gateway")

Thread(target=run_resolver, daemon=True).start()

# PUBLIC
app.include_router(auth_router, prefix="/auth")
app.include_router(logs_router)

# PROTECTED
app.include_router(project_router, dependencies=[Depends(get_current_user)])
app.include_router(incidents_router, dependencies=[Depends(get_current_user)])


@app.get("/health")
def health():
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
