from archivista_processing import process_document_task
import traceback
p = 'documenti_da_processare/Conflict Altruism’s midwife.pdf'
try:
    print('Calling process_document_task... this may take a while')
    r = process_document_task(p)
    print('Result:', r)
except Exception as e:
    print('EXCEPTION:', type(e).__name__, e)
    traceback.print_exc()
