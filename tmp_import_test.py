import sys
try:
    import importlib
    m = importlib.import_module('archivista_processing')
    print('import archivista_processing: OK')
    print('has ensure_storage_files_exist:', hasattr(m, 'ensure_storage_files_exist'))
except Exception as e:
    print('IMPORT ERROR:', type(e).__name__, e)
    sys.exit(1)
