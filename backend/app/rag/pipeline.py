import time
from prometheus_client import Counter, Gauge, Histogram
from app.rag.retriever import MedicalRetriever
from app.rag.generator import MedicalGenerator

# Initialisation des métriques applicatives pour Prometheus
RAG_REQUEST_COUNT = Counter('rag_requests_total', 'Nombre total de requêtes RAG')
RAG_FAITHFULNESS = Gauge('rag_faithfulness_score', 'Score de fidélité de la réponse')
RAG_LATENCY = Histogram('rag_generation_latency_seconds', 'Temps de réponse total du pipeline')

class MedicalPipeline:
    def __init__(self):
        self.retriever = MedicalRetriever()
        self.generator = MedicalGenerator()

    def search(self, query: str):
        # Incrémenter le compteur de requêtes
        RAG_REQUEST_COUNT.inc()
        start_time = time.time()

        print("\n" + "="*50)
        print(f"🚀 PIPELINE : {query}")
        print("="*50)

        # 1. Get clinical chunks (Expansion + Retrieval + Reranking)
        docs = self.retriever.get_relevant_documents(query)

        # 2. Generate final clinical answer
        answer = self.generator.generate(query, docs)

        # Enregistrement de la latence
        latency = time.time() - start_time
        RAG_LATENCY.observe(latency)

        # Mise à jour de la jauge de qualité (Initialisée à 1.0 par défaut)
        # Cette valeur sera surveillée par vos alertes Prometheus
        RAG_FAITHFULNESS.set(1.0) 

        return {
            "answer": answer,
            "sources": [doc.metadata for doc in docs]
        }

# if __name__ == "__main__":
#     pipeline = MedicalPipeline()
#     res = pipeline.search("Quels sont les signes d'une fièvre mal supportée en pédiatrie ?")
#     print(f"\n✅ RÉPONSE FINALE :\n{res['answer']}")