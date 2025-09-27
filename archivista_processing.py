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
import pdfplumber
from pypdf import PdfReader
from pdfminer.high_level import extract_text as pdfminer_extract

from bs4 import BeautifulSoup
import chardet

from llama_index.core import Document, Settings, VectorStoreIndex, StorageContext, PromptTemplate, load_index_from_storage

from celery_app import celery_app
from config import initialize_services
import prompt_manager
import knowledge_structure
from file_utils import setup_database

# --- CONFIGURAZIONE (sposteremo in config.py nel prossimo step) ---
DOCS_TO_PROCESS_DIR = "documenti_da_processare"
CATEGORIZED_ARCHIVE_DIR = "Dall_Origine_alla_Complessita"
DB_STORAGE_DIR = "db_memoria"
METADATA_DB_FILE = os.path.join(DB_STORAGE_DIR, "metadata.sqlite")
ARCHIVISTA_STATUS_FILE = os.path.join(DB_STORAGE_DIR, "archivista_status.json")


def ensure_storage_files_exist():
    """Ensure the storage directory and minimal storage json files exist.
    This prevents FileNotFoundError when llama_index.StorageContext.from_defaults
    attempts to open persistent kvstore files.
    """
    try:
        os.makedirs(DB_STORAGE_DIR, exist_ok=True)
        # Create a few minimal JSON files expected by llama_index simple_kvstore
        for fname in [
            "docstore.json",
            "index_store.json",
            "default__vector_store.json",
            "graph_store.json",
            "image__vector_store.json",
        ]:
            path = os.path.join(DB_STORAGE_DIR, fname)
            if not os.path.exists(path):
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write("{}")
                except Exception as e:
                    print(f"--> Errore creando file di storage '{path}': {e}")
    except Exception as e:
        print(f"--> Errore assicurando la cartella di storage: {e}")

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

# --- FUNZIONI PER L'ESTRAZIONE DEL TESTO ---

def extract_text_from_pdf(file_path: str) -> str:
    """Estrae il testo completo da un file PDF con metodi fallback."""
    text_extractors = [
        ("PyMuPDF", extract_text_pymupdf),
        ("PyPDF2", extract_text_pypdf2),
        ("pdfplumber", extract_text_pdfplumber),
        ("pdfminer", extract_text_pdfminer)
    ]

    for extractor_name, extractor_func in text_extractors:
        try:
            text = extractor_func(file_path)
            if text and text.strip():
                print(f"✓ Testo estratto con successo usando {extractor_name}")
                return text
        except Exception as e:
            print(f"✗ Errore con {extractor_name}: {e}")
            continue

    raise ValueError(f"Impossibile estrarre testo dal PDF {file_path} con alcun metodo")

def extract_text_pymupdf(file_path: str) -> str:
    """Estrae testo usando PyMuPDF."""
    with fitz.open(file_path) as doc:
        return "".join(page.get_text() for page in doc)

def extract_text_pypdf2(file_path: str) -> str:
    """Estrae testo usando PyPDF2."""
    with open(file_path, 'rb') as file:
        pdf_reader = PdfReader(file)
        return "".join(page.extract_text() for page in pdf_reader.pages)

def extract_text_pdfplumber(file_path: str) -> str:
    """Estrae testo usando pdfplumber."""
    with pdfplumber.open(file_path) as pdf:
        return "".join(page.extract_text() or "" for page in pdf.pages)

def extract_text_pdfminer(file_path: str) -> str:
    """Estrae testo usando pdfminer."""
    return pdfminer_extract(file_path)

def extract_text_from_docx(file_path: str) -> str:
    """Estrae il testo completo da un file DOCX."""
    try:
        doc = DocxDocument(file_path)
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        return text
    except Exception as e:
        print(f"Errore estrazione testo da DOCX {file_path}: {e}")
        raise

def extract_text_from_rtf(file_path: str) -> str:
    """Estrae il testo da un file RTF (semplificato)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            rtf_content = file.read()
        # Semplice rimozione dei comandi RTF più comuni
        import re
        # Rimuovi i comandi RTF di base
        text = re.sub(r'\\[a-z]+\d*\s?', '', rtf_content)  # Rimuovi comandi come \b0, \i0, etc.
        text = re.sub(r'\\[a-z]+', '', text)  # Rimuovi altri comandi RTF
        text = re.sub(r'[{}]', '', text)  # Rimuovi parentesi graffe
        return text.strip()
    except Exception as e:
        print(f"Errore estrazione testo da RTF {file_path}: {e}")
        raise

def extract_text_from_html(file_path: str) -> str:
    """Estrae il testo da un file HTML."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text()
    except Exception as e:
        print(f"Errore estrazione testo da HTML {file_path}: {e}")
        raise

