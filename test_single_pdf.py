#!/usr/bin/env python3
"""
Test script to process a single PDF and identify where it fails
"""
import os
import sys
import traceback
from pathlib import Path

# Add current path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_single_pdf_processing():
    """Test processing of a single PDF file"""
    pdf_file = "documenti_da_processare/attention-deficit-hyperactivity-disorder.pdf"

    if not os.path.exists(pdf_file):
        print(f"❌ File not found: {pdf_file}")
        return

    print(f"🔍 Testing processing of: {pdf_file}")

    try:
        # Step 1: Test text extraction
        print("\n1️⃣ Testing text extraction...")
        from archivista_processing import extract_text_from_pdf
        text = extract_text_from_pdf(pdf_file)
        print(f"✅ Text extraction successful: {len(text)} characters")
        print(f"📄 Preview: {text[:200]}...")

        # Step 2: Test LLM classification
        print("\n2️⃣ Testing LLM classification...")
        from archivista_processing import classify_document
        from llama_index.core import Settings
        from config import initialize_services

        initialize_services()
        if not Settings.llm:
            print("❌ LLM not configured")
            return

        category = classify_document(text)
        print(f"✅ Classification successful: {category}")

        # Step 3: Test metadata extraction
        print("\n3️⃣ Testing metadata extraction...")
        from archivista_processing import PaperMetadata
        from llama_index.core import PromptTemplate
        import prompt_manager
        import json

        metadata_prompt = PromptTemplate(prompt_manager.get_prompt("PYDANTIC_METADATA_PROMPT"))
        category_name = "Test Category"  # Simplified for testing
        metadata_query = metadata_prompt.format(document_text=text[:4000], category_name=category_name)
        response = Settings.llm.complete(metadata_query)
        print(f"🔍 LLM raw response: '{str(response)}'")

        try:
            metadata = PaperMetadata(**json.loads(str(response)))
            print(f"✅ Metadata extraction successful: {metadata.title}")
        except Exception as e:
            print(f"⚠️ Metadata extraction had issues: {e}")
            print(f"   Trying to parse as JSON: {repr(str(response))}")
            metadata = PaperMetadata(title=os.path.basename(pdf_file), authors=[], publication_year=None)

        # Step 4: Test indexing
        print("\n4️⃣ Testing indexing...")
        from llama_index.core import Document, VectorStoreIndex, StorageContext
        from llama_index.core.storage.docstore import SimpleDocumentStore
        from llama_index.core.storage.index_store import SimpleIndexStore
        from llama_index.core.vector_stores import SimpleVectorStore

        doc = Document(text=text)
        doc.metadata.update({
            "file_name": os.path.basename(pdf_file),
            "title": metadata.title,
            "authors": json.dumps(metadata.authors),
            "publication_year": metadata.publication_year,
            "category_id": category,
            "category_name": category_name
        })

        storage_context = StorageContext.from_defaults(
            docstore=SimpleDocumentStore(),
            vector_store=SimpleVectorStore(),
            index_store=SimpleIndexStore(),
            persist_dir="db_memoria"
        )

        try:
            index = VectorStoreIndex.from_documents([doc], storage_context=storage_context)
            index.storage_context.persist(persist_dir="db_memoria")
            print("✅ Indexing successful")
        except Exception as e:
            print(f"❌ Indexing failed: {e}")
            print(f"   Traceback: {traceback.format_exc()}")

        print("\n🎉 All tests passed! The file should process successfully.")

    except Exception as e:
        print(f"❌ Error during processing: {e}")
        print(f"   Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_single_pdf_processing()
