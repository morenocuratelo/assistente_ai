import os
from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SemanticSplitterNodeParser

def initialize_services():
    """
    Inizializza e configura i servizi AI (LLM, embedding, parser)
    in un unico posto per garantire coerenza in tutto il progetto.
    Gestisce gracefully la mancanza di connessione a Ollama.
    """
    print("Inizializzazione dei servizi AI condivisi...")

    # Configurazione Ollama con supporto per ambiente Docker
    ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

    try:
        # Test connessione a Ollama
        test_llm = Ollama(model="llama3", request_timeout=10.0, base_url=ollama_base_url)
        # Prova a ottenere i metadati per verificare la connessione
        _ = test_llm.metadata
        print(f"✅ Connessione a Ollama verificata (URL: {ollama_base_url})")

        # LLM per l'indicizzazione (llama3 - più veloce e stabile)
        Settings.llm = Ollama(
            model="llama3",
            request_timeout=300.0,
            base_url=ollama_base_url
        )
        print(f"✅ LLM per indicizzazione configurato: {Settings.llm.model}")

    except Exception as e:
        print(f"⚠️  Impossibile connettersi a Ollama: {e}")
        print("🔄 Configurazione fallback: sistema funzionerà in modalità limitata")
        print("💡 Avvia Ollama con: ollama serve")
        Settings.llm = None

    print("Caricamento del modello di embedding multilingue...")
    try:
        embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            device="cpu",
            cache_folder="./model_cache"  # Add cache folder to avoid issues
        )
        Settings.embed_model = embed_model
        print("✅ Modello di embedding caricato con successo")
    except Exception as e:
        print(f"❌ Errore nel caricamento del modello di embedding: {e}")
        print("🔄 Tentativo con un modello di embedding più semplice...")
        try:
            # Fallback to a simpler embedding model
            embed_model = HuggingFaceEmbedding(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",
                cache_folder="./model_cache"
            )
            Settings.embed_model = embed_model
            print("✅ Modello di embedding fallback caricato con successo")
        except Exception as e2:
            print(f"❌ Errore anche con il modello fallback: {e2}")
            print("⚠️  Procedendo senza embedding model")
            Settings.embed_model = None

    print("Configurazione del parser semantico per un'indicizzazione più efficace...")
    try:
        if Settings.embed_model:
            # Usiamo il parser semantico che migliora la coerenza dei chunk di testo.
            Settings.node_parser = SemanticSplitterNodeParser.from_defaults(
                embed_model=Settings.embed_model
            )
            print("✅ Parser semantico configurato con successo")
        else:
            print("⚠️  Parser semantico non configurato (embedding non disponibile)")
            Settings.node_parser = None
    except Exception as e:
        print(f"❌ Errore nella configurazione del parser: {e}")
        Settings.node_parser = None

    print("Servizi AI condivisi inizializzati (con eventuali limitazioni).")

def get_chat_llm():
    """
    Restituisce un LLM configurato per la chat con supporto multimodale.
    Utilizza llava-llama3 per supportare testo e immagini.
    """
    ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

    try:
        return Ollama(
            model="llava-llama3",
            request_timeout=300.0,
            base_url=ollama_base_url
        )
    except Exception as e:
        print(f"❌ Impossibile creare LLM per chat: {e}")
        return None
