"""
Modulo per operazioni batch sui metadati dei documenti.
Permette modifiche massive sicure e validate.
"""
import pandas as pd
import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple
from file_utils import db_connect, get_papers_dataframe, update_paper_metadata

# --- CONFIGURAZIONE ---
DB_STORAGE_DIR = "db_memoria"
METADATA_DB_FILE = os.path.join(DB_STORAGE_DIR, "metadata.sqlite")

class BatchOperation:
    """Rappresenta una singola operazione batch."""

    def __init__(self, operation_type: str, field: str, value: Any, file_names: List[str]):
        self.operation_type = operation_type  # 'set', 'append', 'remove'
        self.field = field
        self.value = value
        self.file_names = file_names
        self.timestamp = datetime.now()

    def to_dict(self):
        return {
            'operation_type': self.operation_type,
            'field': self.field,
            'value': self.value,
            'file_count': len(self.file_names),
            'timestamp': self.timestamp.isoformat()
        }

def validate_batch_operation(operation: BatchOperation, df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Valida un'operazione batch prima dell'esecuzione.
    Restituisce (is_valid, error_message).
    """
    try:
        # Verifica che tutti i file esistano nel dataframe
        existing_files = set(df['file_name'].tolist())
        missing_files = [f for f in operation.file_names if f not in existing_files]

        if missing_files:
            return False, f"File non trovati nell'archivio: {', '.join(missing_files[:5])}"

        # Verifica che il campo sia valido
        valid_fields = {'title', 'authors', 'publication_year', 'category_id'}
        if operation.field not in valid_fields:
            return False, f"Campo non valido: {operation.field}"

        # Validazione specifica per tipo di operazione
        if operation.operation_type == 'set':
            if operation.field == 'publication_year' and operation.value is not None:
                try:
                    year = int(operation.value)
                    if year < 1000 or year > datetime.now().year + 1:
                        return False, f"Anno non valido: {operation.value}"
                except:
                    return False, f"Anno deve essere un numero valido: {operation.value}"

        elif operation.operation_type == 'append' and operation.field == 'authors':
            if not isinstance(operation.value, str) or not operation.value.strip():
                return False, "Nome autore non valido per operazione di aggiunta"

        return True, ""

    except Exception as e:
        return False, f"Errore validazione: {str(e)}"

def execute_batch_operation(operation: BatchOperation) -> Tuple[bool, str, int]:
    """
    Esegue un'operazione batch e restituisce (success, message, affected_count).
    """
    try:
        # Crea backup preventivo (in produzione, salva su file)
        df = get_papers_dataframe()
        if df.empty:
            return False, "Archivio vuoto", 0

        # Valida l'operazione
        is_valid, error_msg = validate_batch_operation(operation, df)
        if not is_valid:
            return False, error_msg, 0

        affected_count = 0

        for file_name in operation.file_names:
            try:
                # Trova il documento corrente
                file_df = df[df['file_name'] == file_name]
                if file_df.empty:
                    continue

                current_data = {
                    'title': file_df.iloc[0].get('title'),
                    'authors': file_df.iloc[0].get('authors', '[]'),
                    'publication_year': file_df.iloc[0].get('publication_year'),
                    'category_id': file_df.iloc[0].get('category_id')
                }

                # Applica l'operazione
                if operation.operation_type == 'set':
                    if operation.field == 'authors':
                        # Per gli autori, sostituisci completamente
                        current_data['authors'] = json.dumps([operation.value] if operation.value else [])
                    else:
                        current_data[operation.field] = operation.value

                elif operation.operation_type == 'append' and operation.field == 'authors':
                    # Aggiungi autore alla lista esistente
                    try:
                        current_authors = json.loads(current_data['authors']) if current_data['authors'] else []
                        if operation.value and operation.value.strip() not in current_authors:
                            current_authors.append(operation.value.strip())
                            current_data['authors'] = json.dumps(current_authors)
                    except:
                        current_data['authors'] = json.dumps([operation.value] if operation.value else [])

                elif operation.operation_type == 'remove' and operation.field == 'authors':
                    # Rimuovi autore dalla lista
                    try:
                        current_authors = json.loads(current_data['authors']) if current_data['authors'] else []
                        current_authors = [a for a in current_authors if a.strip() != operation.value.strip()]
                        current_data['authors'] = json.dumps(current_authors)
                    except:
                        pass

                # Esegui l'aggiornamento
                if update_paper_metadata(file_name, current_data):
                    affected_count += 1

            except Exception as e:
                print(f"Errore nell'aggiornamento di {file_name}: {e}")
                continue

        if affected_count > 0:
            return True, f"Operazione completata con successo. {affected_count} documenti aggiornati.", affected_count
        else:
            return False, "Nessun documento aggiornato", 0

    except Exception as e:
        return False, f"Errore durante l'operazione batch: {str(e)}", 0

def get_batch_preview(operation: BatchOperation, df: pd.DataFrame) -> List[Dict]:
    """
    Restituisce un'anteprima delle modifiche che saranno applicate.
    """
    try:
        preview_data = []

        for file_name in operation.file_names[:10]:  # Limita a 10 per performance
            file_df = df[df['file_name'] == file_name]
            if file_df.empty:
                continue

            current_row = file_df.iloc[0]
            current_data = {
                'title': current_row.get('title'),
                'authors': current_row.get('authors', '[]'),
                'publication_year': current_row.get('publication_year'),
                'category_id': current_row.get('category_id')
            }

            # Calcola i nuovi valori
            new_data = current_data.copy()

            if operation.operation_type == 'set':
                if operation.field == 'authors':
                    new_data['authors'] = json.dumps([operation.value] if operation.value else [])
                else:
                    new_data[operation.field] = operation.value

            elif operation.operation_type == 'append' and operation.field == 'authors':
                try:
                    current_authors = json.loads(current_data['authors']) if current_data['authors'] else []
                    if operation.value and operation.value.strip() not in current_authors:
                        current_authors.append(operation.value.strip())
                        new_data['authors'] = json.dumps(current_authors)
                except:
                    new_data['authors'] = json.dumps([operation.value] if operation.value else [])

            elif operation.operation_type == 'remove' and operation.field == 'authors':
                try:
                    current_authors = json.loads(current_data['authors']) if current_data['authors'] else []
                    current_authors = [a for a in current_authors if a.strip() != operation.value.strip()]
                    new_data['authors'] = json.dumps(current_authors)
                except:
                    pass

            preview_data.append({
                'file_name': file_name,
                'current_title': current_data.get('title', ''),
                'new_title': new_data.get('title', ''),
                'current_authors': current_data.get('authors', '[]'),
                'new_authors': new_data.get('authors', '[]'),
                'current_year': current_data.get('publication_year'),
                'new_year': new_data.get('publication_year'),
                'current_category': current_data.get('category_id', ''),
                'new_category': new_data.get('category_id', '')
            })

        return preview_data

    except Exception as e:
        print(f"Errore nella generazione anteprima: {e}")
        return []

def get_available_operations() -> List[Dict]:
    """Restituisce la lista delle operazioni batch disponibili."""
    return [
        {
            'id': 'set_title',
            'name': 'Imposta Titolo',
            'field': 'title',
            'operation_type': 'set',
            'description': 'Imposta lo stesso titolo per tutti i documenti selezionati'
        },
        {
            'id': 'set_year',
            'name': 'Imposta Anno',
            'field': 'publication_year',
            'operation_type': 'set',
            'description': 'Imposta lo stesso anno di pubblicazione per tutti i documenti selezionati'
        },
        {
            'id': 'add_author',
            'name': 'Aggiungi Autore',
            'field': 'authors',
            'operation_type': 'append',
            'description': 'Aggiunge un autore alla lista degli autori di tutti i documenti selezionati'
        },
        {
            'id': 'remove_author',
            'name': 'Rimuovi Autore',
            'field': 'authors',
            'operation_type': 'remove',
            'description': 'Rimuove un autore dalla lista degli autori di tutti i documenti selezionati'
        },
        {
            'id': 'set_category',
            'name': 'Cambia Categoria',
            'field': 'category_id',
            'operation_type': 'set',
            'description': 'Sposta tutti i documenti selezionati nella stessa categoria'
        }
    ]

def create_batch_operation(operation_id: str, value: Any, selected_files: List[str]) -> BatchOperation:
    """Crea un'operazione batch dai parametri forniti."""
    operations = get_available_operations()
    operation_config = next((op for op in operations if op['id'] == operation_id), None)

    if not operation_config:
        raise ValueError(f"Operazione non valida: {operation_id}")

    return BatchOperation(
        operation_type=operation_config['operation_type'],
        field=operation_config['field'],
        value=value,
        file_names=selected_files
    )
