"""
Modulo per l'esportazione dei dati dell'archivio in vari formati.
Supporta CSV, JSON e Excel con filtri avanzati.
"""
import pandas as pd
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import base64
import io
from file_utils import get_papers_dataframe
import knowledge_structure

# --- CONFIGURAZIONE ---
DB_STORAGE_DIR = "db_memoria"

def get_exportable_dataframe(
    file_names: Optional[List[str]] = None,
    category_filter: Optional[str] = None,
    author_filter: Optional[str] = None,
    year_filter: Optional[int] = None,
    include_preview: bool = False
) -> pd.DataFrame:
    """
    Restituisce un DataFrame filtrato per l'esportazione.
    """
    try:
        df = get_papers_dataframe()
        if df.empty:
            return pd.DataFrame()

        # Applica filtri
        if file_names:
            df = df[df['file_name'].isin(file_names)]

        if category_filter and category_filter != "Tutte":
            df = df[df['category_id'] == category_filter]

        if author_filter:
            # Filtra documenti che contengono l'autore specificato
            filtered_df = pd.DataFrame()
            for _, row in df.iterrows():
                try:
                    authors_list = json.loads(row.get('authors', '[]'))
                    if any(author_filter.lower() in author.lower() for author in authors_list):
                        filtered_df = pd.concat([filtered_df, pd.DataFrame([row])], ignore_index=True)
                except:
                    continue
            df = filtered_df

        if year_filter:
            df = df[df['publication_year'] == year_filter]

        # Seleziona colonne per l'esportazione
        export_columns = [
            'file_name', 'title', 'authors', 'publication_year',
            'category_id', 'category_name', 'processed_at'
        ]

        if include_preview:
            export_columns.append('formatted_preview')

        # Verifica che tutte le colonne esistano
        available_columns = [col for col in export_columns if col in df.columns]
        df = df[available_columns].copy()

        # Rinomina colonne per leggibilità
        column_rename = {
            'file_name': 'Nome File',
            'title': 'Titolo',
            'authors': 'Autori',
            'publication_year': 'Anno Pubblicazione',
            'category_id': 'ID Categoria',
            'category_name': 'Nome Categoria',
            'processed_at': 'Data Elaborazione',
            'formatted_preview': 'Anteprima'
        }

        df = df.rename(columns=column_rename)

        return df

    except Exception as e:
        print(f"Errore nella preparazione dati per esportazione: {e}")
        return pd.DataFrame()

def export_to_csv(
    df: pd.DataFrame,
    include_preview: bool = False,
    delimiter: str = ','
) -> str:
    """
    Esporta il DataFrame in formato CSV.
    Restituisce il contenuto CSV come stringa.
    """
    try:
        if df.empty:
            return ""

        # Crea buffer in memoria
        output = io.StringIO()

        # Esporta con configurazione ottimale
        df.to_csv(
            output,
            index=False,
            sep=delimiter,
            encoding='utf-8-sig',  # UTF-8 con BOM per Excel
            quoting=1,  # Quote solo campi necessari
            quotechar='"',
            doublequote=True,
            escapechar='\\'
        )

        return output.getvalue()

    except Exception as e:
        print(f"Errore esportazione CSV: {e}")
        return ""

def export_to_json(
    df: pd.DataFrame,
    include_preview: bool = False,
    pretty_print: bool = True
) -> str:
    """
    Esporta il DataFrame in formato JSON.
    """
    try:
        if df.empty:
            return "[]"

        # Converte DataFrame in lista di dizionari
        records = df.to_dict('records')

        # Configurazione JSON
        indent = 2 if pretty_print else None
        separators = (', ', ': ') if pretty_print else (',', ':')

        return json.dumps(
            records,
            indent=indent,
            separators=separators,
            ensure_ascii=False,
            default=str  # Gestisce tipi non serializzabili
        )

    except Exception as e:
        print(f"Errore esportazione JSON: {e}")
        return "[]"

