#!/usr/bin/env python3
"""
Test script for the New Navigation Architecture.
Tests the complete sidebar-based navigation system with toggle functionality.
"""

import sys
import os
import shutil
import subprocess

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_architecture_test_data():
    """Create test data for the new architecture."""
    print("🏗️ Creating test data for new architecture...")

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

    # Rich sample files
    sample_files_data = [
        ("cosmologia_moderna.pdf", "La Cosmologia Moderna", "Marco Rossi, Giulia Bianchi", 2023, "Studio completo sulla cosmologia contemporanea"),
        ("origine_vita.txt", "L'Origine Biochimica della Vita", "Alessandra Verdi", 2022, "Analisi dei processi chimici prebiotici"),
        ("evoluzione_specie.docx", "L'Evoluzione delle Specie", "Roberto Neri, Francesca Gialli", 2024, "Meccanismi evolutivi e selezione naturale"),
        ("universo_olografico.pdf", "L'Universo come Ologramma", "Stefano Blu", 2021, "Teoria olografica dell'universo"),
        ("antropologia_evolutiva.txt", "Antropologia Evolutiva", "Maria Rosa", 2023, "Rapporto tra biologia e cultura umana"),
        ("homo_sapiens.docx", "Il Futuro di Homo Sapiens", "Luca Verdi, Anna Rossi", 2022, "Prospettive evolutive della nostra specie")
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
                f.write(f"""Documento di Ricerca: {title}

Autori: {authors}
Anno di Pubblicazione: {year}
Categoria: {category}

Riassunto Esecutivo:
{description}

Contenuto del Documento:
Questo documento rappresenta un contributo significativo al campo della ricerca scientifica nel percorso di conoscenza "Dall'Origine alla Complessità". La ricerca si concentra su aspetti fondamentali dell'evoluzione cosmica e biologica, fornendo nuove prospettive teoriche e sperimentali.

Metodologia di Ricerca:
- Analisi teorica dei modelli cosmologici
- Studio empirico dei processi evolutivi
- Integrazione di dati multidisciplinari
- Validazione sperimentale delle ipotesi

Risultati e Conclusioni:
I risultati suggeriscono nuove direzioni per la ricerca futura e aprono interessanti quesiti sul rapporto tra complessità biologica e cosmologica. Le implicazioni di questa ricerca si estendono a multiple discipline scientifiche.

Parole Chiave: cosmologia, evoluzione, complessità, ricerca scientifica, metodologia
""")

    print(f"✅ Created test data in '{archive_dir}' with {len(sample_files_data)} files")

def cleanup_test_data():
    """Clean up the test data."""
    archive_dir = "Dall_Origine_alla_Complessita"
    if os.path.exists(archive_dir):
        shutil.rmtree(archive_dir)
        print(f"🗑️ Cleaned up test data '{archive_dir}'")

def run_architecture_test():
    """Run the new architecture test."""
    try:
        print("🚀 Starting New Architecture Test...")
        print("📱 The app will open in your browser at: http://localhost:8501")
        print()
        print("🎯 New Architecture Features:")
        print("  • Modern sidebar-based navigation")
        print("  • Toggle between Chat View and File Explorer")
        print("  • Chat-optimized document selection")
        print("  • Full-width dashboard")
        print("  • Context preservation between views")
        print("  • Simplified, focused interfaces")
        print()
        print("🔄 Press Ctrl+C to stop the app")

        # Run the new architecture app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "main_new_architecture.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ], cwd=os.getcwd())

    except KeyboardInterrupt:
        print("\n🛑 Stopping New Architecture Test...")
    except Exception as e:
        print(f"❌ Error running architecture test: {e}")

def main():
    """Main function to test the new architecture."""
    print("🧪 New Navigation Architecture Test")
    print("=" * 60)
    print("🎯 Testing New Architecture:")
    print("  • Sidebar Navigation (💬 Chat, 🗂️ Archive, 📊 Dashboard)")
    print("  • Chat View: Optimized for document selection")
    print("  • Archive View: Toggle between Chat View and File Explorer")
    print("  • Dashboard View: Full-width statistics")
    print("  • Context Integration: Seamless switching")
    print("  • Modern UX: Clean, focused interfaces")
    print("=" * 60)

    # Create test data
    create_architecture_test_data()

    try:
        # Run the architecture test
        run_architecture_test()

    finally:
        # Clean up
        cleanup_test_data()
        print("✅ Architecture test completed and cleaned up")

if __name__ == "__main__":
    main()
