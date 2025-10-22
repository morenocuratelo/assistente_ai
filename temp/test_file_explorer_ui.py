#!/usr/bin/env python3
"""
Test script for the File Explorer UI.
Creates sample data and runs the Streamlit interface.
"""

import sys
import os
import shutil
import subprocess
import time
import threading

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_sample_data():
    """Create sample directory structure and database entries for testing."""
    print("🏗️ Creating sample data for UI testing...")

    # Create main archive directory
    archive_dir = "Dall_Origine_alla_Complessita"
    os.makedirs(archive_dir, exist_ok=True)

    # Create sample category structure
    categories = [
        "P1_IL_PALCOSCENICO_COSMICO_E_BIOLOGICO/C01",
        "P1_IL_PALCOSCENICO_COSMICO_E_BIOLOGICO/C02",
        "P2_L_ASCESA_DEL_GENERE_HOMO/C04",
        "P2_L_ASCESA_DEL_GENERE_HOMO/C05"
    ]

    sample_files_data = [
        ("documento_universo.pdf", "L'Universo e le sue Origini", "Marco Rossi, Giulia Bianchi", 2023),
        ("origine_vita.txt", "L'Origine della Vita sulla Terra", "Alessandra Verdi", 2022),
        ("evoluzione_specie.docx", "L'Evoluzione delle Specie", "Roberto Neri, Francesca Gialli", 2024),
        ("cosmologia_moderna.pdf", "Cosmologia Moderna", "Stefano Blu", 2021),
        ("antropologia_evolutiva.txt", "Antropologia Evolutiva", "Maria Rosa", 2023),
        ("homo_sapiens.docx", "L'Emergere di Homo Sapiens", "Luca Verdi, Anna Rossi", 2022)
    ]

    for category in categories:
        category_path = os.path.join(archive_dir, category)
        os.makedirs(category_path, exist_ok=True)

        # Create 2-3 files per category
        files_for_category = sample_files_data[:3] if "C01" in category else sample_files_data[3:]

        for file_name, title, authors, year in files_for_category:
            file_path = os.path.join(category_path, file_name)

            # Create file with content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"""Documento di esempio: {title}

Autori: {authors}
Anno: {year}
Categoria: {category}

Questo è un documento di esempio per testare l'interfaccia del file explorer.
Contiene informazioni sulla categoria {category} del percorso di conoscenza.
""")

    print(f"✅ Created sample structure in '{archive_dir}' with {len(sample_files_data)} files")

def cleanup_sample_data():
    """Clean up the sample data."""
    archive_dir = "Dall_Origine_alla_Complessita"
    if os.path.exists(archive_dir):
        shutil.rmtree(archive_dir)
        print(f"🗑️ Cleaned up sample data '{archive_dir}'")

def run_streamlit_app():
    """Run the Streamlit app in a separate process."""
    try:
        print("🚀 Starting Streamlit File Explorer...")
        print("📱 The app will open in your browser at: http://localhost:8501")
        print("🔄 Press Ctrl+C to stop the app")

        # Run the Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "file_explorer_ui.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ], cwd=os.getcwd())

    except KeyboardInterrupt:
        print("\n🛑 Stopping Streamlit app...")
    except Exception as e:
        print(f"❌ Error running Streamlit app: {e}")

def main():
    """Main function to test the file explorer UI."""
    print("🧪 Testing File Explorer UI - Phase 2")
    print("=" * 50)

    # Create sample data
    create_sample_data()

    try:
        # Run the Streamlit app
        run_streamlit_app()

    finally:
        # Clean up
        cleanup_sample_data()
        print("✅ Test completed and cleaned up")

if __name__ == "__main__":
    main()
