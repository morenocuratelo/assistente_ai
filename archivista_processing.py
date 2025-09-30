"""
Questo file contiene la logica di business principale per il processamento
dei documenti. La funzione qui definita viene registrata come task Celery.
"""
import os
import shutil
import sqlite3
import json
import time
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional

# Import per l'estrazione granulare del testo
import fitz
from docx import Document as DocxDocument
import pdfplumber
from pypdf import PdfReader
from pdfminer.high_level import extract_text as pdfminer_extract
from bs4 import BeautifulSoup
import chardet

from llama_index.core import Document, Settings, VectorStoreIndex, StorageContext, PromptTemplate, load_index_from_storage

from celery_app import celery_app
from celery.exceptions import SoftTimeLimitExceeded
from config import initialize_services
import prompt_manager # <-- MODIFICA: Importa il nuovo gestore dei prompt
import knowledge_structure
from file_utils import setup_database

# --- CONFIGURAZIONE ---
DOCS_TO_PROCESS_DIR = "documenti_da_processare"
CATEGORIZED_ARCHIVE_DIR = "Dall_Origine_alla_Complessita"
DB_STORAGE_DIR = "db_memoria"
METADATA_DB_FILE = os.path.join(DB_STORAGE_DIR, "metadata.sqlite")
ARCHIVISTA_STATUS_FILE = os.path.join(DB_STORAGE_DIR, "archivista_status.json")

# --- MODELLI DATI E FUNZIONI DI UTILITÀ ---

class PaperMetadata(BaseModel):
    title: str = Field(..., description="Il titolo completo e corretto dell'articolo.")
    authors: List[str] = Field(default_factory=list, description="La lista completa degli autori menzionati.")
    publication_year: Optional[int] = Field(None, description="L'anno di pubblicazione (solo il numero).")

