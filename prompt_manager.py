import json

def load_prompts(filepath="prompts.json"):
    """
    Carica i prompt da un file JSON.

    Il file deve essere un dizionario con i nomi dei prompt come chiavi 
    e il testo del prompt come valori.

    Args:
        filepath (str): Il percorso del file JSON dei prompt.

    Returns:
        dict: Un dizionario con i prompt caricati.
    """
    prompts = {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            prompts = json.load(f)
            
    except FileNotFoundError:
        print(f"ATTENZIONE: File dei prompt '{filepath}' non trovato. Verranno usati i prompt di default.")
    except json.JSONDecodeError:
        print(f"ERRORE: Il file '{filepath}' non è un JSON valido.")
    except Exception as e:
        print(f"Errore durante il caricamento dei prompt: {e}")
        
    return prompts

# Carica i prompt una sola volta all'avvio del modulo
_prompts = load_prompts()

def get_prompt(prompt_name, default_text=""):
    """
    Recupera un prompt specifico dal dizionario caricato.

    Args:
        prompt_name (str): Il nome del prompt da recuperare (es. "CHAT_ASSISTANT_PROMPT").
        default_text (str): Un testo di default da restituire se il prompt non viene trovato.

    Returns:
        str: Il testo del prompt o il testo di default.
    """
    return _prompts.get(prompt_name, default_text)

# Esempio di utilizzo (se si esegue questo file direttamente)
if __name__ == "__main__":
    chat_prompt = get_prompt("CHAT_ASSISTANT_PROMPT")
    if chat_prompt:
        print("--- PROMPT PER LA CHAT CARICATO ---")
        print(chat_prompt)
    else:
        print("Prompt per la chat non trovato!")

    meta_prompt = get_prompt("METADATA_EXTRACTION_PROMPT")
    if meta_prompt:
        print("\n--- PROMPT PER ESTRAZIONE METADATI CARICATO ---")
        print(meta_prompt)
    else:
        print("Prompt per estrazione metadati non trovato!")
        
    router_prompt = get_prompt("ROUTER_PROMPT")
    if router_prompt:
        print("\n--- PROMPT PER IL ROUTER CARICATO ---")
        print(router_prompt)
    else:
        print("Prompt per il router non trovato!")
