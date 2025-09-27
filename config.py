import os
import sys
from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SemanticSplitterNodeParser


def safe_print(msg: str):
    """Print without raising UnicodeEncodeError on consoles with limited encoding.
    Falls back to writing bytes with replacement for unsupported characters.
    """
    try:
        print(msg)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or 'utf-8'
        try:
            # Write bytes directly to avoid encoding errors
            sys.stdout.buffer.write(msg.encode(enc, errors='replace'))
            sys.stdout.buffer.write(b"\n")
        except Exception:
            # Last-resort fallback
            print(msg.encode('utf-8', errors='replace').decode('ascii', errors='replace'))


def initialize_services():
    """Initialize shared AI services (LLM, embeddings, parser).

    This function centralizes LLM and embedding configuration and handles
    graceful fallback when Ollama or models are not available.
    """
    safe_print("Inizializzazione dei servizi AI condivisi...")

    # Configurazione Ollama con supporto per ambiente Docker
    ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

    # Proviamo a connetterci a Ollama e configurare il LLM principale
    try:
        test_llm = Ollama(model="llama3", request_timeout=10.0, base_url=ollama_base_url)
        _ = test_llm.metadata  # trigger metadata fetch to validate connection
        safe_print(f"Connessione a Ollama verificata (URL: {ollama_base_url})")
        Settings.llm = Ollama(model="llama3", request_timeout=300.0, base_url=ollama_base_url)
        safe_print(f"LLM per indicizzazione configurato: {getattr(Settings.llm, 'model', 'unknown')}")
    except Exception as e:
        safe_print(f"Impossibile connettersi a Ollama: {e}")
        safe_print("Configurazione fallback: sistema funzionerà in modalità limitata")
        safe_print("Avvia Ollama con: ollama serve")
        Settings.llm = None

    # Embedding model
    safe_print("Caricamento del modello di embedding multilingue...")
    try:
        embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            device="cpu",
            cache_folder="./model_cache"
        )
        Settings.embed_model = embed_model
        safe_print("Modello di embedding caricato con successo")
    except Exception as e:
        safe_print(f"Errore nel caricamento del modello di embedding: {e}")
        safe_print("Tentativo con un modello di embedding più semplice...")
        try:
            embed_model = HuggingFaceEmbedding(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",
                cache_folder="./model_cache"
            )
            Settings.embed_model = embed_model
            safe_print("Modello di embedding fallback caricato con successo")
        except Exception as e2:
            safe_print(f"Errore anche con il modello fallback: {e2}")
            safe_print("Procedendo senza embedding model")
            Settings.embed_model = None

    # Node parser
    safe_print("Configurazione del parser semantico per un'indicizzazione più efficace...")
    try:
        if Settings.embed_model is not None:
            Settings.node_parser = SemanticSplitterNodeParser.from_defaults(embed_model=Settings.embed_model)
            safe_print("Parser semantico configurato con successo")
        else:
            safe_print("Parser semantico non configurato (embedding non disponibile)")
            Settings.node_parser = None
    except Exception as e:
        safe_print(f"Errore nella configurazione del parser: {e}")
        Settings.node_parser = None

    safe_print("Servizi AI condivisi inizializzati (con eventuali limitazioni).")


def get_chat_llm():
    """Return an Ollama-based LLM configured for chat.

    Falls back to None if Ollama isn't available.
    """
    ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    try:
        return Ollama(model="llava-llama3", request_timeout=300.0, base_url=ollama_base_url)
    except Exception as e:
        safe_print(f"Impossibile creare LLM per chat: {e}")
        return None
