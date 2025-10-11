# Context Manager - Gestore contesto applicazione
"""
Context manager per operazioni sicure e gestione stato.

Fornisce:
- Gestione operazioni con contesto
- Rollback automatico in caso errori
- Logging operazioni strutturato
- Monitoraggio performance operazioni
"""

import logging
import time
from typing import Dict, Any, Optional, Callable, List
from contextlib import contextmanager
from datetime import datetime
from .execution_context import ExecutionContext

logger = logging.getLogger('ContextManager')

class OperationResult:
    """Risultato operazione con metadati"""

    def __init__(self, success: bool, data: Any = None, error: str = None,
                 duration: float = 0.0, metadata: Dict[str, Any] = None):
        self.success = success
        self.data = data
        self.error = error
        self.duration = duration
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Converte risultato a dizionario"""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'duration': self.duration,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }

class ContextManager:
    """
    Gestore contesto per operazioni sicure.

    Fornisce operazioni con gestione errori,
    rollback automatico e monitoring.
    """

    def __init__(self):
        """Inizializza context manager"""
        self.operation_history: List[OperationResult] = []
        self.max_history_size = 1000

        logger.info("ContextManager inizializzato")

    def execute_with_context(self, operation_name: str,
                           operation_func: Callable,
                           context: ExecutionContext = None,
                           rollback_func: Callable = None,
                           *args, **kwargs) -> OperationResult:
        """
        Esegue operazione con gestione contesto completa.

        Args:
            operation_name: Nome operazione per logging
            operation_func: Funzione da eseguire
            context: Contesto esecuzione
            rollback_func: Funzione rollback in caso errore
            *args, **kwargs: Argomenti operazione

        Returns:
            OperationResult con esito operazione
        """
        start_time = time.time()
        metadata = {
            'operation_name': operation_name,
            'start_time': datetime.now().isoformat(),
            'context_available': context is not None
        }

        try:
            # Log inizio operazione
            logger.debug(f"Inizio operazione: {operation_name}")

            # Esegui operazione
            if context:
                result = context.execute_in_context(operation_name, operation_func, *args, **kwargs)
            else:
                result = operation_func(*args, **kwargs)

            # Calcola durata
            duration = time.time() - start_time

            # Crea risultato successo
            operation_result = OperationResult(
                success=True,
                data=result,
                duration=duration,
                metadata=metadata
            )

            # Log successo
            logger.debug(f"Operazione completata: {operation_name} ({duration:.3f}s)")

            # Aggiungi a history
            self._add_to_history(operation_result)

            return operation_result

        except Exception as e:
            # Calcola durata anche in caso errore
            duration = time.time() - start_time

            # Log errore
            logger.error(f"Errore operazione {operation_name}: {e}")

            # Crea risultato errore
            operation_result = OperationResult(
                success=False,
                error=str(e),
                duration=duration,
                metadata=metadata
            )

            # Esegui rollback se disponibile
            if rollback_func:
                try:
                    logger.info(f"Eseguo rollback per operazione: {operation_name}")
                    rollback_func(e)
                except Exception as rollback_error:
                    logger.error(f"Errore rollback operazione {operation_name}: {rollback_error}")

            # Aggiungi a history
            self._add_to_history(operation_result)

            return operation_result

    @contextmanager
    def operation_context(self, operation_name: str, context: ExecutionContext = None):
        """
        Context manager per operazioni con gestione errori.

        Args:
            operation_name: Nome operazione
            context: Contesto esecuzione

        Yields:
            OperationResult parziale per operazione in corso
        """
        start_time = time.time()
        metadata = {
            'operation_name': operation_name,
            'start_time': datetime.now().isoformat(),
            'context_available': context is not None
        }

        # Crea risultato parziale
        partial_result = OperationResult(
            success=False,  # Sarà aggiornato al termine
            duration=0.0,
            metadata=metadata
        )

        try:
            logger.debug(f"Inizio operazione context: {operation_name}")
            yield partial_result

            # Operazione completata con successo
            duration = time.time() - start_time
            partial_result.success = True
            partial_result.duration = duration

            logger.debug(f"Operazione context completata: {operation_name} ({duration:.3f}s)")

        except Exception as e:
            # Operazione fallita
            duration = time.time() - start_time
            partial_result.success = False
            partial_result.error = str(e)
            partial_result.duration = duration

            logger.error(f"Errore operazione context {operation_name}: {e}")
            raise

        finally:
            # Aggiungi sempre a history
            self._add_to_history(partial_result)

    def get_operation_stats(self) -> Dict[str, Any]:
        """
        Statistiche operazioni eseguite.

        Returns:
            Dizionario statistiche operazioni
        """
        if not self.operation_history:
            return {
                'total_operations': 0,
                'success_rate': 0.0,
                'avg_duration': 0.0,
                'recent_operations': []
            }

        # Calcola statistiche
        total_ops = len(self.operation_history)
        successful_ops = len([op for op in self.operation_history if op.success])
        success_rate = (successful_ops / total_ops) * 100

        # Durata media operazioni successful
        successful_durations = [op.duration for op in self.operation_history if op.success]
        avg_duration = sum(successful_durations) / len(successful_durations) if successful_durations else 0.0

        # Operazioni recenti
        recent_ops = self.operation_history[-10:]  # Ultime 10

        return {
            'total_operations': total_ops,
            'successful_operations': successful_ops,
            'failed_operations': total_ops - successful_ops,
            'success_rate': round(success_rate, 2),
            'avg_duration': round(avg_duration, 3),
            'recent_operations': [op.to_dict() for op in recent_ops]
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Report performance operazioni.

        Returns:
            Dizionario report performance
        """
        stats = self.get_operation_stats()

        # Analisi performance per tipo operazione
        operation_types = {}
        for op in self.operation_history:
            op_name = op.metadata.get('operation_name', 'unknown')
            if op_name not in operation_types:
                operation_types[op_name] = {
                    'count': 0,
                    'total_duration': 0.0,
                    'success_count': 0,
                    'error_count': 0
                }

            operation_types[op_name]['count'] += 1
            operation_types[op_name]['total_duration'] += op.duration

            if op.success:
                operation_types[op_name]['success_count'] += 1
            else:
                operation_types[op_name]['error_count'] += 1

        # Calcola medie per tipo
        for op_type in operation_types:
            data = operation_types[op_type]
            data['avg_duration'] = data['total_duration'] / data['count']
            data['success_rate'] = (data['success_count'] / data['count']) * 100

        return {
            'summary': stats,
            'by_operation_type': operation_types,
            'slowest_operations': self._get_slowest_operations(5),
            'most_error_prone': self._get_most_error_prone_operations(5)
        }

    def _get_slowest_operations(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Restituisce operazioni più lente"""
        sorted_ops = sorted(
            self.operation_history,
            key=lambda x: x.duration,
            reverse=True
        )
        return [op.to_dict() for op in sorted_ops[:limit]]

    def _get_most_error_prone_operations(self, limit: int = 5) -> List[str]:
        """Restituisce operazioni con più errori"""
        operation_errors = {}
        for op in self.operation_history:
            if not op.success:
                op_name = op.metadata.get('operation_name', 'unknown')
                operation_errors[op_name] = operation_errors.get(op_name, 0) + 1

        # Ordina per numero errori
        sorted_errors = sorted(
            operation_errors.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [op_name for op_name, _ in sorted_errors[:limit]]

    def _add_to_history(self, operation_result: OperationResult):
        """Aggiunge operazione a history con gestione dimensione"""
        self.operation_history.append(operation_result)

        # Mantieni dimensione massima
        if len(self.operation_history) > self.max_history_size:
            # Rimuovi operazioni più vecchie
            self.operation_history = self.operation_history[-self.max_history_size:]

    def clear_history(self):
        """Pulisce history operazioni"""
        self.operation_history.clear()
        logger.info("History operazioni pulita")

    def get_context_info(self) -> Dict[str, Any]:
        """
        Informazioni contesto manager.

        Returns:
            Dizionario informazioni contesto
        """
        return {
            'history_size': len(self.operation_history),
            'max_history_size': self.max_history_size,
            'stats': self.get_operation_stats(),
            'performance_report': self.get_performance_report()
        }

    def export_history(self, format: str = 'json') -> str:
        """
        Esporta history operazioni.

        Args:
            format: Formato esportazione ('json', 'csv')

        Returns:
            History in formato richiesto
        """
        if format.lower() == 'json':
            operations_data = [op.to_dict() for op in self.operation_history]
            import json
            return json.dumps(operations_data, indent=2, default=str)

        elif format.lower() == 'csv':
            if not self.operation_history:
                return "No operations recorded"

            # Header CSV
            csv_lines = ["timestamp,operation_name,success,duration,error"]

            # Dati operazioni
            for op in self.operation_history:
                op_name = op.metadata.get('operation_name', 'unknown')
                csv_line = f"{op.timestamp},{op_name},{op.success},{op.duration},{op.error or ''}"
                csv_lines.append(csv_line)

            return "\n".join(csv_lines)

        else:
            raise ValueError(f"Formato non supportato: {format}")

    def get_error_analysis(self) -> Dict[str, Any]:
        """
        Analisi errori operazioni.

        Returns:
            Dizionario analisi errori
        """
        if not self.operation_history:
            return {'total_errors': 0, 'error_types': {}, 'error_patterns': []}

        # Analisi errori
        error_operations = [op for op in self.operation_history if not op.success]

        if not error_operations:
            return {'total_errors': 0, 'error_types': {}, 'error_patterns': []}

        # Tipi errore
        error_types = {}
        for op in error_operations:
            error_msg = op.error or 'Unknown error'
            error_type = error_msg.split(':')[0] if ':' in error_msg else 'Generic error'
            error_types[error_type] = error_types.get(error_type, 0) + 1

        # Pattern errori (operazioni che falliscono spesso)
        operation_failures = {}
        for op in error_operations:
            op_name = op.metadata.get('operation_name', 'unknown')
            operation_failures[op_name] = operation_failures.get(op_name, 0) + 1

        # Trova pattern
        error_patterns = []
        for op_name, failure_count in operation_failures.items():
            if failure_count > 1:  # Operazioni fallite più volte
                error_patterns.append({
                    'operation': op_name,
                    'failure_count': failure_count,
                    'recent_failures': failure_count >= 3
                })

        return {
            'total_errors': len(error_operations),
            'error_rate': round((len(error_operations) / len(self.operation_history)) * 100, 2),
            'error_types': error_types,
            'error_patterns': sorted(error_patterns, key=lambda x: x['failure_count'], reverse=True)
        }
