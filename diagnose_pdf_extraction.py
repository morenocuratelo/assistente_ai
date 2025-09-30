#!/usr/bin/env python3
"""
Script diagnostico per testare l'estrazione PDF sui file in errore
"""
import os
import sys
import traceback
from pathlib import Path

# Aggiungi il path corrente per importare i moduli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pdf_extraction():
    """Testa tutti gli estrattori PDF sui file in errore"""

    error_dir = "documenti_da_processare/_error"
    if not os.path.exists(error_dir):
        print(f"❌ Directory errori non trovata: {error_dir}")
        return

    pdf_files = [f for f in os.listdir(error_dir) if f.lower().endswith('.pdf')]

    if not pdf_files:
        print(f"❌ Nessun file PDF trovato in: {error_dir}")
        return

    print(f"📋 Trovati {len(pdf_files)} file PDF in errore:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file}")

    # Test su ogni file PDF
    for pdf_file in pdf_files:
        pdf_path = os.path.join(error_dir, pdf_file)
        print(f"\n🔍 Testando: {pdf_file}")
        print("=" * 50)

        # Test 1: Verifica se il file è leggibile
        try:
            file_size = os.path.getsize(pdf_path)
            print(f"📏 Dimensione file: {file_size:,}","ytes")

            # Prova ad aprire il file
            with open(pdf_path, 'rb') as f:
                header = f.read(20)
            print(f"📖 Header file: {header[:10].hex()}...")
            print("✅ File accessibile")

        except Exception as e:
            print(f"❌ Errore accesso file: {e}")
            continue

        # Test 2: Prova ogni estrattore PDF
        extractors = [
            ("PyMuPDF (fitz)", test_pymupdf),
            ("PyPDF2 (pypdf)", test_pypdf2),
            ("pdfplumber", test_pdfplumber),
            ("pdfminer", test_pdfminer)
        ]

        successful_extractors = []

        for name, test_func in extractors:
            print(f"\n🧪 Testando {name}...")
            try:
                text = test_func(pdf_path)
                if text and text.strip():
                    char_count = len(text)
                    word_count = len(text.split())
                    print(f"✅ {name}: SUCCESSO")
                    print(f"   Caratteri: {char_count:,}")
                    print(f"   Parole: {word_count:,}")
                    print(f"   Anteprima: {text[:200].replace(chr(10), ' ').replace(chr(13), ' ')}...")
                    successful_extractors.append(name)
                else:
                    print(f"⚠️ {name}: Testo vuoto")

            except Exception as e:
                print(f"❌ {name}: FALLITO - {e}")
                print(f"   Traceback: {traceback.format_exc()}")

        print(f"\n📊 Risultato per {pdf_file}:")
        print(f"   Estrattori funzionanti: {len(successful_extractors)}/{len(extractors)}")
        if successful_extractors:
            print(f"   ✅ Riuscito con: {', '.join(successful_extractors)}")
        else:
            print("   ❌ Nessun estrattore ha funzionato")

        print("-" * 50)

def test_pymupdf(file_path):
    """Test PyMuPDF"""
    try:
        import fitz
        with fitz.open(file_path) as doc:
            return "".join(page.get_text() for page in doc)
    except ImportError:
        raise ImportError("PyMuPDF (fitz) non installato")

def test_pypdf2(file_path):
    """Test PyPDF2"""
    try:
        from pypdf import PdfReader
        with open(file_path, 'rb') as f:
            return "".join(p.extract_text() for p in PdfReader(f).pages)
    except ImportError:
        raise ImportError("PyPDF2 (pypdf) non installato")

def test_pdfplumber(file_path):
    """Test pdfplumber"""
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            return "".join(p.extract_text() or "" for p in pdf.pages)
    except ImportError:
        raise ImportError("pdfplumber non installato")

def test_pdfminer(file_path):
    """Test pdfminer"""
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract
        return pdfminer_extract(file_path)
    except ImportError:
        raise ImportError("pdfminer non installato")

def test_llm_configuration():
    """Test configurazione LLM"""
    print("\n🤖 Test configurazione LLM")
    print("=" * 50)

    # Test servizi AI
    try:
        from config import initialize_services
        from llama_index.core import Settings

        print("🔧 Inizializzazione servizi...")
        initialize_services()

        if Settings.llm:
            print(f"✅ LLM configurato: {type(Settings.llm).__name__}")
            try:
                # Test connessione con una query semplice
                response = Settings.llm.complete("Ciao, riesci a sentirmi?")
                print(f"✅ Test LLM: {str(response)[:100]}...")
            except Exception as e:
                print(f"⚠️ LLM configurato ma test fallito: {e}")
        else:
            print("❌ Nessun LLM configurato")

        if Settings.embed_model:
            print(f"✅ Modello embedding configurato: {type(Settings.embed_model).__name__}")
        else:
            print("❌ Nessun modello embedding configurato")

    except Exception as e:
        print(f"❌ Errore configurazione servizi: {e}")
        print(f"   Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    print("🔬 DIAGNOSTICA SISTEMA DI INDICIZZAZIONE")
    print("=" * 60)

    # Test configurazione LLM
    test_llm_configuration()

    # Test estrazione PDF
    test_pdf_extraction()

    print("\n" + "=" * 60)
    print("✅ Diagnostica completata")
