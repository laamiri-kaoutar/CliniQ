import os
import re
import mlflow
from docling.document_converter import DocumentConverter
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from app.core.config import settings

# Configuration from paths
PDF_PATH = "/app/data/raw_pdfs/guide_medical.pdf"
CHROMA_PERSIST_DIR = "/app/chroma_db"

def process_medical_pdf(pdf_path: str):
    print(f"Converting PDF: {pdf_path}")
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    markdown_content = result.document.export_to_markdown()

    # Strategy: Markdown Header-Based Segmentation
    headers_to_split_on = [("##", "header_title")]
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on, 
        strip_headers=False
    )
    
    raw_chunks = splitter.split_text(markdown_content)
    final_documents = []
    current_service = "Général"
    
    service_keywords = ["PÉDIATRIE", "DENTAIRE", "MÉDECINE", "URGENCE"]

    for chunk in raw_chunks:
        header = chunk.metadata.get("header_title", "").strip()
        header_upper = header.upper()

        if any(keyword in header_upper for keyword in service_keywords):
            current_service = header
        
        chunk.metadata["service"] = current_service
        chunk.metadata["section"] = header
        chunk.metadata["source"] = pdf_path
        
        context_prefix = f"DOMAINE: {current_service}\nSUJET: {header}\n"
        chunk.page_content = f"{context_prefix}---\n{chunk.page_content}"
        chunk.page_content = re.sub(r'\n{3,}', '\n\n', chunk.page_content)
        
        final_documents.append(chunk)

    return final_documents

def ingest_to_chroma():
    if not os.path.exists(PDF_PATH):
        print(f"Error: PDF not found at {PDF_PATH}")
        return

    # --- MLflow Ingestion Logging ---
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    mlflow.set_experiment("ProtoCare_Data_Ingestion")

    with mlflow.start_run(run_name="Ingestion_Guide_Medical"):
        # Logging Chunking Strategy
        mlflow.log_params({
            "chunk_strategy": "Markdown_Header_Splitter",
            "header_level": "H2 (##)",
            "context_injection": "True",
            "source_file": os.path.basename(PDF_PATH)
        })

        # Process chunks
        chunks = process_medical_pdf(PDF_PATH)
        print(f"Generated {len(chunks)} semantic blocks.")
        mlflow.log_metric("total_chunks", len(chunks))

        # Initialize Embedding Model using Settings
        print(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        embeddings_model = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'}, 
            encode_kwargs={'normalize_embeddings': True}
        )

        # Logging Embedding Hyperparameters
        mlflow.log_params({
            "embedding_model": settings.EMBEDDING_MODEL,
            "dimension": 1024, # BGE-M3 standard
            "normalization": "True"
        })  

        # Persist to vector store
        print(f"Saving to vector store: {CHROMA_PERSIST_DIR}")
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings_model,
            persist_directory=CHROMA_PERSIST_DIR
        )
        
        # Save the LangChain pipeline structure to MLflow
        mlflow.log_artifact(PDF_PATH, "source_documents")
        
        print("Ingestion complete. Metrics logged to MLflow.")

if __name__ == "__main__":
    ingest_to_chroma()