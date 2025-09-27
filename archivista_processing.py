"""
Questo file contiene la logica di business principale per il processamento
dei documenti. La funzione qui definita viene registrata come task Celery.
"""
import os
import shutil
import sqlite3
import json
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from typing import List, Optional

# Import per l'estrazione granulare del testo
import fitz  # PyMuPDF
from docx import Document as DocxDocument

from llama_index.core import Document, Settings, VectorStoreIndex, StorageContext, PromptTemplate, load_index_from_storage

from celery_app import celery_app
from config import initialize_services
import prompt_manager
import knowledge_structure

# --- CONFIGURAZIONE (sposteremo in config.py nel prossimo step) ---
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
        with open(ARCHIVISTA_STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump({"status": status, "file": current_file, "timestamp": datetime.now().isoformat()}, f)
    except Exception as e:
        print(f"--> ERRORE aggiornamento stato: {e}")

def db_connect():
    conn = sqlite3.connect(METADATA_DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# --- NUOVE FUNZIONI PER L'ESTRAZIONE DEL TESTO ---

def extract_text_from_pdf(file_path: str) -> str:
    """Estrae il testo completo da un file PDF."""
    try:
        with fitz.open(file_path) as doc:
            text = "".join(page.get_text() for page in doc)
        return text
    except Exception as e:
        print(f"Errore estrazione testo da PDF {file_path}: {e}")
        raise

def extract_text_from_docx(file_path: str) -> str:
    """Estrae il testo completo da un file DOCX."""
    try:
        doc = DocxDocument(file_path)
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        return text
    except Exception as e:
        print(f"Errore estrazione testo da DOCX {file_path}: {e}")
        raise

def classify_document(text_content):
    if not Settings.llm:
        raise ConnectionError("LLM non disponibile per la classificazione.")
    classification_structure = knowledge_structure.get_structure_for_prompt()
    prompt = PromptTemplate(prompt_manager.get_prompt("DOCUMENT_CLASSIFICATION_PROMPT"))
    formatted_prompt = prompt.format(
        classification_structure=classification_structure,
        document_text=text_content[:8000]
    )
    response = Settings.llm.complete(formatted_prompt)
    category_id = str(response).strip()
    if knowledge_structure.is_valid_category_id(category_id):
        return category_id
    else:
        return "UNCATEGORIZED/C00"


# --- TASK PRINCIPALE (MODIFICATA) ---
@celery_app.task(name='archivista.process_document')
def process_document_task(file_path):
    initialize_services()
    file_name = os.path.basename(file_path)
    update_status("Avviato processamento", file_name)

    try:
        # 1. ESTRAZIONE TESTO (Logica Unificata)
        update_status("Estrazione testo...", file_name)
        file_ext = os.path.splitext(file_name)[1].lower()
        if file_ext == '.pdf':
            full_text = extract_text_from_pdf(file_path)
        elif file_ext == '.docx':
            full_text = extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Formato file non supportato: {file_ext}")

        if not full_text:
            raise ValueError("Documento vuoto o illeggibile.")
        
        # Crea un singolo oggetto Document per LlamaIndex
        doc = Document(text=full_text)

        # 2. CLASSIFICAZIONE
        update_status("Classificazione AI...", file_name)
        category_id = classify_document(full_text)
        category_full_name = "Non Categorizzato -> Generale"
        if category_id != "UNCATEGORIZED/C00":
            part_id, chapter_id = category_id.split('/')
            part_name = knowledge_structure.KNOWLEDGE_BASE_STRUCTURE[part_id]['name']
            chapter_name = knowledge_structure.KNOWLEDGE_BASE_STRUCTURE[part_id]['chapters'][chapter_id]
            category_full_name = f"{part_name} -> {chapter_name}"

        # 3. ESTRAZIONE METADATI
        update_status("Estrazione metadati...", file_name)
        metadata_prompt = PromptTemplate(prompt_manager.get_prompt("PYDANTIC_METADATA_PROMPT"))
        metadata_query = metadata_prompt.format(document_text=full_text[:4000], category_name=category_full_name)
        response = Settings.llm.complete(metadata_query)
        try:
            metadata = PaperMetadata(**json.loads(str(response)))
        except (json.JSONDecodeError, TypeError):
            metadata = PaperMetadata(title=file_name, authors=[], publication_year=datetime.now().year)

        # 4. INDICIZZAZIONE (Logica ottimizzata nel prossimo step)
        update_status("Indicizzazione...", file_name)
        # Aggiunge i metadati estratti al documento
        doc.metadata.update({
            "file_name": file_name,
            "title": metadata.title,
            "authors": json.dumps(metadata.authors),
            "publication_year": metadata.publication_year,
            "category_id": category_id,
            "category_name": category_full_name
        })
        
        storage_context = StorageContext.from_defaults(persist_dir=DB_STORAGE_DIR)
        index = VectorStoreIndex.from_documents([doc], storage_context=storage_context) # Temporaneo, da ottimizzare
        index.storage_context.persist(persist_dir=DB_STORAGE_DIR)

        # 5. SALVATAGGIO SU DB
        update_status("Salvataggio database...", file_name)
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO papers (file_name, title, authors, publication_year, category_id, category_name, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_name) DO UPDATE SET
                title=excluded.title, authors=excluded.authors, publication_year=excluded.publication_year,
                category_id=excluded.category_id, category_name=excluded.category_name;
            """, (file_name, metadata.title, json.dumps(metadata.authors), metadata.publication_year, category_id, category_full_name, datetime.now().isoformat()))
            conn.commit()

        # 6. ARCHIVIAZIONE FILE FISICO
        update_status("Archiviazione file...", file_name)
        if category_id != "UNCATEGORIZED/C00":
            part_id, chapter_id = category_id.split('/')
            destination_folder = os.path.join(CATEGORIZED_ARCHIVE_DIR, part_id, chapter_id)
        else:
            destination_folder = os.path.join(CATEGORIZED_ARCHIVE_DIR, "UNCATEGORIZED", "C00")
        os.makedirs(destination_folder, exist_ok=True)
        shutil.move(file_path, os.path.join(destination_folder, file_name))

        update_status("Completato", file_name)
        return {'status': 'success', 'file_name': file_name, 'category': category_id}

    except Exception as e:
        update_status(f"Errore: {str(e)}", file_name)
        error_folder = os.path.join(DOCS_TO_PROCESS_DIR, "_error")
        os.makedirs(error_folder, exist_ok=True)
        if os.path.exists(file_path):
            shutil.move(file_path, os.path.join(error_folder, file_name))
        raise

# --- TASK PIANIFICATE (invariate) ---

@celery_app.task(name='archivista.cleanup_old_data')
def cleanup_old_data():
    """Task di pulizia: elimina i file falliti più vecchi di 7 giorni."""
    print("🧹 Esecuzione task di pulizia giornaliera...")
    error_folder = os.path.join(DOCS_TO_PROCESS_DIR, "_error")
    if not os.path.exists(error_folder):
        return "Nessuna cartella _error, pulizia non necessaria."

    cutoff = datetime.now() - timedelta(days=7)
    files_removed = 0
    for filename in os.listdir(error_folder):
        file_path = os.path.join(error_folder, filename)
        try:
            modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if modified_time < cutoff:
                os.remove(file_path)
                files_removed += 1
                print(f"  -> Rimosso file obsoleto: {filename}")
        except Exception as e:
            print(f"  -> Errore durante la rimozione di {filename}: {e}")
    
    print(f"✅ Pulizia completata. File rimossi: {files_removed}.")
    return f"Pulizia completata. File rimossi: {files_removed}."


@celery_app.task(name='archivista.scan_new_documents_periodic')
def scan_for_new_documents_periodic():
    """Task periodica: scansiona la cartella di input e avvia il processamento per i nuovi file."""
    print("🤖 Esecuzione scansione periodica per nuovi documenti...")
    try:
        new_files = [f for f in os.listdir(DOCS_TO_PROCESS_DIR) if f.lower().endswith(('.pdf', '.docx'))]
        if not new_files:
            print("  -> Nessun nuovo documento trovato.")
            return "Nessun nuovo documento."

        processed_count = 0
        for file_name in new_files:
            file_path = os.path.join(DOCS_TO_PROCESS_DIR, file_name)
            process_document_task.delay(file_path)
            processed_count += 1
            print(f"  -> Inviata task per: {file_name}")
        
        print(f"✅ Scansione completata. {processed_count} task inviate.")
        return f"Scansione completata. {processed_count} task inviate."
    except Exception as e:
        print(f"❌ Errore durante la scansione periodica: {e}")
        return f"Errore: {e}"

