import os
import json
import time
import re
import mlflow
from deepeval.metrics import (
    FaithfulnessMetric, 
    AnswerRelevancyMetric, 
    ContextualPrecisionMetric, 
    ContextualRecallMetric
)
from deepeval.test_case import LLMTestCase
from deepeval.models.base_model import DeepEvalBaseLLM
from langchain_groq import ChatGroq
from app.rag.pipeline import MedicalPipeline
from app.core.config import settings

# --- Wrapper DeepEval pour Groq ---
class GroqDeepEvalWrapper(DeepEvalBaseLLM):
    def __init__(self, model_name):
        self.model = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=model_name,
            temperature=0,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        self.model_name = model_name

    def load_model(self):
        return self.model

    def _extract_json(self, text: str) -> str:
        # Nettoyage Regex pour garantir que DeepEval reçoit du JSON pur
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            return match.group(1)
        return text

    def generate(self, prompt: str) -> str:
        # Pause de sécurité avant chaque appel interne de métrique
        time.sleep(2) 
        instruction = "You are a specialized JSON generator. Respond ONLY with a valid JSON object. No prose."
        full_prompt = f"{instruction}\n\n{prompt}"
        
        for attempt in range(3):
            try:
                content = self.model.invoke(full_prompt).content
                return self._extract_json(content)
            except Exception as e:
                if "429" in str(e):
                    print(f"⏳ Rate limit atteint, attente 10s (essai {attempt+1})...")
                    time.sleep(10)
                else:
                    raise e
        return ""

    async def a_generate(self, prompt: str) -> str:
        instruction = "You are a specialized JSON generator. Respond ONLY with a valid JSON object. No prose."
        full_prompt = f"{instruction}\n\n{prompt}"
        res = await self.model.ainvoke(full_prompt)
        return self._extract_json(res.content)

    def get_model_name(self):
        return self.model_name

def evaluate_project():
    pipeline = MedicalPipeline()
    # On reste sur le 8b pour éviter les saturations de quota du 70b
    eval_llm = GroqDeepEvalWrapper(model_name="llama-3.1-8b-instant")
    
    with open('data/test_cases.json', 'r', encoding='utf-8') as f:
        test_cases = json.load(f)

    mlflow.set_experiment("ProtoCare_DeepEval_Full_Audit")

    # Initialisation de TOUTES les métriques demandées
    faith_metric = FaithfulnessMetric(threshold=0.7, model=eval_llm)
    relevancy_metric = AnswerRelevancyMetric(threshold=0.7, model=eval_llm)
    precision_metric = ContextualPrecisionMetric(threshold=0.7, model=eval_llm)
    recall_metric = ContextualRecallMetric(threshold=0.7, model=eval_llm)

    print(f"📊 Début de l'audit complet sur {len(test_cases)} cas...")

    for i, case in enumerate(test_cases):
        print(f"\n🔍 Évaluation Cas #{i+1} : {case['question'][:50]}...")
        
        try:
            # Exécution du pipeline (Gemini)
            result = pipeline.search(case['question'])
            
            # Nettoyage de la réponse
            raw_answer = result['answer']
            actual_output = raw_answer[0].get('text', str(raw_answer)) if isinstance(raw_answer, list) and len(raw_answer) > 0 else str(raw_answer)

            # Nettoyage du contexte
            retrieval_context = [
                doc.get('page_content', str(doc)) if isinstance(doc, dict) else str(doc)
                for doc in result['sources']
            ]
            
            # Création du Test Case complet
            test_case = LLMTestCase(
                input=case['question'],
                actual_output=actual_output,
                expected_output=str(case['expected_output']),
                retrieval_context=retrieval_context
            )

            # Mesure des métriques
            print("⚖️ Calcul des 4 métriques via Groq...")
            faith_metric.measure(test_case)
            relevancy_metric.measure(test_case)
            precision_metric.measure(test_case)
            recall_metric.measure(test_case)

            with mlflow.start_run(run_name=f"Audit_Full_Case_{i+1}"):
                # 1. Logger les paramètres et métriques
                mlflow.log_param("question", case['question'])
                mlflow.log_metric("faithfulness", faith_metric.score)
                mlflow.log_metric("answer_relevance", relevancy_metric.score)
                mlflow.log_metric("contextual_precision", precision_metric.score)
                mlflow.log_metric("contextual_recall", recall_metric.score)
                
                # 2. Logger les textes pour comparaison visuelle
                mlflow.log_text(actual_output, "actual_response.txt")
                mlflow.log_text(str(case['expected_output']), "expected_response.txt")
                
                # 3. Logger les raisons du juge
                mlflow.log_text(str(faith_metric.reason), "debug/faithfulness_reason.txt")
                mlflow.log_text(str(relevancy_metric.reason), "debug/relevancy_reason.txt")
                
                # 4. Logger le contexte utilisé
                mlflow.log_text("\n---\n".join(retrieval_context), "retrieval_context.txt")
                
                print(f"✅ Scores Cas #{i+1}: Faith={faith_metric.score} | Rel={relevancy_metric.score} | Prec={precision_metric.score} | Rec={recall_metric.score}")

        except Exception as e:
            print(f"❌ Erreur lors de l'évaluation du cas {i+1}: {str(e)}")

        # Pause longue entre chaque cas pour réinitialiser le quota TPM de Groq
        print("⏳ Pause de 15s pour le Rate Limit...")
        time.sleep(15)

if __name__ == "__main__":
    evaluate_project()