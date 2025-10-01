"""
Modulo per le statistiche e analisi dell'archivio documentale.
Fornisce funzionalità per dashboard, metriche e analisi dei dati.
"""
import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta
from collections import Counter
import json
from typing import List, Dict, Any
from file_utils import db_connect, get_papers_dataframe

# --- CONFIGURAZIONE ---
DB_STORAGE_DIR = "db_memoria"
METADATA_DB_FILE = os.path.join(DB_STORAGE_DIR, "metadata.sqlite")

def get_basic_stats():
    """Restituisce le statistiche di base dell'archivio."""
    try:
        df = get_papers_dataframe()
        if df.empty:
            return {
                'total_documents': 0,
                'total_categories': 0,
                'total_authors': 0,
                'avg_documents_per_category': 0,
                'recent_documents': 0,
                'oldest_document': None,
                'newest_document': None
            }

        # Calcoli di base
        total_docs = len(df)
        total_cats = df['category_id'].nunique()

        # Conta autori unici (gestisce JSON array)
        all_authors = []
        for authors_json in df['authors'].dropna():
            try:
                authors_list = json.loads(authors_json)
                all_authors.extend(authors_list)
            except:
                continue

        unique_authors = len(set(all_authors)) if all_authors else 0

        # Documenti recenti (ultimi 7 giorni)
        recent_docs = 0
        if 'processed_at' in df.columns:
            try:
                week_ago = datetime.now() - timedelta(days=7)
                df['processed_at'] = pd.to_datetime(df['processed_at'], errors='coerce')
                recent_docs = len(df[df['processed_at'] >= week_ago])
            except:
                recent_docs = 0

        # Documenti più vecchio e più nuovo
        oldest_doc = None
        newest_doc = None
        if 'processed_at' in df.columns:
            try:
                valid_dates = df['processed_at'].dropna()
                if not valid_dates.empty:
                    oldest_doc = valid_dates.min().strftime('%Y-%m-%d')
                    newest_doc = valid_dates.max().strftime('%Y-%m-%d')
            except:
                pass

        return {
            'total_documents': total_docs,
            'total_categories': total_cats,
            'total_authors': unique_authors,
            'avg_documents_per_category': round(total_docs / total_cats, 1) if total_cats > 0 else 0,
            'recent_documents': recent_docs,
            'oldest_document': oldest_doc,
            'newest_document': newest_doc
        }

    except Exception as e:
        print(f"Errore nel calcolo statistiche di base: {e}")
        return {
            'total_documents': 0,
            'total_categories': 0,
            'total_authors': 0,
            'avg_documents_per_category': 0,
            'recent_documents': 0,
            'oldest_document': None,
            'newest_document': None
        }

def get_category_distribution():
    """Restituisce la distribuzione dei documenti per categoria."""
    try:
        df = get_papers_dataframe()
        if df.empty:
            return []

        # Raggruppa per categoria e conta
        category_stats = df.groupby(['category_id', 'category_name']).size().reset_index(name='count')
        category_stats = category_stats.sort_values('count', ascending=False)

        # Calcola percentuali
        total = category_stats['count'].sum()
        category_stats['percentage'] = ((category_stats['count'] / total) * 100).round(1)

        return category_stats.to_dict('records')

    except Exception as e:
        print(f"Errore nel calcolo distribuzione categorie: {e}")
        return []

def get_author_stats():
    """Restituisce statistiche sugli autori."""
    try:
        df = get_papers_dataframe()
        if df.empty:
            return []

        # Conta occorrenze autori
        author_counts = Counter()
        for authors_json in df['authors'].dropna():
            try:
                authors_list = json.loads(authors_json)
                for author in authors_list:
                    author_counts[author.strip()] += 1
            except:
                continue

        # Crea lista ordinata
        author_stats = [
            {'author': author, 'document_count': count}
            for author, count in author_counts.most_common(20)  # Top 20 autori
        ]

        return author_stats

    except Exception as e:
        print(f"Errore nel calcolo statistiche autori: {e}")
        return []

