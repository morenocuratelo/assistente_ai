# Document Cache Management System

A comprehensive cache management system for resetting and cleaning all document-related caches in the assistente_ai application.

## Overview

This system provides centralized management for all cache systems used throughout the application for document processing and archiving:

- **Streamlit UI Caches** - Dashboard and UI component caches
- **Performance Optimizer Caches** - Advanced caching system for performance optimization
- **Search Engine Caches** - Document search results cache
- **Knowledge Graph Caches** - AI knowledge graph cache
- **File Processing Caches** - Processed document information cache
- **Model Caches** - AI model cache files
- **Vector Store Caches** - LlamaIndex VectorStore and ChromaDB document embeddings

## Quick Start

### Basic Usage

```python
from src.core.performance.cache_manager import clear_all_document_caches

# Clear all document caches
results = clear_all_document_caches(include_streamlit=True)
print(f"Cleared {sum(r.entries_cleared for r in results.values())} cache entries")
```

### Check Cache Status

```python
from src.core.performance.cache_manager import get_document_cache_status

status = get_document_cache_status()
print(f"Total cache entries: {status.total_entries}")

for system, info in status.cache_systems.items():
    if info.get('available') and 'entries' in info:
        print(f"{system}: {info['entries']} entries")
```

## API Reference

### Main Functions

#### `clear_all_document_caches(include_streamlit=True)`

Clears all document-related cache systems.

**Parameters:**
- `include_streamlit` (bool): Whether to include Streamlit UI caches

**Returns:**
- Dictionary mapping operation names to `CacheOperationResult` objects

**Example:**
```python
results = clear_all_document_caches(include_streamlit=True)

for operation, result in results.items():
    if result.success:
        print(f"✅ {operation}: {result.entries_cleared} entries cleared")
    else:
        print(f"❌ {operation}: {result.error_message}")
```

#### `get_document_cache_status()`

Returns comprehensive status information for all cache systems.

**Returns:**
- `CacheStatus` object with detailed information about each cache system

**Example:**
```python
status = get_document_cache_status()

print(f"📊 Cache Status Report")
print(f"Generated: {status.timestamp}")
print(f"Total entries: {status.total_entries}")

for system_name, system_info in status.cache_systems.items():
    print(f"\n🔍 {system_name.upper()}:")
    if 'error' in system_info:
        print(f"   ❌ Error: {system_info['error']}")
    elif system_info.get('available'):
        print(f"   ✅ Active - {system_info.get('entries', 0)} entries")
```

### Selective Cache Clearing

#### `clear_streamlit_document_caches()`

Clears only Streamlit UI caches.

#### `clear_performance_document_caches()`

Clears only performance optimizer caches.

#### `clear_search_document_caches()`

Clears only search engine caches.

#### `clear_knowledge_graph_document_caches()`

Clears only knowledge graph caches.

### Cache Operation History

#### `get_document_cache_history(limit=10)`

Returns recent cache operation history.

**Parameters:**
- `limit` (int): Maximum number of operations to return

**Returns:**
- List of `CacheOperationResult` objects

**Example:**
```python
history = get_document_cache_history(5)

for operation in history:
    print(f"{operation.timestamp}: {operation.operation}")
    print(f"  Success: {operation.success}")
    print(f"  Entries cleared: {operation.entries_cleared}")
    print(f"  Duration: {operation.execution_time_ms:.1f}ms")
```

## Command Line Interface

Use the provided example script for command-line cache management:

```bash
# Show cache status
python cache_management_example.py --status

# Clear all caches
python cache_management_example.py --all

# Clear only specific cache types
python cache_management_example.py --streamlit-only
python cache_management_example.py --performance-only
python cache_management_example.py --search-only
python cache_management_example.py --knowledge-graph-only

# Show operation history
python cache_management_example.py --history

# Dry run (show what would be cleared)
python cache_management_example.py --dry-run
```

## Data Structures

### CacheOperationResult

