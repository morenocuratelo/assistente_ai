from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from duckduckgo_search import DDGS

def web_search(query: str) -> str:
    """
    Esegue una ricerca web usando DuckDuckGo per trovare informazioni recenti
    o non presenti nei documenti caricati.
    """
    print(f"--- Eseguo ricerca web per: '{query}' ---")
    try:
        with DDGS() as ddgs:
            # Limitiamo a 3 risultati per brevità
            results = list(ddgs.text(query, max_results=3))
            if not results:
                return "Nessun risultato trovato sul web per questa query."
            
            # Formattiamo i risultati in modo leggibile
            formatted_results = "\n\n".join([
                f"**Titolo:** {r.get('title', 'N/D')}\n"
                f"**Fonte:** {r.get('href', 'N/D')}\n"
                f"**Contenuto:** {r.get('body', 'Nessuna descrizione.')}"
                for r in results
            ])
            return f"Ho trovato i seguenti risultati sul web:\n{formatted_results}"
    except Exception as e:
        return f"Si è verificato un errore durante la ricerca web: {e}"

def summarize_document(file_name: str, index: VectorStoreIndex) -> str:
    """
    Genera un riassunto dettagliato di un documento specifico presente nell'indice.
    L'input deve essere il nome esatto del file (es. 'documento_x.pdf').
    """
    print(f"--- Avvio riassunto per il file: {file_name} ---")
    try:
        # Creiamo un retriever che filtra i nodi solo per il file specificato
        retriever = index.as_retriever(
            similarity_top_k=1000,  # Prendiamo un numero elevato di nodi
            filters=MetadataFilters(filters=[ExactMatchFilter(key="file_name", value=file_name)])
        )
        
        nodes = retriever.retrieve("contenuto completo del documento")
        
        if not nodes:
            return f"Non ho trovato il documento '{file_name}' nella base di conoscenza."
            
        full_text = "\n---\n".join([node.get_content() for node in nodes])
        
        summarization_prompt = f"Crea un riassunto dettagliato, completo e ben strutturato in italiano del seguente testo estratto dal documento '{file_name}':\n\n{full_text}"
        
        response = Settings.llm.complete(summarization_prompt)
        
        return response.text
    except Exception as e:
        return f"Si è verificato un errore durante la creazione del riassunto: {e}"
