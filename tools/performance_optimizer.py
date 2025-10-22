#!/usr/bin/env python3
"""
Modulo per ottimizzazioni delle performance del sistema di indicizzazione
"""
import os
import time
import hashlib
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ProcessingMetrics:
    """Metrica di processamento per ottimizzazioni"""
    file_path: str
    file_size: int
    processing_time: float
    extractor_used: str
    text_length: int
    success: bool
    error_message: Optional[str] = None

class PerformanceOptimizer:
    """Ottimizzatore delle performance per il sistema di indicizzazione"""

    def __init__(self):
        self.metrics_file = "db_memoria/processing_metrics.json"
        self.extractor_performance = {}
        self.cache_file = "db_memoria/file_cache.json"
        self.file_cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict]:
        """Carica la cache dei file processati"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        """Salva la cache su disco"""
        os.makedirs("db_memoria", exist_ok=True)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.file_cache, f, indent=2)

    def get_file_hash(self, file_path: str) -> str:
        """Calcola hash del file per verificare modifiche"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return ""

    def is_file_processed(self, file_path: str) -> bool:
        """Verifica se il file è già stato processato"""
        file_hash = self.get_file_hash(file_path)
        if file_hash and file_hash in self.file_cache:
            cache_data = self.file_cache[file_hash]
            # Verifica se il file è stato modificato
            if os.path.getmtime(file_path) <= cache_data.get('processed_time', 0):
                return True
        return False

    def select_best_extractor(self, file_path: str) -> str:
        """Seleziona l'estrattore più veloce per il tipo di file"""
        file_ext = Path(file_path).suffix.lower()

        if file_ext in self.extractor_performance:
            # Restituisci l'estrattore con le migliori performance
            best_extractor = min(
                self.extractor_performance[file_ext].items(),
                key=lambda x: x[1]['avg_time']
            )
            return best_extractor[0]

        # Default extractor order basato su velocità generale
        default_extractors = ['PyMuPDF', 'pdfplumber', 'PyPDF2', 'pdfminer']
        return default_extractors[0]

    def record_metrics(self, metrics: ProcessingMetrics):
        """Registra le metriche di processamento"""
        file_ext = Path(metrics.file_path).suffix.lower()

        if file_ext not in self.extractor_performance:
            self.extractor_performance[file_ext] = {}

        extractor_data = self.extractor_performance[file_ext].setdefault(metrics.extractor_used, {
            'count': 0,
            'total_time': 0,
            'success_count': 0,
            'avg_time': 0
        })

        extractor_data['count'] += 1
        extractor_data['total_time'] += metrics.processing_time
        if metrics.success:
            extractor_data['success_count'] += 1

        extractor_data['avg_time'] = extractor_data['total_time'] / extractor_data['count']

        # Salva metriche su disco
        self._save_metrics()

    def _save_metrics(self):
        """Salva le metriche su disco"""
        metrics_data = {
            'extractor_performance': self.extractor_performance,
            'last_updated': time.time()
        }

        os.makedirs("db_memoria", exist_ok=True)
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=2)

    def get_performance_report(self) -> Dict:
        """Genera report delle performance"""
        total_files = sum(
            sum(ext['count'] for ext in file_types.values())
            for file_types in [self.extractor_performance]
        )

        return {
            'total_files_processed': total_files,
            'extractor_performance': self.extractor_performance,
            'cache_size': len(self.file_cache),
            'optimization_suggestions': self._generate_suggestions()
        }

    def _generate_suggestions(self) -> List[str]:
        """Genera suggerimenti per ottimizzazioni"""
        suggestions = []

        # Analizza performance degli estrattori
        for file_ext, extractors in self.extractor_performance.items():
            if len(extractors) > 1:
                best_extractor = min(extractors.items(), key=lambda x: x[1]['avg_time'])
                worst_extractor = max(extractors.items(), key=lambda x: x[1]['avg_time'])

                if worst_extractor[1]['avg_time'] > best_extractor[1]['avg_time'] * 1.5:
                    diff_time = worst_extractor[1]['avg_time'] - best_extractor[1]['avg_time']
                    suggestions.append(
                        f"Per i file {file_ext}, considera di usare {best_extractor[0]} "
                        f"invece di {worst_extractor[0]} (differenza: {diff_time:.2f}s)"
                    )

        if len(self.file_cache) > 100:
            suggestions.append("Considera pulizia cache file per migliorare performance I/O")

        return suggestions

# Istanza globale dell'ottimizzatore
performance_optimizer = PerformanceOptimizer()

def optimize_pdf_extraction(file_path: str, extractor_name: str, start_time: float) -> str:
    """Ottimizza l'estrazione PDF registrando metriche"""
    end_time = time.time()
    processing_time = end_time - start_time

    # Determina lunghezza del testo estratto
    try:
        file_size = os.path.getsize(file_path)
        # Questo è un placeholder - nella pratica dovresti passare la lunghezza del testo
        text_length = 0  # Da calcolare durante l'estrazione

        metrics = ProcessingMetrics(
            file_path=file_path,
            file_size=file_size,
            processing_time=processing_time,
            extractor_used=extractor_name,
            text_length=text_length,
            success=True
        )

        performance_optimizer.record_metrics(metrics)
        return extractor_name

    except Exception as e:
        print(f"⚠️ Errore registrazione metriche: {e}")
        return extractor_name

def get_optimized_extractor_list(file_path: str) -> List[Tuple[str, callable]]:
    """Restituisce lista di estrattori ordinata per performance"""
    file_ext = Path(file_path).suffix.lower()

    # Lista default degli estrattori
    all_extractors = [
        ("PyMuPDF", extract_text_pymupdf),
        ("pdfplumber", extract_text_pdfplumber),
        ("PyPDF2", extract_text_pypdf2),
        ("pdfminer", extract_text_pdfminer)
    ]

    if file_ext in performance_optimizer.extractor_performance:
        # Ordina per performance (tempo medio crescente)
        ext_performance = performance_optimizer.extractor_performance[file_ext]

        # Separa estrattori con dati di performance da quelli senza
        known_extractors = []
        unknown_extractors = []

        for name, func in all_extractors:
            if name in ext_performance:
                known_extractors.append((name, func, ext_performance[name]['avg_time']))
            else:
                unknown_extractors.append((name, func))

        # Ordina known_extractors per performance
        known_extractors.sort(key=lambda x: x[2])

        # Combina: prima i più veloci noti, poi gli sconosciuti
        optimized_extractors = [(name, func) for name, func, _ in known_extractors] + unknown_extractors

        return optimized_extractors

    return all_extractors

# Import delle funzioni di estrazione (devono essere definite altrove)
try:
    from archivista_processing import (
        extract_text_pymupdf, extract_text_pdfplumber,
        extract_text_pypdf2, extract_text_pdfminer
    )
except ImportError:
    # Placeholder functions per test
    def extract_text_pymupdf(file_path: str) -> str: return ""
    def extract_text_pdfplumber(file_path: str) -> str: return ""
    def extract_text_pypdf2(file_path: str) -> str: return ""
    def extract_text_pdfminer(file_path: str) -> str: return ""
