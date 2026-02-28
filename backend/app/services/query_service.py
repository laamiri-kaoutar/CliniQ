import mlflow
from sqlalchemy.orm import Session
from app.rag.pipeline import MedicalPipeline
from app.db.models.query import Query
from app.db.models.user import User
from app.core.config import settings

class QueryService:
    def __init__(self):
        self.pipeline = MedicalPipeline()
        
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        mlflow.set_experiment("ProtoCare_Clinical_Decision_Support")
    
    def create_medical_query(self, db: Session, user: User, query_text: str):
        with mlflow.start_run(run_name=f"Dr_{user.username}_Query"):
            self.pipeline.retriever.log_params()
            self.pipeline.generator.log_params()
            
            result = self.pipeline.search(query_text)
            
            
            raw_answer = result["answer"]
            if isinstance(raw_answer, list) and len(raw_answer) > 0:
                
                final_answer_text = raw_answer[0].get('text', str(raw_answer))
            else:
                final_answer_text = str(raw_answer)
            
            mlflow.log_param("user_id", user.id)
            mlflow.log_param("original_query", query_text)
            mlflow.log_metric("source_chunks_found", len(result["sources"]))
            
            
            new_query = Query(
                query_text=query_text,
                response_text=final_answer_text, 
                user_id=user.id
            )
            db.add(new_query)
            db.commit()
            db.refresh(new_query)
    
            # return {
            #     "id": new_query.id,
            #     "answer": final_answer_text,
            #     "sources": result["sources"],
            #     "created_at": new_query.created_at
            # }

            return {
            "id": new_query.id,
            "query_text": query_text,           
            "response_text": final_answer_text, 
            "sources": result["sources"],
            "created_at": new_query.created_at
            }
  
    def get_user_query_history(self, db: Session, user_id: int):
        return db.query(Query).filter(
            Query.user_id == user_id
        ).order_by(Query.created_at.desc()).all()
query_service = QueryService()