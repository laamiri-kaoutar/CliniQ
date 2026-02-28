# from langchain.prompts import PromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from langchain_groq import ChatGroq
import mlflow

class MedicalGenerator:
    def __init__(self):
        # Dynamically pulling configuration from settings
        self.model_name = settings.GENERATOR_MODEL
        self.temperature = settings.GENERATOR_TEMP
        
        # self.llm = ChatGoogleGenerativeAI(
        #     model=self.model_name,
        #     # google_api_key=settings.GOOGLE_API_KEY,
        #     temperature=self.temperature  
        # )

        self.llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile",
            temperature=0.2
        )
        
        template = """VOUS ÊTES UN EXPERT EN AIDE À LA DÉCISION CLINIQUE (CDSS).
        Votre mission est de transformer des extraits de protocoles en une réponse synthétique, lisible et actionnable pour un médecin urgentiste.
        
        CADRE STRICT :
        1. BASE DE CONNAISSANCE : Utilisez UNIQUEMENT le contexte fourni. Ne faites appel à aucune connaissance externe.
        2. ABSENCE D'INFO : Si le contexte ne contient pas la réponse exacte, dites : "Les protocoles actuels ne contiennent pas d'information permettant de répondre à cette question."
        3. FORMATAGE UI : Évitez les tableaux bruts. Utilisez des titres en gras, des listes à puces aérées et des sauts de ligne clairs.
        
        RÈGLES D'URGENCE (PRIORITÉ ABSOLUE) :
        - Si le contexte mentionne "Référer SAMU", "Urgence Vitale", ou "Avis spécialisé urgent", commencez la réponse par la mention "🚨 **URGENCE : RÉFÉRER SAMU IMMÉDIATEMENT**" en gras et en rouge (texte).
        
        STRUCTURE DE LA RÉPONSE :
        - **Alerte :** (Si applicable)
        - **Synthèse Clinique :** Une explication fluide en 2-3 phrases.
        - **Actions Immédiates :** Liste à puces des gestes à faire.
        - **Points de Vigilance :** Signes de gravité à surveiller.
        
        CONTEXTE MÉDICAL :
        {context}
        
        QUESTION DU PRATICIEN :
        {question}
        
        RÉPONSE CLINIQUE (SYNTHÈSE PROFESSIONNELLE) :"""

        self.prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Chain composition using LCEL
        self.chain = self.prompt | self.llm

    def generate(self, question, docs):
        # Synthesis of top-ranked clinical chunks
        context_text = "\n\n".join([doc.page_content for doc in docs])
        
        print(f"✍️ [Phase 4: Génération] Synthèse clinique via {self.model_name}...")
        response = self.chain.invoke({"context": context_text, "question": question})
        
        return response.content
    
    def log_params(self):
        """Logs the actual live parameters to MLflow"""
        mlflow.log_params({
            "generator_model": self.model_name,
            "generator_temperature": self.temperature,
            "template_version": "v1-clinical-strict"
        })