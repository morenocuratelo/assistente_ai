"""
Service Manager esistente.

Gestisce i servizi legacy del sistema.
"""

from typing import Dict, Any, Optional
from ..core.errors.error_handler import ErrorHandler

class ServiceManager:
    """Service Manager esistente."""

    def __init__(self):
        """Inizializza service manager."""
        self.services = {}
        self.error_handler = ErrorHandler()

    def register_service(self, name: str, service: Any) -> None:
        """Registra servizio."""
        self.services[name] = service

    def get_service(self, name: str) -> Optional[Any]:
        """Recupera servizio."""
        return self.services.get(name)

    def get_status(self) -> Dict[str, Any]:
        """Restituisce stato servizi."""
        return {
            "total_services": len(self.services),
            "services": list(self.services.keys())
        }

# Singleton instance
service_manager = ServiceManager()

def get_service_manager() -> ServiceManager:
    """Restituisce service manager."""
    return service_manager

def initialize_services() -> bool:
    """Inizializza servizi."""
    try:
        # Inizializza servizi esistenti se necessario
        return True
    except Exception as e:
        print(f"Errore inizializzazione servizi: {e}")
        return False

def get_service_status() -> Dict[str, Any]:
    """Restituisce stato servizi."""
    return service_manager.get_status()
