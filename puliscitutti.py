import os
from pathlib import Path

# 1. Configurazione
nome_file_input = 'tuttifile.txt'
nome_file_output = 'elenco_snellito_finale.txt'

# Cartelle da escludere (Aggiunte in base alla tua richiesta)
PERCORSI_ESCLUSI = [
    # Cartelle di sistema/cache/ambiente
    '\\.git',         
    '\\.venv',        
    '\\__pycache__',  
    '\\node_modules', 
    '\\.idea',        
    '\\build',        
    '\\dist',
    
    # Cartelle contenenti dati, test, documentazione, ecc. (Aggiunte dalla tua lista)
    '\\logs',         
    '\\tests',        
    '\\data',         
    '\\notebooks',    
    '\\docs',         
    '\\media',        
    '\\static',       
    '\\db',           
]

# Estensioni da escludere (File derivati o temporanei)
ESTENSIONI_ESCLUSE = (
    '.pyc',   
    '.pyd',   
    '.exe',   
    '.dll',   
    '.pdb',   
    '.log',   
    '.sqlite',
    '.jpeg',  # Immagini (se non rilevanti per il codice)
    '.jpg',   # Immagini
    '.png',   # Immagini
    '.gif',   # Immagini
    '.mp4',   # Video
    '.avi',   # Video
)

# 2. Logica di Pulizia e Semplificazione

def pulisci_e_snellisci_elenco(input_path, output_path):
    
    # 2.1 Trova la radice del progetto per la semplificazione del percorso
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            first_line = ""
            # Cerca la prima linea che non sia un'intestazione di directory
            for line in f:
                if line.strip() and not line.startswith('--- Directory:'):
                    first_line = line.strip()
                    break
            
            if not first_line:
                print("Il file di input non contiene percorsi di file validi.")
                return

            # Esempio di percorso radice: E:\Etc\LLM\llava-llama3\assistente_ai
            # Ottenuta prendendo la directory madre del primo file.
            root_path = Path(first_line).parent
            root_path_str = str(root_path).replace('\\', '/')
            
    except Exception as e:
        print(f"Errore nella lettura del file di input o identificazione della radice: {e}")
        return

    conteggio_totale = 0
    conteggio_snellito = 0

    with open(input_path, 'r', encoding='utf-8') as file_input, \
         open(output_path, 'w', encoding='utf-8') as file_output:
        
        file_output.write(f"# Struttura della Repository (Snellita per Analisi AI)\n")
        file_output.write(f"# Radice del Progetto Assunta: {root_path_str}\n\n")
        
        for line in file_input:
            line = line.strip()
            
            if not line or line.startswith('--- Directory:'):
                continue
            
            conteggio_totale += 1
            
            # --- APPLICAZIONE DEI FILTRI ---
            
            # Sostituisci gli slash di Windows per un controllo path universale
            line_normalized = line.replace('\\', '/')
            
            # 1. Filtra per estensione
            if line.lower().endswith(ESTENSIONI_ESCLUSE):
                continue
            
            # 2. Filtra per percorso escluso (Verifica se la linea contiene una delle cartelle escluse)
            # Aggiunto il '/' prima del nome della cartella per evitare false esclusioni 
            # (es. una cartella chiamata 'test_core' non verrebbe esclusa da '\tests')
            if any('/' + path.strip('\\').lower() + '/' in line_normalized.lower() or 
                   '\\' + path.strip('\\').lower() + '\\' in line.lower()
                   for path in PERCORSI_ESCLUSI):
                continue
            
            # --- SEMPLIFICAZIONE DEL PERCORSO ---
            relative_path = line_normalized.replace(root_path_str, '').lstrip('/')
            
            if relative_path:
                file_output.write(f"{relative_path}\n")
                conteggio_snellito += 1
                
    print(f"\n--- Riepilogo della Pulizia ---")
    print(f"File totali rilevati in origine: {conteggio_totale}")
    print(f"File rilevanti inviati all'AI: {conteggio_snellito}")
    print(f"Risparmio in termini di file (e token): {conteggio_totale - conteggio_snellito}")
    print(f"Elenco snellito salvato in '{nome_file_output}'.")


# Esegui la funzione
pulisci_e_snellisci_elenco(nome_file_input, nome_file_output)