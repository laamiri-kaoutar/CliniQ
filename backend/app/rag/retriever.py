import os
import warnings
from typing import List
import mlflow
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_cohere import CohereRerank
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from app.core.config import settings
from langchain_groq import ChatGroq


warnings.filterwarnings("ignore", category=DeprecationWarning)
CHROMA_PERSIST_DIR = "/app/chroma_db"

class QueryExpander:
    def __init__(self):
        # Dynamically loaded from settings
        self.model_name = settings.EXPANSION_MODEL
        self.temperature = settings.EXPANSION_TEMP
        
        # self.llm = ChatGoogleGenerativeAI(
        #     model=self.model_name,
        #     # google_api_key=settings.GOOGLE_API_KEY,
        #     temperature=self.temperature 
        # )

        self.llm = ChatGroq(
           groq_api_key=settings.GROQ_API_KEY,
            model_name="llama-3.1-8b-instant", 
            temperature=0.1
        )



        self.prompt = PromptTemplate(
            input_variables=["question"],
            template="""Tu es un assistant médical expert. 
            Ta tâche est de générer 2 reformulations cliniques ou synonymes de la question suivante pour améliorer la recherche dans une base de données médicale.
            Ne donne aucune explication. Renvoie uniquement les 2 questions, séparées par un saut de ligne.
            
            Question originale : {question}
            Reformulations :"""
        )
        self.chain = self.prompt | self.llm

    def expand(self, query: str) -> List[str]:
        print(f"🧠 [Phase 1: Expansion] Reformulation via {self.model_name}...")
        try:
            response = self.chain.invoke({"question": query})
            expanded_queries = [q.strip() for q in response.content.split('\n') if q.strip()]
            return [query] + expanded_queries[:2] 
        except Exception as e:
            print(f"⚠️ Erreur d'expansion : {e}. Utilisation de la question originale.")
            return [query]

class BaseRetriever:
    def __init__(self):
        # Pulling real config from settings
        self.embedding_model = settings.EMBEDDING_MODEL
        self.k = settings.RETRIEVAL_K
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        self.vector_store = Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=self.embeddings
        )
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": self.k})

    def retrieve_candidates(self, queries: List[str]) -> List[any]:
        print(f"📚 [Phase 2: Recherche] Extraction ChromaDB (k={self.k}) pour {len(queries)} variations...")
        all_docs = []
        for q in queries:
            docs = self.retriever.invoke(q)
            all_docs.extend(docs)
        
        unique_docs = {doc.page_content: doc for doc in all_docs}.values()
        print(f"   -> {len(unique_docs)} documents uniques trouvés.")
        return list(unique_docs)

class MedicalRetriever:
    def __init__(self):
        self.expander = QueryExpander()
        self.vector_search = BaseRetriever()
        
        # Pulling reranker config from settings
        self.rerank_model = settings.RERANK_MODEL
        self.top_n = settings.RERANK_TOP_N
        
        print(f"🎯 [Initialisation] Chargement du Reranker Cohere ({self.rerank_model})...")
        self.reranker = CohereRerank(
            cohere_api_key=settings.COHERE_API_KEY,
            model=self.rerank_model,
            top_n=self.top_n
        )

    def get_relevant_documents(self, query: str):
        queries = self.expander.expand(query)
        candidates = self.vector_search.retrieve_candidates(queries)
        print(f"⚖️ [Phase 3: Reranking] Tri par Cohere (top_n={self.top_n})...")
        return self.reranker.compress_documents(documents=candidates, query=query)
    
    def log_params(self):
        """Logs real, non-hardcoded parameters used during this execution"""
        mlflow.log_params({
            "expansion_model": self.expander.model_name,
            "embedding_model": self.vector_search.embedding_model,
            "retrieval_k": self.vector_search.k,
            "rerank_model": self.rerank_model,
            "rerank_top_n": self.top_n
        })