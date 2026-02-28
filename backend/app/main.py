from fastapi import FastAPI
from app.db.database import engine, Base
from app.db.models import user
from app.api.endpoints import auth, chat 
from prometheus_fastapi_instrumentator import Instrumentator

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CliniQ API", version="1.0.0")

app.include_router(auth.router, prefix="/auth", tags=["Authentification"])
app.include_router(chat.router, prefix="/chat", tags=["RAG Assistant"])

# pour exposer les métriques
Instrumentator().instrument(app).expose(app)

@app.get("/")
def read_root():
    return {"status": "success", "message": "L'API CliniQ est prête !"}