def extract_text_from_txt(file_path: str) -> str:
    """Estrae il testo da un file di testo."""
    try:
        # Prima prova con UTF-8
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Se UTF-8 fallisce, prova a rilevare l'encoding
            with open(file_path, 'rb') as file:
                raw_data = file.read()
            detected_encoding = chardet.detect(raw_data)['encoding']
            if detected_encoding:
                with open(file_path, 'r', encoding=detected_encoding) as file:
                    return file.read()
            else:
                raise ValueError("Impossibile rilevare l'encoding del file")
    except Exception as e:
        print(f"Errore estrazione testo da TXT {file_path}: {e}")
        raise

def get_text_extractor(file_extension: str):
    """Restituisce la funzione di estrazione appropriata per l'estensione del file."""
    extractors = {
        '.pdf': extract_text_from_pdf,
        '.docx': extract_text_from_docx,
        '.rtf': extract_text_from_rtf,
        '.html': extract_text_from_html,
        '.htm': extract_text_from_html,
        '.txt': extract_text_from_txt,
    }
    return extractors.get(file_extension.lower())

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


# --- TASK PRINCIPALE (CON INDICIZZAZIONE OTTIMIZZATA) ---
@celery_app.task(name='archivista.process_document')
def process_document_task(file_path):
    initialize_services()
    file_name = os.path.basename(file_path)

    # Ensure storage folder and minimal persistent files exist before llama_index loads them
    ensure_storage_files_exist()

    # Setup database table
    setup_database()

    update_status("Avviato processamento", file_name)

    try:
        # 1. ESTRAZIONE TESTO
        update_status("Estrazione testo...", file_name)
        file_ext = os.path.splitext(file_name)[1].lower()

        # Ottieni la funzione di estrazione appropriata
        extractor = get_text_extractor(file_ext)
        if not extractor:
            raise ValueError(f"Formato file non supportato: {file_ext}")

        # Estrai il testo usando la funzione appropriata
        full_text = extractor(file_path)

        if not full_text or not full_text.strip():
            raise ValueError("Documento vuoto o illeggibile.")
        
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

        # 4. INDICIZZAZIONE OTTIMIZZATA
        update_status("Indicizzazione...", file_name)
        doc.metadata.update({
            "file_name": file_name,
            "title": metadata.title,
            "authors": json.dumps(metadata.authors),
            "publication_year": metadata.publication_year,
            "category_id": category_id,
            "category_name": category_full_name
        })

        # Verifica se l'indice esiste già
        index_exists = os.path.exists(os.path.join(DB_STORAGE_DIR, "docstore.json"))

        if index_exists:
            try:
                # Prova a caricare un indice esistente
                storage_context = StorageContext.from_defaults(persist_dir=DB_STORAGE_DIR)
                # Ensure embed_model is set before loading index
                if Settings.embed_model is None:
                    print("Embedding model not set, reinitializing services...")
                    initialize_services()
                index = load_index_from_storage(storage_context)
                # Inserisci il nuovo documento nell'indice esistente
                index.insert(doc)
                print(f"--> Documento '{file_name}' inserito nell'indice esistente.")
            except Exception as e:
                print(f"--> Errore nel caricamento dell'indice esistente: {e}. Creazione nuovo indice.")
                storage_context = StorageContext.from_defaults(persist_dir=DB_STORAGE_DIR)
                index = VectorStoreIndex.from_documents([doc], storage_context=storage_context)
                print(f"--> Creato nuovo indice con il documento: '{file_name}'.")
        else:
            # Se l'indice non esiste, creane uno nuovo con il documento corrente
            storage_context = StorageContext.from_defaults(persist_dir=DB_STORAGE_DIR)
            index = VectorStoreIndex.from_documents([doc], storage_context=storage_context)
            print(f"--> Creato nuovo indice con il primo documento: '{file_name}'.")

        # Persisti le modifiche (sia per l'inserimento che per la creazione)
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
        supported_extensions = ['.pdf', '.docx', '.rtf', '.html', '.htm', '.txt']
        new_files = [f for f in os.listdir(DOCS_TO_PROCESS_DIR) if any(f.lower().endswith(ext) for ext in supported_extensions)]
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