def get_temporal_trend():
    """Restituisce il trend temporale dei documenti processati."""
    try:
        df = get_papers_dataframe()
        if df.empty or 'processed_at' not in df.columns:
            return []

        # Converte date e raggruppa per mese
        df['processed_at'] = pd.to_datetime(df['processed_at'], errors='coerce')
        monthly_trend = df.groupby(df['processed_at'].dt.to_period('M')).size().reset_index(name='count')
        monthly_trend['period'] = monthly_trend['processed_at'].astype(str)
        monthly_trend = monthly_trend.sort_values('processed_at')

        return monthly_trend.to_dict('records')

    except Exception as e:
        print(f"Errore nel calcolo trend temporale: {e}")
        return []

def get_data_quality_metrics():
    """Restituisce metriche sulla qualità dei dati."""
    try:
        df = get_papers_dataframe()
        if df.empty:
            return {
                'total_documents': 0,
                'docs_with_preview': 0,
                'docs_with_year': 0,
                'docs_with_authors': 0,
                'completeness_score': 0
            }

        total_docs = len(df)

        # Documenti con anteprima
        docs_with_preview = len(df[df['formatted_preview'].notna() & (df['formatted_preview'] != '')])

        # Documenti con anno pubblicazione
        docs_with_year = len(df[df['publication_year'].notna()])

        # Documenti con autori
        docs_with_authors = 0
        for authors_json in df['authors'].dropna():
            try:
                authors_list = json.loads(authors_json)
                if authors_list and any(author.strip() for author in authors_list):
                    docs_with_authors += 1
            except:
                continue

        # Calcolo punteggio completezza (0-100)
        completeness_score = 0
        if total_docs > 0:
            preview_score = (docs_with_preview / total_docs) * 40  # 40% peso
            year_score = (docs_with_year / total_docs) * 30       # 30% peso
            authors_score = (docs_with_authors / total_docs) * 30  # 30% peso
            completeness_score = round(preview_score + year_score + authors_score, 1)

        return {
            'total_documents': total_docs,
            'docs_with_preview': docs_with_preview,
            'docs_with_year': docs_with_year,
            'docs_with_authors': docs_with_authors,
            'completeness_score': completeness_score
        }

    except Exception as e:
        print(f"Errore nel calcolo metriche qualità: {e}")
        return {
            'total_documents': 0,
            'docs_with_preview': 0,
            'docs_with_year': 0,
            'docs_with_authors': 0,
            'completeness_score': 0
        }

def get_top_categories(limit=10):
    """Restituisce le categorie più popolate."""
    try:
        category_dist = get_category_distribution()
        return sorted(category_dist, key=lambda x: x['count'], reverse=True)[:limit]
    except:
        return []

def get_recent_activity(days=7):
    """Restituisce l'attività recente dell'archivio."""
    try:
        df = get_papers_dataframe()
        if df.empty or 'processed_at' not in df.columns:
            return []

        # Filtra documenti recenti
        cutoff_date = datetime.now() - timedelta(days=days)
        df['processed_at'] = pd.to_datetime(df['processed_at'], errors='coerce')
        recent_df = df[df['processed_at'] >= cutoff_date]

        # Ordina per data più recente
        recent_df = recent_df.sort_values('processed_at', ascending=False)

        return recent_df[['file_name', 'title', 'category_name', 'processed_at']].to_dict('records')

    except Exception as e:
        print(f"Errore nel calcolo attività recente: {e}")
        return []

@st.cache_data(ttl=300)  # Cache per 5 minuti
def get_comprehensive_stats():
    """Restituisce tutte le statistiche in un unico dizionario."""
    return {
        'basic_stats': get_basic_stats(),
        'category_distribution': get_category_distribution(),
        'author_stats': get_author_stats(),
        'temporal_trend': get_temporal_trend(),
        'data_quality': get_data_quality_metrics(),
        'top_categories': get_top_categories(),
        'recent_activity': get_recent_activity(),
        'last_updated': datetime.now().isoformat()
    }
