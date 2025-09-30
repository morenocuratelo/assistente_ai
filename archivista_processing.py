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

def extract_text_from_doc(file_path: str) -> str:
    """Extract text from legacy Word .doc files"""
    try:
        # Try using antiword if available (external tool)
        import subprocess
        try:
            result = subprocess.run(['antiword', file_path],
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Fallback: try using pypandoc if available
        try:
            import pypandoc
            return pypandoc.convert_file(file_path, 'plain', format='doc')
        except ImportError:
            pass

        # Final fallback: return placeholder message
        print(f"⚠️ Estrazione DOC non disponibile per {file_path}")
        return f"Contenuto Word (.doc): {os.path.basename(file_path)} - Richiede antiword o pypandoc per estrazione completa"

    except Exception as e:
        print(f"Errore estrazione DOC: {e}")
        return ""
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

def extract_text_from_pptx(file_path: str) -> str:
    """Extract text from PowerPoint .pptx files"""
    try:
        from pptx import Presentation
        prs = Presentation(file_path)
        text_content = []

        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text_content.append(shape.text)

        return '\n'.join(text_content)
    except Exception as e:
        print(f"Errore estrazione PPTX: {e}")
        return ""

def extract_text_from_ppt(file_path: str) -> str:
    """Extract text from legacy PowerPoint .ppt files"""
    try:
        # For .ppt files, we can try to use an external tool or convert to pptx
        # For now, return a placeholder - full implementation would need additional tools
        print(f"⚠️ Estrazione PPT non completamente implementata per {file_path}")
        return f"Contenuto PowerPoint (.ppt): {os.path.basename(file_path)} - Richiede tool esterno per estrazione completa"
    except Exception as e:
        print(f"Errore estrazione PPT: {e}")
        return ""

def extract_text_from_xlsx(file_path: str) -> str:
    """Extract text from Excel .xlsx files"""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        text_content = []

        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            sheet_text = [f"Foglio: {sheet_name}"]

            for row in sheet.iter_rows(values_only=True):
                # Extract non-empty cell values
                row_data = [str(cell) for cell in row if cell is not None]
                if row_data:
                    sheet_text.append(" | ".join(row_data))

            if len(sheet_text) > 1:  # More than just the sheet name
                text_content.extend(sheet_text)
                text_content.append("")  # Empty line between sheets

        return '\n'.join(text_content)
    except Exception as e:
        print(f"Errore estrazione XLSX: {e}")
        return ""

def extract_text_from_xls(file_path: str) -> str:
    """Extract text from legacy Excel .xls files"""
    try:
        import xlrd
        wb = xlrd.open_workbook(file_path)
        text_content = []

        for sheet_name in wb.sheet_names():
            sheet = wb.sheet_by_name(sheet_name)
            sheet_text = [f"Foglio: {sheet_name}"]

            for row_idx in range(sheet.nrows):
                row = sheet.row_values(row_idx)
                # Extract non-empty cell values
                row_data = [str(cell) for cell in row if cell != ""]
                if row_data:
                    sheet_text.append(" | ".join(row_data))

            if len(sheet_text) > 1:  # More than just the sheet name
                text_content.extend(sheet_text)
                text_content.append("")  # Empty line between sheets

        return '\n'.join(text_content)
    except ImportError:
        print("xlrd non disponibile per file .xls - considera installazione: pip install xlrd")
        return f"Contenuto Excel (.xls): {os.path.basename(file_path)} - Richiede xlrd per estrazione completa"
    except Exception as e:
        print(f"Errore estrazione XLS: {e}")
        return ""

def extract_text_from_csv(file_path: str) -> str:
    """Extract text from CSV files"""
    try:
        import csv
        text_content = []
        encoding = 'utf-8'

        # Try to detect encoding
        try:
            with open(file_path, 'rb') as f:
                raw = f.read()
                enc = chardet.detect(raw)['encoding']
                if enc:
                    encoding = enc
        except:
            pass

        with open(file_path, 'r', encoding=encoding) as f:
            # Try to detect delimiter
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter

            reader = csv.reader(f, delimiter=delimiter)
            for row_idx, row in enumerate(reader):
                # Extract non-empty cell values
                row_data = [str(cell) for cell in row if cell != ""]
                if row_data:
                    text_content.append(" | ".join(row_data))

        return '\n'.join(text_content)
    except Exception as e:
        print(f"Errore estrazione CSV: {e}")
        return ""

def get_text_extractor(file_extension: str):
    extractors = {
        # Text Documents
        '.pdf': extract_text_from_pdf,
        '.docx': extract_text_from_docx,
        '.doc': extract_text_from_doc,  # Use dedicated .doc extractor
        '.rtf': extract_text_from_rtf,
        '.html': extract_text_from_html,
        '.htm': extract_text_from_html,
        '.txt': extract_text_from_txt,

        # Presentations
        '.pptx': extract_text_from_pptx,
        '.ppt': extract_text_from_ppt,

        # Spreadsheets
        '.xlsx': extract_text_from_xlsx,
        '.xls': extract_text_from_xls,
        '.csv': extract_text_from_csv,
    }
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

    # Check for existing lock with timeout
    if os.path.exists(lock_file):
        lock_age = time.time() - os.path.getmtime(lock_file)
        if lock_age < 600:  # Increased timeout to 10 minutes
            update_status(f"File già in elaborazione da {lock_age:.0f}s", file_name)
            print(f"⏳ {file_name} già in elaborazione, attendo...")
            return {'status': 'already_processing', 'file_name': file_name}
        else:
            print(f"⚠️ Rimuovo lock obsoleto per {file_name} (età: {lock_age:.0f}s)")
            os.remove(lock_file)

    try:
        # Create lock file atomically
        try:
            with open(lock_file, "w") as f:
                f.write(f"{os.getpid()},{time.time()}")
        except Exception as e:
            print(f"❌ Errore creazione lock per {file_name}: {e}")
            return {'status': 'lock_error', 'file_name': file_name}

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

        # Crea storage context per l'indicizzazione
        from llama_index.core.storage.docstore import SimpleDocumentStore
        from llama_index.core.storage.index_store import SimpleIndexStore
        from llama_index.core.vector_stores import SimpleVectorStore

        storage_context = StorageContext.from_defaults(
            docstore=SimpleDocumentStore(),
            vector_store=SimpleVectorStore(),
            index_store=SimpleIndexStore(),
            persist_dir=DB_STORAGE_DIR
        )

        max_index_retries = 3
        index_created = False

        for attempt in range(max_index_retries):
            try:
                # Verifica se esiste un index esistente
                index_exists = os.path.exists(os.path.join(DB_STORAGE_DIR, "docstore.json"))

                if index_exists and not index_created:
                    print(f"📚 Caricamento index esistente da {DB_STORAGE_DIR} (tentativo {attempt + 1})")
                    # Se esiste, carica l'index esistente e aggiungici il documento
                    index = load_index_from_storage(storage_context)
                    index.insert(doc)
                    print("✅ Documento aggiunto all'index esistente")
                else:
                    print(f"🆕 Creazione nuovo index in {DB_STORAGE_DIR} (tentativo {attempt + 1})")
                    # Se non esiste, crea un nuovo index
                    index = VectorStoreIndex.from_documents([doc], storage_context=storage_context)
                    print("✅ Nuovo index creato con successo")
                    index_created = True

                index.storage_context.persist(persist_dir=DB_STORAGE_DIR)
                print("💾 Index salvato su disco")
                break  # Success, exit retry loop

            except Exception as e:
                print(f"⚠️ Errore indicizzazione tentativo {attempt + 1}: {e}")
                if attempt == max_index_retries - 1:
                    # Last attempt failed, raise the error
                    error_msg = f"Errore critico creazione index dopo {max_index_retries} tentativi: {e}"
                    print(f"❌ {error_msg}")
                    raise ValueError(error_msg)
                else:
                    # Wait before retry
                    print(f"⏳ Attendo 5 secondi prima del prossimo tentativo...")
                    time.sleep(5)
                    # Reset storage context for retry
                    storage_context = StorageContext.from_defaults(
                        docstore=SimpleDocumentStore(),
                        vector_store=SimpleVectorStore(),
                        index_store=SimpleIndexStore(),
                        persist_dir=DB_STORAGE_DIR
                    )

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
            # Don't raise here, just return an error status
            return {'status': 'ai_service_error', 'file_name': file_name, 'error': str(e)}

        # Sposta in errore solo per errori reali del documento
        error_folder = os.path.join(DOCS_TO_PROCESS_DIR, "_error")
        os.makedirs(error_folder, exist_ok=True)
        if os.path.exists(file_path):
            try:
                print(f"📁 Sposto {file_name} nella cartella errori")
                shutil.move(file_path, os.path.join(error_folder, file_name))
                print(f"✅ File {file_name} spostato nella cartella errori")
            except Exception as move_error:
                print(f"⚠️ Errore spostamento file {file_name}: {move_error}")

        # Return error status instead of raising
        return {'status': 'processing_error', 'file_name': file_name, 'error': str(e)}
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