def export_to_excel(df: pd.DataFrame, include_preview: bool = False) -> bytes:
    """
    Esporta il DataFrame in formato Excel.
    Restituisce i bytes del file Excel.
    """
    try:
        if df.empty:
            return b""

        # Crea buffer in memoria
        output = io.BytesIO()

        # Crea Excel writer
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Foglio principale con dati
            df.to_excel(writer, sheet_name='Documenti', index=False)

            # Foglio con metadati
            metadata_df = pd.DataFrame([{
                'Campo': 'Data Esportazione',
                'Valore': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, {
                'Campo': 'Numero Documenti',
                'Valore': len(df)
            }, {
                'Campo': 'Include Anteprime',
                'Valore': 'Sì' if include_preview else 'No'
            }])

            metadata_df.to_excel(writer, sheet_name='Metadati', index=False)

        return output.getvalue()

    except ImportError:
        print("openpyxl non disponibile per esportazione Excel")
        return b""
    except Exception as e:
        print(f"Errore esportazione Excel: {e}")
        return b""

def get_export_filename(format_type: str, include_preview: bool = False) -> str:
    """
    Genera un nome file appropriato per l'esportazione.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    preview_suffix = "_con_anteprime" if include_preview else ""

    format_extensions = {
        'csv': '.csv',
        'json': '.json',
        'excel': '.xlsx'
    }

    extension = format_extensions.get(format_type.lower(), '.csv')
    return f"archivio_documenti_{timestamp}{preview_suffix}{extension}"

def get_category_choices_for_filter():
    """Restituisce le categorie disponibili per il filtro di esportazione."""
    try:
        categories = knowledge_structure.get_category_choices()
        return categories
    except:
        return []

def get_author_choices_for_filter():
    """Restituisce gli autori disponibili per il filtro di esportazione."""
    try:
        from statistics import get_author_stats
        authors = get_author_stats()
        return [author['author'] for author in authors[:50]]  # Top 50 autori
    except:
        return []

def get_year_choices_for_filter():
    """Restituisce gli anni disponibili per il filtro di esportazione."""
    try:
        df = get_papers_dataframe()
        if df.empty or 'publication_year' not in df.columns:
            return []

        years = df['publication_year'].dropna().astype(int).unique()
        return sorted(years.tolist(), reverse=True)
    except:
        return []

def create_export_data(
    format_type: str,
    file_names: Optional[List[str]] = None,
    category_filter: Optional[str] = None,
    author_filter: Optional[str] = None,
    year_filter: Optional[int] = None,
    include_preview: bool = False
) -> Tuple[str, bytes]:
    """
    Crea i dati di esportazione nel formato richiesto.
    Restituisce (filename, file_content).
    """
    try:
        # Ottieni DataFrame filtrato
        df = get_exportable_dataframe(
            file_names=file_names,
            category_filter=category_filter,
            author_filter=author_filter,
            year_filter=year_filter,
            include_preview=include_preview
        )

        if df.empty:
            return "empty_export.csv", b""

        # Crea nome file
        filename = get_export_filename(format_type, include_preview)

        # Esporta nel formato richiesto
        if format_type.lower() == 'csv':
            content = export_to_csv(df, include_preview)
            return filename, content.encode('utf-8-sig')

        elif format_type.lower() == 'json':
            content = export_to_json(df, include_preview)
            return filename, content.encode('utf-8')

        elif format_type.lower() == 'excel':
            content_bytes = export_to_excel(df, include_preview)
            return filename, content_bytes

        else:
            # Default CSV
            content = export_to_csv(df, include_preview)
            return filename, content.encode('utf-8-sig')

    except Exception as e:
        print(f"Errore creazione dati esportazione: {e}")
        return "error_export.csv", b""

def get_export_summary(
    file_names: Optional[List[str]] = None,
    category_filter: Optional[str] = None,
    author_filter: Optional[str] = None,
    year_filter: Optional[int] = None,
    include_preview: bool = False
) -> Dict[str, Any]:
    """
    Restituisce un riepilogo dei dati che saranno esportati.
    """
    try:
        df = get_exportable_dataframe(
            file_names=file_names,
            category_filter=category_filter,
            author_filter=author_filter,
            year_filter=year_filter,
            include_preview=include_preview
        )

        if df.empty:
            return {
                'document_count': 0,
                'category_count': 0,
                'author_count': 0,
                'year_range': None,
                'file_size_estimate': '0 KB'
            }

        # Calcola statistiche
        doc_count = len(df)

        # Conta categorie uniche
        cat_column = 'Nome Categoria' if 'Nome Categoria' in df.columns else 'category_name'
        cat_count = df[cat_column].nunique() if cat_column in df.columns else 0

        # Conta autori unici
        author_count = 0
        if 'Autori' in df.columns:
            all_authors = []
            for authors_json in df['Autori'].dropna():
                try:
                    authors_list = json.loads(authors_json)
                    all_authors.extend(authors_list)
                except:
                    continue
            author_count = len(set(all_authors)) if all_authors else 0

        # Range anni
        year_range = None
        if 'Anno Pubblicazione' in df.columns:
            years = df['Anno Pubblicazione'].dropna()
            if not years.empty:
                year_range = f"{int(years.min())} - {int(years.max())}"

        # Stima dimensione file (approssimativa)
        estimated_size = len(df.to_string()) * 1.5  # Moltiplicatore approssimativo
        if estimated_size < 1024:
            size_str = f"{estimated_size:.0f} B"
        elif estimated_size < 1024 * 1024:
            size_str = f"{estimated_size/1024:.1f} KB"
        else:
            size_str = f"{estimated_size/(1024*1024):.1f} MB"

        return {
            'document_count': doc_count,
            'category_count': cat_count,
            'author_count': author_count,
            'year_range': year_range,
            'file_size_estimate': size_str
        }

    except Exception as e:
        print(f"Errore calcolo riepilogo esportazione: {e}")
        return {
            'document_count': 0,
            'category_count': 0,
            'author_count': 0,
            'year_range': None,
            'file_size_estimate': '0 KB'
        }
