#!/usr/bin/env python3
"""
Test script for File Explorer UI - Phase 3 Features.
Tests the enhanced UI with file selection, context menus, and action handling.
"""

import sys
import os
import shutil
import subprocess

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_enhanced_sample_data():
    """Create enhanced sample data with more realistic content."""
    print("🏗️ Creating enhanced sample data for Phase 3 testing...")

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

    # Enhanced sample files with more metadata
    sample_files_data = [
        ("documento_universo.pdf", "L'Universo e le sue Origini", "Marco Rossi, Giulia Bianchi", 2023, "Studio completo sull'origine dell'universo"),
        ("origine_vita.txt", "L'Origine della Vita sulla Terra", "Alessandra Verdi", 2022, "Analisi dei processi chimici che hanno portato alla vita"),
        ("evoluzione_specie.docx", "L'Evoluzione delle Specie", "Roberto Neri, Francesca Gialli", 2024, "Meccanismi evolutivi e selezione naturale"),
        ("cosmologia_moderna.pdf", "Cosmologia Moderna", "Stefano Blu", 2021, "Teorie attuali sulla struttura dell'universo"),
        ("antropologia_evolutiva.txt", "Antropologia Evolutiva", "Maria Rosa", 2023, "Evoluzione del genere umano"),
        ("homo_sapiens.docx", "L'Emergere di Homo Sapiens", "Luca Verdi, Anna Rossi", 2022, "Caratteristiche uniche della nostra specie")
    ]

    for category in categories:
        category_path = os.path.join(archive_dir, category)
        os.makedirs(category_path, exist_ok=True)

        # Create 2-3 files per category
        files_for_category = sample_files_data[:3] if "C01" in category else sample_files_data[3:]

        for file_name, title, authors, year, description in files_for_category:
            file_path = os.path.join(category_path, file_name)

            # Create file with rich content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"""Documento: {title}

Autori: {authors}
Anno di pubblicazione: {year}
Categoria: {category}

Descrizione:
{description}

Questo documento fa parte del percorso di conoscenza "Dall'Origine alla Complessità"
ed è stato catalogato nella sezione {category}.

Parole chiave: ricerca, scienza, conoscenza, complessità
""")

    print(f"✅ Created enhanced sample structure in '{archive_dir}' with {len(sample_files_data)} files")

def cleanup_sample_data():
    """Clean up the sample data."""
    archive_dir = "Dall_Origine_alla_Complessita"
    if os.path.exists(archive_dir):
        shutil.rmtree(archive_dir)
        print(f"🗑️ Cleaned up sample data '{archive_dir}'")

def run_enhanced_ui():
    """Run the enhanced Streamlit UI."""
    try:
        print("🚀 Starting Enhanced File Explorer UI...")
        print("📱 The app will open in your browser at: http://localhost:8501")
        print("🎯 Phase 3 Features Available:")
        print("  • File selection and AI details panel activation")
        print("  • Context menus with rename, delete, and AI actions")
        print("  • Visual selection indicators")
        print("  • Bulk operations for multiple files")
        print("  • Enhanced list and grid views")
        print()
        print("🔄 Press Ctrl+C to stop the app")

        # Run the Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "file_explorer_ui.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ], cwd=os.getcwd())

    except KeyboardInterrupt:
        print("\n🛑 Stopping Enhanced File Explorer UI...")
    except Exception as e:
        print(f"❌ Error running Enhanced UI: {e}")

def main():
    """Main function to test the enhanced file explorer UI."""
    print("🧪 Testing File Explorer UI - Phase 3 Features")
    print("=" * 60)
    print("🎯 Testing Enhanced Features:")
    print("  • File Selection & AI Details Activation")
    print("  • Context Menus (⋮) with Actions")
    print("  • Rename & Delete Operations")
    print("  • AI Action Placeholders")
    print("  • Visual Selection Indicators")
    print("  • Bulk Operations")
    print("=" * 60)

    # Create enhanced sample data
    create_enhanced_sample_data()

    try:
        # Run the enhanced UI
        run_enhanced_ui()

    finally:
        # Clean up
        cleanup_sample_data()
        print("✅ Phase 3 test completed and cleaned up")

if __name__ == "__main__":
    main()
