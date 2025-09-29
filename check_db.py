#!/usr/bin/env python3
"""
Script di diagnostica per Archivista AI
Verifica la configurazione e lo stato del sistema
"""

import os
import sys
from dotenv import load_dotenv

def check_env_file():
    """Verifica il caricamento del file .env"""
    print("🔍 VERIFICA FILE .ENV")
    print("=" * 50)

    # Cerca il file .env in più posizioni
    project_root = os.path.abspath(os.path.dirname(__file__))
    possible_paths = [
        os.path.join(project_root, '.env'),
        os.path.join(os.getcwd(), '.env'),
        os.path.join(os.path.dirname(project_root), '.env')
    ]

    dotenv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            dotenv_path = path
            break

    if dotenv_path:
        print(f"✅ File .env trovato: {dotenv_path}")
        load_dotenv(dotenv_path=dotenv_path)
        print("✅ Variabili d'ambiente caricate")
    else:
        print("❌ File .env NON TROVATO!")
        print(f"Posizioni cercate: {', '.join(possible_paths)}")
        return False

    return True

def check_api_keys():
    """Verifica le chiavi API"""
    print("\n🔑 VERIFICA CHIAVI API")
    print("=" * 50)

    ollama_base_url = os.getenv('OLLAMA_BASE_URL')
    openai_api_key = os.getenv('OPENAI_API_KEY')

    print(f"OLLAMA_BASE_URL: {'✅ impostato' if ollama_base_url else '❌ non impostato'}")
    if ollama_base_url:
        print(f"  Valore: {ollama_base_url}")

    print(f"OPENAI_API_KEY: {'✅ impostato' if openai_api_key else '❌ non impostato'}")
    if openai_api_key:
        print(f"  Preview: {openai_api_key[:20]}...")
        if not openai_api_key.startswith('sk-'):
            print("  ⚠️  ATTENZIONE: La chiave non inizia con 'sk-'")
        else:
            print("  ✅ Formato chiave valido")

    return openai_api_key is not None

def check_database():
    """Verifica lo stato del database"""
    print("\n🗄️  VERIFICA DATABASE")
    print("=" * 50)

    db_dir = "db_memoria"
    metadata_file = os.path.join(db_dir, "metadata.sqlite")

    if os.path.exists(metadata_file):
        print(f"✅ Database trovato: {metadata_file}")

        # Conta i record
        try:
            import sqlite3
            conn = sqlite3.connect(metadata_file)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM papers")
            count = cursor.fetchone()[0]
            print(f"✅ Record nel database: {count}")

            # Verifica file fisici
            cursor.execute("SELECT file_name, category_id FROM papers")
            papers = cursor.fetchall()

            missing_files = 0
            for paper in papers:
                file_name = paper[0]
                category_id = paper[1]
                file_path = os.path.join("Dall_Origine_alla_Complessita", *category_id.split('/'), file_name)
                if not os.path.exists(file_path):
                    missing_files += 1
                    print(f"  ❌ File mancante: {file_name}")

            if missing_files == 0:
                print("✅ Tutti i file fisici sono presenti")
            else:
                print(f"⚠️  {missing_files} file fisici mancanti")

            conn.close()

        except Exception as e:
            print(f"❌ Errore accesso database: {e}")

    else:
        print(f"❌ Database non trovato: {metadata_file}")

def check_directories():
    """Verifica le directory necessarie"""
    print("\n📁 VERIFICA DIRECTORY")
    print("=" * 50)

    directories = [
        "db_memoria",
        "documenti_da_processare",
        "Dall_Origine_alla_Complessita",
        "model_cache"
    ]

    for dir_name in directories:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ (manca)")

def main():
    """Funzione principale"""
    print("🔧 DIAGNOSTICA ARCHIVISTA AI")
    print("=" * 60)

    # Verifica .env
    env_ok = check_env_file()

    # Verifica chiavi API
    api_ok = check_api_keys()

    # Verifica database
    check_database()

    # Verifica directory
    check_directories()

    print("\n📋 RIEPILOGO")
    print("=" * 50)

    if env_ok and api_ok:
        print("✅ Configurazione di base OK")
        print("💡 Prova ad avviare l'applicazione con: streamlit run main.py")
    else:
        print("❌ Problemi nella configurazione")
        print("💡 Verifica il file .env e le chiavi API")

if __name__ == "__main__":
    main()