```python
@dataclass
class CacheOperationResult:
    operation: str           # Name of the operation performed
    success: bool           # Whether the operation succeeded
    entries_cleared: int    # Number of cache entries cleared
    error_message: Optional[str]  # Error message if operation failed
    execution_time_ms: float      # Execution time in milliseconds
    timestamp: datetime          # When the operation was performed
```

### CacheStatus

```python
@dataclass
class CacheStatus:
    timestamp: datetime                    # When status was generated
    cache_systems: Dict[str, Dict[str, Any]]  # Status of each cache system
    total_entries: int                     # Total entries across all systems
    last_cleanup: Optional[datetime]       # When last cleanup was performed
```

## Error Handling

The cache management system includes comprehensive error handling:

- **Graceful Degradation**: If one cache system fails, others continue to be processed
- **Detailed Logging**: All operations are logged with appropriate levels
- **Error Recovery**: Failed operations are recorded but don't prevent other operations
- **Operation History**: All operations (successful and failed) are tracked

## Performance Considerations

- **Atomic Operations**: Each cache system is cleared independently
- **Execution Time Tracking**: Performance metrics are recorded for each operation
- **Memory Efficient**: Large cache files are handled appropriately
- **Non-blocking**: Operations are designed to be fast and not block the application

## Integration Examples

### In Application Code

```python
from src.core.performance.cache_manager import get_document_cache_manager

# Get the cache manager instance
cache_manager = get_document_cache_manager()

# Clear all caches with custom options
results = cache_manager.clear_all_caches(include_streamlit=False)

# Check specific cache status
status = cache_manager.get_cache_status()
streamlit_status = status.cache_systems.get('streamlit', {})
```

### In Streamlit Apps

```python
import streamlit as st

# Add cache management buttons to your Streamlit app
if st.button("🧹 Clear Document Caches"):
    with st.spinner("Clearing caches..."):
        from src.core.performance.cache_manager import clear_all_document_caches

        results = clear_all_document_caches(include_streamlit=True)

        total_cleared = sum(r.entries_cleared for r in results.values())
        st.success(f"✅ Cleared {total_cleared} cache entries")

        # Refresh the app to ensure UI updates
        st.rerun()
```

### In Background Tasks

```python
from src.core.performance.cache_manager import clear_all_document_caches
import logging

def cleanup_caches_background():
    """Background task to clean up caches."""
    try:
        logger = logging.getLogger(__name__)
        logger.info("Starting background cache cleanup")

        results = clear_all_document_caches(include_streamlit=False)

        total_cleared = sum(r.entries_cleared for r in results.values())
        logger.info(f"Background cache cleanup completed: {total_cleared} entries cleared")

        return True

    except Exception as e:
        logger.error(f"Background cache cleanup failed: {e}")
        return False
```

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure write permissions for cache directories
2. **Import Errors**: Verify all required modules are installed
3. **Memory Issues**: Large cache files are handled gracefully
4. **Service Unavailable**: Some cache systems may not be available in all environments

### Debugging

Enable debug logging to troubleshoot issues:

```python
import logging

# Enable debug logging for cache operations
logging.getLogger('src.core.performance.cache_manager').setLevel(logging.DEBUG)

# Then run cache operations as normal
```

## Best Practices

1. **Regular Cleanup**: Schedule regular cache cleanup to prevent accumulation
2. **Monitor Performance**: Use the operation history to track cleanup performance
3. **Selective Clearing**: Use selective clearing for targeted maintenance
4. **Error Handling**: Always handle exceptions when integrating cache management
5. **User Feedback**: Provide user feedback during long-running operations

## Contributing

When adding new cache systems to the application:

1. Add the cache clearing logic to `DocumentCacheManager`
2. Update the status checking in `get_cache_status()`
3. Add appropriate error handling and logging
4. Update this documentation
5. Test thoroughly with the example script

## License

This cache management system is part of the assistente_ai project.
