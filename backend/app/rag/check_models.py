import os
import re
from docling.document_converter import DocumentConverter
from langchain_text_splitters import MarkdownHeaderTextSplitter

PDF_PATH = "/app/data/raw_pdfs/guide_medical.pdf"

def test_flattened_chunking():
    if not os.path.exists(PDF_PATH):
        print(f"❌ File not found at {PDF_PATH}")
        return

    print("📄 Converting PDF to Markdown...")
    converter = DocumentConverter()
    result = converter.convert(PDF_PATH)
    markdown_content = result.document.export_to_markdown()

    # Split only on ## because your PDF uses it for every main title
    headers_to_split_on = [("##", "header_title")]
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)
    
    print("✂️ Splitting into chunks...")
    raw_chunks = splitter.split_text(markdown_content)

    final_test_docs = []
    current_service = "Général"
    
    # List of keywords that represent a main medical category
    service_keywords = ["PÉDIATRIE", "DENTAIRE", "MÉDECINE", "URGENCE"]

    for chunk in raw_chunks:
        header = chunk.metadata.get("header_title", "").strip()
        header_upper = header.upper()

        # Update the 'Service' only when we hit a major section header
        if any(keyword in header_upper for keyword in service_keywords):
            current_service = header
        
        # Build the final metadata and page content
        chunk.metadata["service"] = current_service
        chunk.metadata["section"] = header
        
        # We manually inject the service into the text so the retriever finds it easily
        context_prefix = f"DOMAINE: {current_service}\nSUJET: {header}\n"
        chunk.page_content = f"{context_prefix}---\n{chunk.page_content}"
        
        final_test_docs.append(chunk)

    print(f"✅ Generated {len(final_test_docs)} chunks.")
    print("\n" + "🔍 " * 5 + " RESULTS CHECK " + "🔍 " * 5)
    
    for i, doc in enumerate(final_test_docs[:10]):
        # Cleaning the text here to avoid the f-string backslash error
        clean_text = doc.page_content[:200].replace('\n', ' ')
        
        print(f"\n📦 [CHUNK {i+1}]")
        print(f"  🔹 Metadata Service: {doc.metadata['service']}")
        print(f"  🔹 Metadata Section: {doc.metadata['section']}")
        print(f"  📝 Preview: {clean_text}...")
        print("-" * 50)

if __name__ == "__main__":
    test_flattened_chunking()