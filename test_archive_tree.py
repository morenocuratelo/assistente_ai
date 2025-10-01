#!/usr/bin/env python3
"""
Test script for the get_archive_tree() function.
This script tests the archive tree generation and displays the results.
"""

import sys
import os
import json

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from file_utils import get_archive_tree, setup_database

def test_archive_tree():
    """Test the get_archive_tree function and display results."""
    print("🧪 Testing get_archive_tree() function...")
    print("=" * 50)

    # Ensure database is set up
    setup_database()

    # Get the archive tree
    archive_tree = get_archive_tree()

    # Display results
    if not archive_tree:
        print("⚠️ Archive tree is empty. This could mean:")
        print("  - The 'Dall_Origine_alla_Complessita' directory doesn't exist")
        print("  - No files are present in the archive")
        print("  - An error occurred during tree generation")
        return

    print(f"✅ Archive tree generated successfully!")
    print(f"📊 Tree contains {len(archive_tree)} top-level parts")
    print()

    # Display the tree structure
    def print_tree(node, prefix="", level=0):
        """Recursively print the tree structure."""
        if level > 3:  # Limit depth for readability
            print(f"{prefix}... (truncated)")
            return

        for key, value in node.items():
            if isinstance(value, dict):
                node_type = value.get('type', 'unknown')
                name = value.get('name', key)

                if node_type == 'part':
                    print(f"{prefix}📂 {key}: {name}")
                elif node_type == 'chapter':
                    print(f"{prefix}📁 {key}: {name}")
                else:
                    print(f"{prefix}📂 {key}")

                # Print files if present
                if 'files' in value and value['files']:
                    for file_obj in value['files'][:3]:  # Show first 3 files
                        status_icon = "✅" if file_obj['status'] == 'indexed' else "❓"
                        print(f"{prefix}  {status_icon} {file_obj['name']} ({file_obj['extension']})")
                    if len(value['files']) > 3:
                        print(f"{prefix}  ... and {len(value['files']) - 3} more files")

                # Recurse into children
                if 'children' in value and value['children']:
                    print_tree(value['children'], prefix + "  ", level + 1)

    print("🌳 Archive Tree Structure:")
    print("=" * 30)
    print_tree(archive_tree)

    # Display statistics
    print("\n📈 Statistics:")
    print("=" * 30)

    total_files = 0
    indexed_files = 0
    unindexed_files = 0

    def count_files(node):
        nonlocal total_files, indexed_files, unindexed_files
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, dict):
                    if 'files' in value:
                        for file_obj in value['files']:
                            total_files += 1
                            if file_obj['status'] == 'indexed':
                                indexed_files += 1
                            else:
                                unindexed_files += 1
                    if 'children' in value:
                        count_files(value['children'])

    count_files(archive_tree)

    print(f"Total files found: {total_files}")
    print(f"Indexed files: {indexed_files}")
    print(f"Unindexed files: {unindexed_files}")

    if total_files > 0:
        index_rate = (indexed_files / total_files) * 100
        print(f"Indexing rate: {index_rate:.1f}%")

    # Test with a sample file object
    print("\n🔍 Sample File Object:")
    print("=" * 30)

    def find_sample_file(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, dict) and 'files' in value and value['files']:
                    return value['files'][0]  # Return first file found
                result = find_sample_file(value)
                if result:
                    return result
        return None

    sample_file = find_sample_file(archive_tree)
    if sample_file:
        print(json.dumps(sample_file, indent=2, ensure_ascii=False))
    else:
        print("No sample file found to display structure.")

if __name__ == "__main__":
    test_archive_tree()
