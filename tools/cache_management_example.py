#!/usr/bin/env python3
"""
Example usage of the Document Cache Management System

This script demonstrates how to use the comprehensive cache management system
to reset and clean all document-related caches in the application.

Usage:
    python cache_management_example.py [options]

Options:
    --all                    Clear all caches (default)
    --streamlit-only        Clear only Streamlit UI caches
    --performance-only      Clear only performance optimizer caches
    --search-only          Clear only search engine caches
    --knowledge-graph-only Clear only knowledge graph caches
    --status               Show cache status without clearing
    --dry-run              Show what would be cleared without actually doing it

Author: Cline
Created: 2025
"""

import sys
import argparse
from typing import Dict, Any

# Import the cache management system
from src.core.performance.cache_manager import (
    clear_all_document_caches,
    clear_streamlit_document_caches,
    clear_performance_document_caches,
    clear_search_document_caches,
    clear_knowledge_graph_document_caches,
    clear_vector_store_document_caches,
    get_document_cache_status,
    get_document_cache_history,
    CacheOperationResult,
    CacheStatus
)


def print_cache_status(status: CacheStatus) -> None:
    """Print comprehensive cache status."""
    print("\n📊 Document Cache Status Report")
    print(f"Generated at: {status.timestamp}")
    print(f"Total cache entries across all systems: {status.total_entries}")
    print()

    for system_name, system_info in status.cache_systems.items():
        print(f"🔍 {system_name.upper()}:")

        if 'error' in system_info:
            print(f"   ❌ Error: {system_info['error']}")
        elif system_info.get('available', False):
            if 'entries' in system_info:
                print(f"   ✅ Active - {system_info['entries']} entries")
            else:
                print("   ✅ Active")
        else:
            print("   ⚠️  Not available")

        # Print additional details for specific systems
        if system_name == 'performance_optimizer' and 'stats' in system_info:
            stats = system_info['stats']
            print(f"   📈 Stats: {stats.get('valid_entries', 0)} valid, {stats.get('expired_entries', 0)} expired")

        if system_name == 'file_processing' and 'file_path' in system_info:
            print(f"   📁 Cache file: {system_info['file_path']}")

        if system_name == 'model_cache' and 'directory' in system_info:
            print(f"   🤖 Cache directory: {system_info['directory']}")

        print()


def print_operation_results(results: Dict[str, CacheOperationResult]) -> None:
    """Print the results of cache clearing operations."""
    print("\n🧹 Cache Clearing Results")
    print("=" * 50)

    total_cleared = 0
    total_time = 0.0

    for operation_name, result in results.items():
        status_icon = "✅" if result.success else "❌"
        print(f"{status_icon} {operation_name}:")

        if result.success:
            print(f"   Cleared {result.entries_cleared} entries in {result.execution_time_ms:.1f}s")
            total_cleared += result.entries_cleared
            total_time += result.execution_time_ms
        else:
            print(f"   Failed: {result.error_message}")

        print()

    print(f"📊 Summary: {total_cleared} total entries cleared in {total_time:.1f}s")


def show_cache_history(limit: int = 5) -> None:
    """Show recent cache operation history."""
    print(f"\n📜 Recent Cache Operations (last {limit})")
    print("=" * 50)

    try:
        history = get_document_cache_history(limit)
        if not history:
            print("No cache operations in history")
            return

        for i, operation in enumerate(history, 1):
            status_icon = "✅" if operation.success else "❌"
            print(f"{i}. {status_icon} {operation.operation}")
            print(f"   Time: {operation.timestamp}")
            print(f"   Duration: {operation.execution_time_ms:.1f}s")
            if operation.entries_cleared > 0:
                print(f"   Entries cleared: {operation.entries_cleared}")
            if operation.error_message:
                print(f"   Error: {operation.error_message}")
            print()

    except Exception as e:
        print(f"Error retrieving cache history: {e}")


def main():
    """Main function to demonstrate cache management."""
    parser = argparse.ArgumentParser(description="Document Cache Management Example")
    parser.add_argument('--all', action='store_true', default=True,
                       help='Clear all caches (default)')
    parser.add_argument('--streamlit-only', action='store_true',
                       help='Clear only Streamlit UI caches')
    parser.add_argument('--performance-only', action='store_true',
                       help='Clear only performance optimizer caches')
    parser.add_argument('--search-only', action='store_true',
                       help='Clear only search engine caches')
    parser.add_argument('--knowledge-graph-only', action='store_true',
                       help='Clear only knowledge graph caches')
    parser.add_argument('--vector-store-only', action='store_true',
                       help='Clear only vector store caches (LlamaIndex + ChromaDB)')
    parser.add_argument('--status', action='store_true',
                       help='Show cache status without clearing')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be cleared without actually doing it')
    parser.add_argument('--history', action='store_true',
                       help='Show cache operation history')

    args = parser.parse_args()

    try:
        # Show current cache status
        print("🔍 Checking current cache status...")
        status = get_document_cache_status()
        print_cache_status(status)

        # Handle different operation modes
        if args.status:
            print("ℹ️  Status mode - no caches will be cleared")
            return

        if args.history:
            show_cache_history()
            return

        if args.dry_run:
            print("🔍 DRY RUN - No actual cache clearing will be performed")
            print("This would clear the following caches:")
            if args.all or (args.streamlit_only or args.performance_only or args.search_only or args.knowledge_graph_only or args.vector_store_only):
                print("  • Streamlit UI caches" if args.streamlit_only or args.all else "")
                print("  • Performance optimizer caches" if args.performance_only or args.all else "")
                print("  • Search engine caches" if args.search_only or args.all else "")
                print("  • Knowledge graph caches" if args.knowledge_graph_only or args.all else "")
                print("  • Vector store caches (LlamaIndex + ChromaDB)" if args.vector_store_only or args.all else "")
            return

        # Perform cache clearing based on arguments
        print("🧹 Starting cache cleanup...")

        if args.streamlit_only:
            print("Clearing only Streamlit caches...")
            result = clear_streamlit_document_caches()
            print(f"✅ Streamlit caches cleared: {result.entries_cleared} entries in {result.execution_time_ms:.1f}s")

        elif args.performance_only:
            print("Clearing only performance optimizer caches...")
            result = clear_performance_document_caches()
            print(f"✅ Performance caches cleared: {result.entries_cleared} entries in {result.execution_time_ms:.1f}s")

        elif args.search_only:
            print("Clearing only search engine caches...")
            result = clear_search_document_caches()
            print(f"✅ Search caches cleared: {result.entries_cleared} entries in {result.execution_time_ms:.1f}s")

        elif args.knowledge_graph_only:
            print("Clearing only knowledge graph caches...")
            result = clear_knowledge_graph_document_caches()
            print(f"✅ Knowledge graph caches cleared: {result.entries_cleared} entries in {result.execution_time_ms:.1f}s")

        elif args.vector_store_only:
            print("Clearing only vector store caches...")
            result = clear_vector_store_document_caches()
            print(f"✅ Vector store caches cleared: {result.entries_cleared} entries in {result.execution_time_ms:.1f}s")

        else:  # args.all or default
            print("Clearing all document caches...")
            results = clear_all_document_caches(include_streamlit=True)
            print_operation_results(results)

        # Show updated status
        print("\n📊 Updated cache status after cleanup:")
        updated_status = get_document_cache_status()
        print_cache_status(updated_status)

        # Show operation history
        show_cache_history(3)

        print("\n✅ Cache management operation completed successfully!")

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during cache management: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