def update_status(status, current_file=None):
    try:
        os.makedirs(DB_STORAGE_DIR, exist_ok=True) # Assicura che la directory esista
        with open(ARCHIVISTA_STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump({"status": status, "file": current_file, "timestamp": datetime.now().isoformat()}, f)
    except Exception as e:
        print(f"--> ERRORE aggiornamento stato: {e}")

def db_connect():
    conn = sqlite3.connect(METADATA_DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# --- FUNZIONI PER L'ESTRAZIONE DEL TESTO (invariate) ---
def extract_text_from_pdf(file_path: str) -> str:
    text_extractors = [("PyMuPDF", extract_text_pymupdf), ("PyPDF2", extract_text_pypdf2), ("pdfplumber", extract_text_pdfplumber), ("pdfminer", extract_text_pdfminer)]
    for name, func in text_extractors:
        try:
            text = func(file_path)
            if text and text.strip(): return text
        except Exception as e:
            print(f"✗ Errore con {name}: {e}")
    raise ValueError(f"Impossibile estrarre testo dal PDF {file_path}")

def extract_text_pymupdf(file_path: str) -> str:
    with fitz.open(file_path) as doc: return "".join(page.get_text() for page in doc)
def extract_text_pypdf2(file_path: str) -> str:
    with open(file_path, 'rb') as f: return "".join(p.extract_text() for p in PdfReader(f).pages)
def extract_text_pdfplumber(file_path: str) -> str:
    with pdfplumber.open(file_path) as pdf: return "".join(p.extract_text() or "" for p in pdf.pages)
def extract_text_pdfminer(file_path: str) -> str:
    return pdfminer_extract(file_path)
def extract_text_from_docx(file_path: str) -> str:
    return "\n".join(p.text for p in DocxDocument(file_path).paragraphs)
def extract_text_from_rtf(file_path: str) -> str:
    try:
        from striprtf.striprtf import rtf_to_text
        with open(file_path, 'r') as f:
            return rtf_to_text(f.read())
    except Exception: return ""
def extract_text_from_html(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f: return BeautifulSoup(f.read(), 'html.parser').get_text()
def extract_text_from_txt(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as f: return f.read()
    except UnicodeDecodeError:
        with open(file_path, 'rb') as f: raw = f.read()
        enc = chardet.detect(raw)['encoding']
        return raw.decode(enc or 'utf-8')

def get_text_extractor(file_extension: str):
    extractors = {'.pdf': extract_text_from_pdf, '.docx': extract_text_from_docx, '.rtf': extract_text_from_rtf, '.html': extract_text_from_html, '.htm': extract_text_from_html, '.txt': extract_text_from_txt}
    return extractors.get(file_extension.lower())

def classify_document(text_content):
    if not Settings.llm:
        raise ConnectionError("LLM non disponibile per la classificazione.")
    classification_structure = knowledge_structure.get_structure_for_prompt()
    # MODIFICA: Usa il prompt manager per caricare il template
    prompt_template = PromptTemplate(prompt_manager.get_prompt("DOCUMENT_CLASSIFICATION_PROMPT"))
    formatted_prompt = prompt_template.format(classification_structure=classification_structure, document_text=text_content[:8000])
    response = Settings.llm.complete(formatted_prompt)
    category_id = str(response).strip()
    return category_id if knowledge_structure.is_valid_category_id(category_id) else "UNCATEGORIZED/C00"

# --- TASK PRINCIPALE ---
@celery_app.task(
    name='archivista.process_document',
    bind=True,
    autoretry_for=(ConnectionError,),
    retry_kwargs={'max_retries': 3},
    default_retry_delay=30,
    soft_time_limit=300,
    time_limit=360
)
def process_document_task(self, file_path):
    file_name = os.path.basename(file_path)
    lock_file = file_path + ".lock"

    if os.path.exists(lock_file):
        lock_age = time.time() - os.path.getmtime(lock_file)
        if lock_age < 360:
            update_status(f"In attesa, file già in elaborazione", file_name)
            raise self.retry(countdown=60, max_retries=5)
        else:
            print(f"⚠️ Rimuovo lock obsoleto per {file_name}")
            os.remove(lock_file)

    try:
        with open(lock_file, "w") as f: f.write(str(os.getpid()))

        initialize_services()
        setup_database()
        
        if Settings.llm is None or Settings.embed_model is None:
            raise ConnectionError("Servizi AI non disponibili. Controlla la connessione e i modelli.")
            
        update_status("Avviato processamento", file_name)
        
        # 1. ESTRAZIONE TESTO
        update_status("Estrazione testo...", file_name)
        file_ext = os.path.splitext(file_name)[1].lower()
        extractor = get_text_extractor(file_ext)
        if not extractor: raise ValueError(f"Formato file non supportato: {file_ext}")
        full_text = extractor(file_path)
        if not full_text or not full_text.strip(): raise ValueError("Documento vuoto o illeggibile.")
        doc = Document(text=full_text)

        # 2. CLASSIFICAZIONE
        update_status("Classificazione AI...", file_name)
        category_id = classify_document(full_text)
        if category_id == "UNCATEGORIZED/C00":
            part_id, chapter_id = "UNCATEGORIZED", "C00"
            part_name, chapter_name = "Non Categorizzato", "Generale"
        else:
            part_id, chapter_id = category_id.split('/')
            part_name = knowledge_structure.KNOWLEDGE_BASE_STRUCTURE[part_id]['name']
            chapter_name = knowledge_structure.KNOWLEDGE_BASE_STRUCTURE[part_id]['chapters'][chapter_id]
        category_full_name = f"{part_name} -> {chapter_name}"

        # 3. ESTRAZIONE METADATI
        update_status("Estrazione metadati...", file_name)
        # MODIFICA: Usa il prompt manager
        metadata_prompt = PromptTemplate(prompt_manager.get_prompt("PYDANTIC_METADATA_PROMPT"))
        metadata_query = metadata_prompt.format(document_text=full_text[:4000], category_name=category_full_name)
        response = Settings.llm.complete(metadata_query)
        try:
            response_text = str(response).strip()
            # Try to extract JSON from the response if it contains extra text
            if '{' in response_text and '}' in response_text:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                json_str = response_text[start_idx:end_idx]
                metadata = PaperMetadata(**json.loads(json_str))
            else:
                # Fallback if no JSON found
                metadata = PaperMetadata(title=file_name, authors=[], publication_year=None)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            print(f"⚠️ Errore parsing metadati JSON: {e}. Response: {str(response)[:200]}...")
            metadata = PaperMetadata(title=file_name, authors=[], publication_year=None)

        # 4. INDICIZZAZIONE
        update_status("Indicizzazione...", file_name)
        doc.metadata.update({"file_name": file_name, "title": metadata.title, "authors": json.dumps(metadata.authors), "publication_year": metadata.publication_year, "category_id": category_id, "category_name": category_full_name})

        # Crea storage context senza cercare di caricare l'index esistente
        from llama_index.core.storage.docstore import SimpleDocumentStore
        from llama_index.core.storage.index_store import SimpleIndexStore
        from llama_index.core.vector_stores import SimpleVectorStore

        # Crea storage context vuoto per il primo avvio
        storage_context = StorageContext.from_defaults(
            docstore=SimpleDocumentStore(),
            vector_store=SimpleVectorStore(),
            index_store=SimpleIndexStore(),
            persist_dir=DB_STORAGE_DIR
        )

        try:
            # Verifica se esiste un index esistente
            index_exists = os.path.exists(os.path.join(DB_STORAGE_DIR, "docstore.json"))

            if index_exists:
                print(f"📚 Caricamento index esistente da {DB_STORAGE_DIR}")
                # Se esiste, carica l'index esistente e aggiungici il documento
                index = load_index_from_storage(storage_context)
                index.insert(doc)
                print("✅ Documento aggiunto all'index esistente")
            else:
                print(f"🆕 Creazione nuovo index in {DB_STORAGE_DIR}")
                # Se non esiste, crea un nuovo index
                index = VectorStoreIndex.from_documents([doc], storage_context=storage_context)
                print("✅ Nuovo index creato con successo")

            index.storage_context.persist(persist_dir=DB_STORAGE_DIR)
            print("💾 Index salvato su disco")

        except Exception as e:
            # Se c'è un errore, crea un nuovo index da zero
            print(f"⚠️ Errore con index esistente: {e}. Creo nuovo index da zero.")
            try:
                index = VectorStoreIndex.from_documents([doc], storage_context=storage_context)
                index.storage_context.persist(persist_dir=DB_STORAGE_DIR)
                print("✅ Nuovo index creato dopo errore")
            except Exception as e2:
                error_msg = f"Errore critico creazione index: {e2}"
                print(f"❌ {error_msg}")
                raise ValueError(error_msg)

        # 5. SALVATAGGIO SU DB E ARCHIVIAZIONE
        update_status("Salvataggio finale...", file_name)
        with db_connect() as conn:
            conn.cursor().execute("""
                INSERT INTO papers (file_name, title, authors, publication_year, category_id, category_name, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(file_name) DO UPDATE SET
                title=excluded.title, authors=excluded.authors, publication_year=excluded.publication_year,
                category_id=excluded.category_id, category_name=excluded.category_name;
            """, (file_name, metadata.title, json.dumps(metadata.authors), metadata.publication_year, category_id, category_full_name, datetime.now().isoformat()))
            conn.commit()

        destination_folder = os.path.join(CATEGORIZED_ARCHIVE_DIR, part_id, chapter_id)
        os.makedirs(destination_folder, exist_ok=True)
        shutil.move(file_path, os.path.join(destination_folder, file_name))
        
        update_status("Completato", file_name)
        return {'status': 'success', 'file_name': file_name, 'category': category_id}

    except Exception as e:
        error_msg = f"Errore: {str(e)}"
        print(f"❌ ERRORE nel processamento di {file_name}: {error_msg}")
        update_status(error_msg, file_name)

        # Non spostare in errore se è un problema di configurazione AI
        if "LLM non disponibile" in str(e) or "Servizi AI non disponibili" in str(e):
            print("⚠️ Errore di configurazione AI - non sposto il file in errore")
            raise

        # Sposta in errore solo per errori reali del documento
        error_folder = os.path.join(DOCS_TO_PROCESS_DIR, "_error")
        os.makedirs(error_folder, exist_ok=True)
        if os.path.exists(file_path):
            print(f"📁 Sposto {file_name} nella cartella errori")
            shutil.move(file_path, os.path.join(error_folder, file_name))
        raise
    finally:
        if os.path.exists(lock_file):
            os.remove(lock_file)
            print(f"🔓 Lock rilasciato per {file_name}")

@celery_app.task(name='archivista.cleanup_old_data')
def cleanup_old_data():
    """Task di pulizia: elimina i file falliti più vecchi di 7 giorni."""
    pass

@celery_app.task(name='archivista.scan_new_documents_periodic')
def scan_for_new_documents_periodic():
    """Task periodica: scansiona la cartella di input e avvia il processamento per i nuovi file."""
    pass
