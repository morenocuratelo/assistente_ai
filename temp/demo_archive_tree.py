#!/usr/bin/env python3
"""
Demo script showing how the get_archive_tree() function works.
This creates a sample directory structure and demonstrates the function's capabilities.
"""

import sys
import os
import json
import shutil
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from file_utils import get_archive_tree, setup_database

def create_sample_structure():
    """Create a sample directory structure for demonstration."""
    print("🏗️ Creating sample directory structure...")

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

    for category in categories:
        category_path = os.path.join(archive_dir, category)
        os.makedirs(category_path, exist_ok=True)

        # Create some sample files
        sample_files = [
            "documento_universo.pdf",
            "origine_vita.txt",
            "evoluzione_specie.docx"
        ]

        for file_name in sample_files[:2]:  # Create 2 files per category
            file_path = os.path.join(category_path, file_name)

            # Create empty file with some content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Contenuto di esempio per {file_name}\nCategoria: {category}\n")

    print(f"✅ Created sample structure in '{archive_dir}'")

def cleanup_sample_structure():
    """Clean up the sample directory structure."""
    archive_dir = "Dall_Origine_alla_Complessita"
    if os.path.exists(archive_dir):
        shutil.rmtree(archive_dir)
        print(f"🗑️ Cleaned up sample structure '{archive_dir}'")

def demo_archive_tree():
    """Demonstrate the get_archive_tree function."""
    print("🎯 Demonstrating get_archive_tree() function...")
    print("=" * 60)

    # Create sample structure
    create_sample_structure()

    try:
        # Ensure database is set up
        setup_database()

        # Get the archive tree
        archive_tree = get_archive_tree()

        # Display results
        if not archive_tree:
            print("❌ Archive tree is still empty after creating sample structure.")
            return

        print("✅ Archive tree generated successfully!")
        print(f"📊 Tree contains {len(archive_tree)} top-level parts")
        print()

        # Display the tree structure
        def print_tree(node, prefix="", level=0):
            """Recursively print the tree structure."""
            if level > 4:  # Allow deeper display for demo
                print(f"{prefix}... (truncated)")
                return

            for key, value in node.items():
                if isinstance(value, dict):
                    node_type = value.get('type', 'unknown')
                    name = value.get('name', key)

                    if node_type == 'part':
                        print(f"{prefix}📂 PART: {name}")
                    elif node_type == 'chapter':
                        print(f"{prefix}📁 CHAPTER: {name}")
                    else:
                        print(f"{prefix}📂 {key}")

                    # Print files if present
                    if 'files' in value and value['files']:
                        for file_obj in value['files']:
                            status_icon = "✅" if file_obj['status'] == 'indexed' else "❓"
                            size_mb = file_obj['size'] / (1024 * 1024)
                            print(f"{prefix}  {status_icon} {file_obj['name']} ({file_obj['extension']}) - {size_mb:.2f}MB")
                            if file_obj['status'] == 'indexed':
                                print(f"{prefix}    📖 Title: {file_obj['title']}")
                                if file_obj['authors']:
                                    print(f"{prefix}    👥 Authors: {file_obj['authors']}")
                                if file_obj['publication_year']:
                                    print(f"{prefix}    📅 Year: {file_obj['publication_year']}")

                    # Recurse into children
                    if 'children' in value and value['children']:
                        print_tree(value['children'], prefix + "  ", level + 1)

        print("🌳 Archive Tree Structure:")
        print("=" * 40)
        print_tree(archive_tree)

        # Display statistics
        print("\n📈 Statistics:")
        print("=" * 40)

        total_files = 0
        indexed_files = 0
        unindexed_files = 0
        total_size = 0

        def analyze_files(node):
            nonlocal total_files, indexed_files, unindexed_files, total_size
            if isinstance(node, dict):
                for key, value in node.items():
                    if isinstance(value, dict):
                        if 'files' in value:
                            for file_obj in value['files']:
                                total_files += 1
                                total_size += file_obj['size']
                                if file_obj['status'] == 'indexed':
                                    indexed_files += 1
                                else:
                                    unindexed_files += 1
                        if 'children' in value:
                            analyze_files(value['children'])

        analyze_files(archive_tree)

        print(f"Total files found: {total_files}")
        print(f"Indexed files: {indexed_files}")
        print(f"Unindexed files: {unindexed_files}")
        print(f"Total size: {total_size / (1024 * 1024):.2f} MB")

        if total_files > 0:
            index_rate = (indexed_files / total_files) * 100
            print(f"Indexing rate: {index_rate:.1f}%")

        # Show sample file structure
        print("\n🔍 Sample File Object Structure:")
        print("=" * 40)

        def find_sample_file(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    if isinstance(value, dict) and 'files' in value and value['files']:
                        return value['files'][0]
                    result = find_sample_file(value)
                    if result:
                        return result
            return None

        sample_file = find_sample_file(archive_tree)
        if sample_file:
            # Show relevant fields only
            display_fields = [
                'name', 'path', 'type', 'size', 'extension',
                'title', 'authors', 'publication_year', 'category_id',
                'status', 'modified_time'
            ]

            sample_display = {k: v for k, v in sample_file.items() if k in display_fields}
            print(json.dumps(sample_display, indent=2, ensure_ascii=False, default=str))
        else:
            print("No sample file found.")

        print("\n🎉 Demo completed successfully!")
        print("\n💡 Key Features Demonstrated:")
        print("  • Hierarchical tree structure with Parts and Chapters")
        print("  • File metadata integration from database")
        print("  • File system information (size, modification time)")
        print("  • Processing status indicators")
        print("  • Graceful handling of missing metadata")
        print("  • Comprehensive error handling")

    finally:
        # Clean up sample structure
        cleanup_sample_structure()

if __name__ == "__main__":
    demo_archive_tree()
