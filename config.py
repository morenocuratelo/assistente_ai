import os
import sys
from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SemanticSplitterNodeParser
from dotenv import load_dotenv

def safe_print(msg: str):
    """Stampa un messaggio in modo sicuro senza causare errori di codifica."""
    try:
        print(msg)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or 'utf-8'
        sys.stdout.buffer.write(msg.encode(enc, errors='replace') + b"\n")

def initialize_services():
    """Inizializza i servizi AI condivisi (LLM, embeddings, parser)."""
    safe_print("Inizializzazione dei servizi AI condivisi...")

    # --- NUOVO: Caricamento robusto del file .env ---
    # Cerca il file .env in più posizioni
    project_root = os.path.abspath(os.path.dirname(__file__))
    possible_paths = [
        os.path.join(project_root, '.env'),
        os.path.join(os.getcwd(), '.env'),
        os.path.join(os.path.dirname(project_root), '.env')
    ]

    dotenv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            dotenv_path = path
            break

    if dotenv_path:
        load_dotenv(dotenv_path=dotenv_path)
        safe_print(f"✅ Variabili d'ambiente caricate da: {dotenv_path}")
    else:
        safe_print("⚠️ File .env non trovato in nessuna posizione. Le configurazioni potrebbero essere incomplete.")
        safe_print(f"Posizioni cercate: {', '.join(possible_paths)}")

    # --- Logica di selezione LLM migliorata ---
    # Priorità a Ollama se specificato, altrimenti prova OpenAI se la chiave è valida.
    ollama_base_url = os.getenv('OLLAMA_BASE_URL')
    openai_api_key = os.getenv('OPENAI_API_KEY')

    # Debug: Mostra lo stato delle chiavi (senza rivelare la chiave completa)
    safe_print(f"OLLAMA_BASE_URL: {'✅ impostato' if ollama_base_url else '❌ non impostato'}")
    safe_print(f"OPENAI_API_KEY: {'✅ impostato' if openai_api_key else '❌ non impostato'}")
    if openai_api_key:
        safe_print(f"OPENAI_API_KEY preview: {openai_api_key[:20]}...")

    llm_configured = False
    if ollama_base_url:
        safe_print(f"Trovato OLLAMA_BASE_URL. Provo a connettermi a Ollama: {ollama_base_url}")
        try:
            # Testa la connessione prima di impostare
            test_llm = Ollama(model="llama3", request_timeout=10.0, base_url=ollama_base_url)
            test_llm.complete("test") # Esegue una piccola chiamata per validare
            Settings.llm = Ollama(model="llama3", request_timeout=300.0, base_url=ollama_base_url)
            safe_print(f"✅ LLM (Ollama) configurato con successo: {Settings.llm.model}")
            llm_configured = True
        except Exception as e:
            safe_print(f"❌ Fallita connessione a Ollama: {e}. Verifico fallback a OpenAI.")
    
    if not llm_configured and openai_api_key and openai_api_key not in ['disabled', '']:
        safe_print("Provo a configurare OpenAI con la chiave API fornita...")
        try:
            # Validazione della chiave API
            if not openai_api_key.startswith('sk-'):
                safe_print("⚠️ La chiave OpenAI non sembra valida (non inizia con 'sk-')")
            else:
                from llama_index.llms.openai import OpenAI
                # Test della chiave con una chiamata semplice
                test_llm = OpenAI(model="gpt-3.5-turbo", api_key=openai_api_key, request_timeout=10.0)
                test_llm.complete("test")  # Test di connessione
                Settings.llm = test_llm
                safe_print("✅ LLM (OpenAI) configurato con successo.")
                llm_configured = True
        except Exception as e:
            safe_print(f"❌ Errore configurazione OpenAI: {e}")
            safe_print("💡 Suggerimenti: Verifica che la chiave API sia corretta e che tu abbia credito sufficiente.")

    if not llm_configured:
        safe_print("❌ NESSUN LLM CONFIGURATO. L'applicazione funzionerà in modalità limitata.")
        Settings.llm = None

    # Caricamento Embedding model (invariato)
    safe_print("Caricamento del modello di embedding...")
    try:
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            device="cpu",
            cache_folder="./model_cache"
        )
        safe_print("✅ Modello di embedding caricato.")
    except Exception as e:
        safe_print(f"❌ Errore caricamento embedding: {e}")
        Settings.embed_model = None

    # Configurazione Node parser (invariato)
    if Settings.embed_model:
        Settings.node_parser = SemanticSplitterNodeParser.from_defaults(embed_model=Settings.embed_model)
        safe_print("✅ Parser semantico configurato.")
    else:
        Settings.node_parser = None
        safe_print("⚠️ Parser semantico non configurato (embedding mancante).")
    
    safe_print("--- Inizializzazione servizi completata ---")

def get_chat_llm():
    """Restituisce un LLM per la chat basato su Ollama."""
    ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    try:
        # Usa un modello diverso/multimodale per la chat se necessario
        return Ollama(model="llava-llama3", request_timeout=300.0, base_url=ollama_base_url)
    except Exception:
        return None
