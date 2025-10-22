import os
from pathlib import Path

# 1. Determina il percorso della directory in cui si trova questo script.
# __file__ è una variabile speciale che contiene il percorso del file Python corrente.
# .resolve().parent prende il percorso assoluto della directory padre (la cartella).
directory_radice = Path(__file__).resolve().parent

nome_file_output = 'tuttifile.txt'

# 2. Il file di output verrà creato nella stessa directory dello script.
percorso_output = directory_radice / nome_file_output 

print(f"Directory di scansione: {directory_radice}")
print(f"File di output: {percorso_output}")


# 3. Apri il file in modalità scrittura ('w')
with open(percorso_output, 'w', encoding='utf-8') as file_output:
    
    conteggio_file = 0
    
    # 4. Attraversa ricorsivamente la directory
    # La conversione a str è necessaria perché os.walk vuole una stringa, 
    # sebbene molti altri metodi Path supportino l'oggetto Path direttamente.
    for root, dirs, files in os.walk(str(directory_radice)):
        
        # Scrivi il percorso della directory corrente
        file_output.write(f"--- Directory: {root} ---\n")
        
        # 5. Scrivi i percorsi completi di tutti i file
        for nome_file in files:
            # Crea il percorso completo
            percorso_completo = os.path.join(root, nome_file)
            
            # Scrivi il percorso nel file
            file_output.write(f"{percorso_completo}\n")
            conteggio_file += 1

    # 6. Scrivi un riepilogo
    file_output.write(f"\n=========================================\n")
    file_output.write(f"Scansione completata. Trovati {conteggio_file} file totali.\n")

print(f"Elenco salvato con successo in '{nome_file_output}'.")