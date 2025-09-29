"""
Modulo per la gestione e il caricamento dei prompt da un file JSON.
Questo centralizza la logica di accesso ai prompt, rendendo il codice
principale più pulito e facile da manutenere.
"""
import json
import os

# Percorso del file JSON che contiene tutti i prompt.
PROMPTS_FILE = "prompts.json"

# Variabile globale per memorizzare i prompt una volta caricati (caching).
_prompts = None

def _load_prompts():
    """
    Carica i prompt dal file JSON.
    Questa funzione viene eseguita solo una volta per efficienza.
    Lancia eccezioni specifiche se il file è mancante o corrotto.
    """
    global _prompts
    # Esegui il caricamento solo se non è già stato fatto.
    if _prompts is None:
        if not os.path.exists(PROMPTS_FILE):
            # Errore fatale se il file di configurazione essenziale non esiste.
            raise FileNotFoundError(f"File dei prompt non trovato: '{PROMPTS_FILE}'. Assicurati che esista.")
        try:
            with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
                _prompts = json.load(f)
        except json.JSONDecodeError as e:
            # Errore fatale se il JSON è malformato.
            raise ValueError(f"Errore nel parsing del file JSON dei prompt: {e}")
        except Exception as e:
            # Altri errori di lettura del file.
            raise IOError(f"Impossibile leggere il file dei prompt: {e}")

def get_prompt(prompt_name: str) -> str:
    """
    Restituisce il testo di un prompt specifico dato il suo nome (chiave).

    Args:
        prompt_name (str): La chiave del prompt da recuperare (es. "CHAT_ASSISTANT_PROMPT").

    Returns:
        str: Il testo del prompt.

    Raises:
        KeyError: Se il nome del prompt non viene trovato nel file.
    """
    _load_prompts()  # Assicura che i prompt siano stati caricati.
    
    # Se la chiave richiesta non è presente nel dizionario, lancia un errore chiaro.
    # Questo è più sicuro che restituire un valore di default (es. stringa vuota),
    # che potrebbe causare errori inaspettati in altre parti del codice.
    if prompt_name not in _prompts:
        raise KeyError(f"Prompt '{prompt_name}' non trovato nel file '{PROMPTS_FILE}'.")
        
    return _prompts[prompt_name]

# Esempio di utilizzo per testare il modulo direttamente.
if __name__ == "__main__":
    try:
        print("--- TEST DEL PROMPT MANAGER ---")
        chat_prompt = get_prompt("CHAT_ASSISTANT_PROMPT")
        print("✅ Prompt per la chat caricato con successo.")
        
        # Test di un prompt che potrebbe non esistere
        non_existent_prompt = get_prompt("NON_EXISTENT_PROMPT")
    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"\n❌ Test fallito come previsto: {e}")

