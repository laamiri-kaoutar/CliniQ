from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.db.database import get_db
from app.db.models.user import User
from app.services.query_service import query_service
from app.schemas.query import QueryBase, QueryResponse

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
def post_medical_query(
    query_in: QueryBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    try:
        return query_service.create_medical_query(
            db=db, 
            user=current_user, 
            query_text=query_in.query_text
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur RAG : {str(e)}"
        )

@router.get("/history", response_model=list[QueryResponse])
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # All logic is hidden in the service
    return query_service.get_user_query_history(db, current_user.id)