#!/usr/bin/env python3
"""
Test script for Complete Integration - Toggle-based File Explorer in Main App.
Tests the full integration with both Chat View and File Explorer modes.
"""

import sys
import os
import shutil
import subprocess

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_integration_test_data():
    """Create comprehensive test data for integration testing."""
    print("🏗️ Creating integration test data...")

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

    # Rich sample files with diverse content
    sample_files_data = [
        ("cosmologia_quantistica.pdf", "La Cosmologia Quantistica", "Marco Rossi, Giulia Bianchi", 2023, "Studio avanzato sulla cosmologia quantistica e teoria delle stringhe"),
        ("origine_vita.txt", "L'Origine Biochimica della Vita", "Alessandra Verdi", 2022, "Analisi dei processi chimici prebiotici"),
        ("evoluzione_umana.docx", "L'Evoluzione del Genere Homo", "Roberto Neri, Francesca Gialli", 2024, "Studio completo sull'evoluzione umana"),
        ("universo_olografico.pdf", "L'Universo come Ologramma", "Stefano Blu", 2021, "Teoria olografica dell'universo"),
        ("antropologia_culturale.txt", "Antropologia e Cultura", "Maria Rosa", 2023, "Rapporto tra biologia e cultura umana"),
        ("homo_sapiens_futuro.docx", "Il Futuro di Homo Sapiens", "Luca Verdi, Anna Rossi", 2022, "Prospettive evolutive della nostra specie")
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

Riassunto:
{description}

Contenuto del Documento:
Questo documento rappresenta un contributo significativo al campo della ricerca scientifica nel percorso di conoscenza "Dall'Origine alla Complessità". La ricerca si concentra su aspetti fondamentali dell'evoluzione cosmica e biologica, fornendo nuove prospettive teoriche e sperimentali.

Metodologia:
- Analisi teorica dei modelli cosmologici
- Studio empirico dei processi evolutivi
- Integrazione di dati multidisciplinari

Conclusioni:
I risultati suggeriscono nuove direzioni per la ricerca futura e aprono interessanti quesiti sul rapporto tra complessità biologica e cosmologica.

Parole Chiave: cosmologia, evoluzione, complessità, ricerca scientifica
""")

    print(f"✅ Created integration test data in '{archive_dir}' with {len(sample_files_data)} files")

def cleanup_test_data():
    """Clean up the test data."""
    archive_dir = "Dall_Origine_alla_Complessita"
    if os.path.exists(archive_dir):
        shutil.rmtree(archive_dir)
        print(f"🗑️ Cleaned up test data '{archive_dir}'")

def run_integration_test():
    """Run the complete integration test."""
    try:
        print("🚀 Starting Complete Integration Test...")
        print("📱 The main app will open in your browser at: http://localhost:8501")
        print()
        print("🎯 Integration Features Available:")
        print("  • Toggle between Chat View and File Explorer")
        print("  • Chat-focused document selection with cards")
        print("  • Full three-column File Explorer interface")
        print("  • Context integration between views")
        print("  • Enhanced search and filtering")
        print("  • Quick preview modals")
        print("  • Session state preservation")
        print()
        print("🔄 Press Ctrl+C to stop the app")

        # Run the main Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "main.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ], cwd=os.getcwd())

    except KeyboardInterrupt:
        print("\n🛑 Stopping Integration Test...")
    except Exception as e:
        print(f"❌ Error running integration test: {e}")

def main():
    """Main function to test the complete integration."""
    print("🧪 Complete Integration Test - Toggle-based File Explorer")
    print("=" * 70)
    print("🎯 Testing Complete Integration:")
    print("  • Archive Tab with Toggle Interface")
    print("  • Chat View: Document selection for chat context")
    print("  • File Explorer: Full file management interface")
    print("  • Context preservation between views")
    print("  • Enhanced chat integration")
    print("  • Session state management")
    print("=" * 70)

    # Create test data
    create_integration_test_data()

    try:
        # Run the integration test
        run_integration_test()

    finally:
        # Clean up
        cleanup_test_data()
        print("✅ Integration test completed and cleaned up")

if __name__ == "__main__":
    main()
