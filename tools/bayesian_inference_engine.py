# -*- coding: utf-8 -*-
"""
Motore di Inferenza Bayesiano per la Gestione Dinamica della Conoscenza

Questo modulo implementa la logica centrale per l'aggiornamento dinamico
dei punteggi di confidenza utilizzando principi Bayesian-inspired.
"""
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

# Import delle nostre strutture dati Bayesian
from knowledge_structure import (
    BayesianKnowledgeEntity,
    BayesianKnowledgeRelationship,
    EvidenceRecord,
    ConfidenceUpdateRequest,
    get_default_confidence_score,
    get_evidence_strength,
    calculate_confidence_update,
    get_confidence_color,
    get_confidence_label
)

# Import delle funzioni database
from file_utils import (
    create_bayesian_entity,
    create_bayesian_relationship,
    update_entity_confidence,
    update_relationship_confidence,
    record_evidence,
    find_or_create_entity,
    find_or_create_relationship,
    get_entity_evidence_history,
    get_relationship_evidence_history,
    apply_temporal_decay,
    corroborate_entities_across_documents,
    get_confidence_statistics
)

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ENUMERAZIONI PER I TIPI DI PROVA ---

class EvidenceType(Enum):
    """Tipi di prova che possono influenzare i punteggi di confidenza."""
    DOCUMENT_EXTRACTION = "document_extraction"
    USER_FEEDBACK_POSITIVE = "user_feedback_positive"
    USER_FEEDBACK_NEGATIVE = "user_feedback_negative"
    CORROBORATION = "corroboration"
    CONTRADICTION = "contradiction"
    TEMPORAL_DECAY = "temporal_decay"
    CROSS_REFERENCE = "cross_reference"
    AUTHORITY_ENDORSEMENT = "authority_endorsement"

class EvidenceSource(Enum):
    """Fonti dalle quali possono provenire le prove."""
    AI_EXTRACTION = "ai_extraction"
    USER_INPUT = "user_input"
    CROSS_DOCUMENT = "cross_document"
    TEMPORAL_SYSTEM = "temporal_system"
    EXTERNAL_AUTHORITY = "external_authority"
    PEER_REVIEW = "peer_review"

# --- STRUTTURE DATI PER IL MOTORE DI INFERENZA ---

@dataclass
class Evidence:
    """Rappresenta una singola prova che influenza la confidenza."""
    evidence_type: EvidenceType
    source: EvidenceSource
    strength: float
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ConfidenceUpdate:
    """Rappresenta un aggiornamento di confidenza."""
    entity_id: Optional[int] = None
    relationship_id: Optional[int] = None
    entity_name: Optional[str] = None
    previous_confidence: float = 0.0
    new_confidence: float = 0.0
    evidence_used: List[Evidence] = field(default_factory=list)
    update_reason: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class InferenceResult:
    """Risultato di un'operazione di inferenza."""
    success: bool
    updates_performed: List[ConfidenceUpdate] = field(default_factory=list)
    entities_created: int = 0
    relationships_created: int = 0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

# --- MOTORE DI INFERENZA PRINCIPALE ---

class BayesianInferenceEngine:
    """
    Motore principale per l'inferenza Bayesiana sulla conoscenza.

    Gestisce l'aggiornamento dinamico dei punteggi di confidenza
    basandosi su nuove prove e mantiene la coerenza del grafo.
    """

    def __init__(self, user_id: int, learning_rate: float = 0.3):
        """
        Inizializza il motore di inferenza.

        Args:
            user_id: ID dell'utente per cui opera il motore
            learning_rate: Tasso di apprendimento per gli aggiornamenti (0.0-1.0)
        """
        self.user_id = user_id
        self.learning_rate = max(0.1, min(0.8, learning_rate))  # Range sicuro
        self.evidence_weights = self._initialize_evidence_weights()
        self.temporal_decay_enabled = True
        self.corroboration_enabled = True

        logger.info(f"🔬 BayesianInferenceEngine inizializzato per user_id={user_id}")
        logger.info(f"⚙️ Learning rate: {self.learning_rate}")
        logger.info(f"📊 Evidence weights: {self.evidence_weights}")

    def _initialize_evidence_weights(self) -> Dict[EvidenceType, float]:
        """Inizializza i pesi per i diversi tipi di prova."""
        return {
            EvidenceType.DOCUMENT_EXTRACTION: 0.6,
            EvidenceType.USER_FEEDBACK_POSITIVE: 0.9,
            EvidenceType.USER_FEEDBACK_NEGATIVE: 0.1,
            EvidenceType.CORROBORATION: 0.7,
            EvidenceType.CONTRADICTION: 0.2,
            EvidenceType.TEMPORAL_DECAY: -0.05,
            EvidenceType.CROSS_REFERENCE: 0.65,
            EvidenceType.AUTHORITY_ENDORSEMENT: 0.85
        }

    def update_belief(self, request: ConfidenceUpdateRequest) -> InferenceResult:
        """
        Funzione principale per l'aggiornamento di una credenza (entità o relazione).

        Args:
            request: Richiesta di aggiornamento con tutti i dettagli necessari

        Returns:
            InferenceResult: Risultato dell'operazione di inferenza
        """
        logger.info(f"🔄 Aggiornamento credenza richiesto: {request.evidence_type}")

        result = InferenceResult(success=False)

        try:
            # Determina se stiamo aggiornando un'entità o una relazione
            if request.entity_id or request.entity_name:
                result = self._update_entity_confidence(request)
            elif request.relationship_id:
                result = self._update_relationship_confidence(request)
            else:
                result.errors.append("Né entity_id né relationship_id specificati")
                return result

            # Applica effetti collaterali se l'aggiornamento ha successo
            if result.success:
                self._apply_side_effects(request, result)

            return result

        except Exception as e:
            error_msg = f"Errore nell'aggiornamento credenza: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result

    def _update_entity_confidence(self, request: ConfidenceUpdateRequest) -> InferenceResult:
        """Aggiorna la confidenza di un'entità."""
        result = InferenceResult(success=False)

        try:
            # Trova o crea l'entità
            if request.entity_id:
                # Verifica che l'entità esista
                from file_utils import db_connect
                with db_connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM concept_entities WHERE id = ? AND user_id = ?",
                                 (request.entity_id, self.user_id))
                    if not cursor.fetchone():
                        result.errors.append(f"Entità {request.entity_id} non trovata")
                        return result
                entity_id = request.entity_id
            else:
                # Crea nuova entità se specificato solo il nome
                if not request.entity_name:
                    result.errors.append("entity_name richiesto se entity_id non specificato")
                    return result
                entity_id = find_or_create_entity(
                    self.user_id, request.entity_name, "concept",
                    f"user_{self.user_id}"
                )
                result.entities_created += 1

            # Calcola la forza effettiva della prova
            base_strength = get_evidence_strength(request.evidence_type)
            effective_strength = base_strength * request.evidence_strength

            # Applica l'aggiornamento
            new_confidence = update_entity_confidence(
                entity_id=entity_id,
                evidence_type=request.evidence_type,
                evidence_strength=effective_strength,
                evidence_description=request.evidence_description
            )

            # Registra l'aggiornamento
            update_record = ConfidenceUpdate(
                entity_id=entity_id,
                previous_confidence=0.75,  # Questo verrà recuperato dal database se necessario
                new_confidence=new_confidence,
                evidence_used=[],  # Popolato dalla funzione di update
                update_reason=request.evidence_description
            )

            result.success = True
            result.updates_performed.append(update_record)

            logger.info(f"✅ Entità {entity_id} aggiornata: {new_confidence:.3f}")

            return result

        except Exception as e:
            result.errors.append(f"Errore aggiornamento entità: {str(e)}")
            return result

    def _update_relationship_confidence(self, request: ConfidenceUpdateRequest) -> InferenceResult:
        """Aggiorna la confidenza di una relazione."""
        result = InferenceResult(success=False)

        try:
            if not request.relationship_id:
                result.errors.append("relationship_id richiesto per aggiornamenti relazioni")
                return result

            # Calcola la forza effettiva della prova
            base_strength = get_evidence_strength(request.evidence_type)
            effective_strength = base_strength * request.evidence_strength

            # Applica l'aggiornamento
            new_confidence = update_relationship_confidence(
                relationship_id=request.relationship_id,
                evidence_type=request.evidence_type,
                evidence_strength=effective_strength,
                evidence_description=request.evidence_description
            )

            # Registra l'aggiornamento
            update_record = ConfidenceUpdate(
                relationship_id=request.relationship_id,
                previous_confidence=0.75,  # Questo verrà recuperato dal database se necessario
                new_confidence=new_confidence,
                evidence_used=[],  # Popolato dalla funzione di update
                update_reason=request.evidence_description
            )

            result.success = True
            result.updates_performed.append(update_record)

            logger.info(f"✅ Relazione {request.relationship_id} aggiornata: {new_confidence:.3f}")

            return result

        except Exception as e:
            result.errors.append(f"Errore aggiornamento relazione: {str(e)}")
            return result

    def _apply_side_effects(self, request: ConfidenceUpdateRequest, result: InferenceResult):
        """Applica effetti collaterali dopo un aggiornamento riuscito."""
        try:
            # 1. Corroborazione automatica se abilitata
            if (self.corroboration_enabled and
                request.evidence_type in ['document_extraction', 'user_feedback_positive']):

                # Se abbiamo aggiornato un'entità, cerca corroborazione
                if request.entity_name:
                    corroboration_result = corroborate_entities_across_documents(
                        self.user_id, request.entity_name
                    )
                    if corroboration_result.get('corroborated'):
                        logger.info(f"🔗 Corroborazione applicata: {request.entity_name}")

            # 2. Propagazione della confidenza (entità correlate)
            if request.entity_id and request.evidence_type == 'user_feedback_positive':
                self._propagate_confidence_to_relationships(request.entity_id)

        except Exception as e:
            logger.warning(f"⚠️ Errore negli effetti collaterali: {str(e)}")

    def _propagate_confidence_to_relationships(self, entity_id: int):
        """Propaga la confidenza dalle entità alle loro relazioni."""
        try:
            from file_utils import db_connect

            with db_connect() as conn:
                cursor = conn.cursor()

                # Trova tutte le relazioni che coinvolgono questa entità
                cursor.execute("""
                    SELECT id, confidence_score FROM concept_relationships
                    WHERE user_id = ? AND (source_entity_id = ? OR target_entity_id = ?)
                """, (self.user_id, entity_id, entity_id))

                relationships = cursor.fetchall()

                for rel in relationships:
                    # Aumenta leggermente la confidenza delle relazioni correlate
                    current_confidence = rel['confidence_score']
                    propagation_strength = 0.1  # Piccolo incremento

                    new_confidence = calculate_confidence_update(
                        current_confidence, propagation_strength, self.learning_rate
                    )

                    cursor.execute("""
                        UPDATE concept_relationships
                        SET confidence_score = ?, updated_at = ?
                        WHERE id = ?
                    """, (new_confidence, datetime.now().isoformat(), rel['id']))

                    # Registra la propagazione come prova
                    record_evidence(
                        relationship_id=rel['id'],
                        evidence_type='cross_reference',
                        evidence_source=f"propagation_from_entity_{entity_id}",
                        evidence_strength=propagation_strength,
                        evidence_description="Propagazione confidenza da entità correlata"
                    )

                conn.commit()
                logger.info(f"🔄 Confidenza propagata a {len(relationships)} relazioni")

        except Exception as e:
            logger.warning(f"⚠️ Errore propagazione confidenza: {str(e)}")

    def process_document_evidence(self, document_file_name: str,
                                extracted_entities: List[Dict],
                                extracted_relationships: List[Dict]) -> InferenceResult:
        """
        Processa le prove estratte da un documento.

        Args:
            document_file_name: Nome del file documento
            extracted_entities: Lista di entità estratte
            extracted_relationships: Lista di relazioni estratte

        Returns:
            InferenceResult: Risultato del processamento
        """
        logger.info(f"📄 Processamento documento: {document_file_name}")

        result = InferenceResult(success=True)

        try:
            # Processa entità estratte
            for entity_data in extracted_entities:
                try:
                    # Crea o trova l'entità
                    entity_id = find_or_create_entity(
                        user_id=self.user_id,
                        entity_name=entity_data['name'],
                        entity_type=entity_data.get('type', 'concept'),
                        source_file_name=document_file_name
                    )

                    # Applica aggiornamento con prova di estrazione
                    request = ConfidenceUpdateRequest(
                        entity_id=entity_id,
                        evidence_type='document_extraction',
                        evidence_strength=0.8,  # Alta confidenza per estrazioni dirette
                        evidence_description=f"Estrazione da documento: {document_file_name}",
                        user_id=self.user_id
                    )

                    entity_result = self.update_belief(request)
                    if entity_result.success:
                        result.entities_created += 1 if 'nuova' in entity_result.metadata else 0
                    else:
                        result.errors.extend(entity_result.errors)

                except Exception as e:
                    result.errors.append(f"Errore processamento entità {entity_data.get('name', 'unknown')}: {str(e)}")

            # Processa relazioni estratte
            for rel_data in extracted_relationships:
                try:
                    # Crea o trova la relazione
                    relationship_id = find_or_create_relationship(
                        user_id=self.user_id,
                        source_entity_name=rel_data['source'],
                        target_entity_name=rel_data['target'],
                        relationship_type=rel_data.get('type', 'related_to')
                    )

                    # Applica aggiornamento con prova di estrazione
                    request = ConfidenceUpdateRequest(
                        relationship_id=relationship_id,
                        evidence_type='document_extraction',
                        evidence_strength=0.7,  # Leggermente inferiore per relazioni
                        evidence_description=f"Relazione estratta da documento: {document_file_name}",
                        user_id=self.user_id
                    )

                    rel_result = self.update_belief(request)
                    if rel_result.success:
                        result.relationships_created += 1 if 'nuova' in rel_result.metadata else 0
                    else:
                        result.errors.extend(rel_result.errors)

                except Exception as e:
                    result.errors.append(f"Errore processamento relazione {rel_data.get('source', 'unknown')}-{rel_data.get('target', 'unknown')}: {str(e)}")

            logger.info(f"✅ Documento processato: {result.entities_created} entità, {result.relationships_created} relazioni")

            return result

        except Exception as e:
            error_msg = f"Errore generale processamento documento: {str(e)}"
            logger.error(error_msg)
            result.success = False
            result.errors.append(error_msg)
            return result

    def process_user_feedback(self, target_type: str, target_id: int,
                            feedback_type: str, feedback_strength: float = 1.0,
                            feedback_text: str = "") -> InferenceResult:
        """
        Processa il feedback dell'utente su entità o relazioni.

        Args:
            target_type: 'entity' o 'relationship'
            target_id: ID del target del feedback
            feedback_type: 'positive', 'negative', o 'correction'
            feedback_strength: Forza del feedback (0.0-1.0)
            feedback_text: Testo esplicativo del feedback

        Returns:
            InferenceResult: Risultato del processamento
        """
        logger.info(f"👤 Processamento feedback utente: {target_type} {target_id}")

        result = InferenceResult(success=False)

        try:
            # Determina il tipo di prova basato sul feedback
            if feedback_type == 'positive':
                evidence_type = 'user_feedback_positive'
                strength = 0.9 * feedback_strength
            elif feedback_type == 'negative':
                evidence_type = 'user_feedback_negative'
                strength = 0.1 * feedback_strength
            elif feedback_type == 'correction':
                evidence_type = 'user_feedback_negative'  # Le correzioni riducono la confidenza
                strength = 0.2 * feedback_strength
            else:
                result.errors.append(f"Tipo di feedback non riconosciuto: {feedback_type}")
                return result

            # Crea la richiesta di aggiornamento
            if target_type == 'entity':
                request = ConfidenceUpdateRequest(
                    entity_id=target_id,
                    evidence_type=evidence_type,
                    evidence_strength=strength,
                    evidence_description=f"Feedback utente: {feedback_text}",
                    user_id=self.user_id
                )
            elif target_type == 'relationship':
                request = ConfidenceUpdateRequest(
                    relationship_id=target_id,
                    evidence_type=evidence_type,
                    evidence_strength=strength,
                    evidence_description=f"Feedback utente: {feedback_text}",
                    user_id=self.user_id
                )
            else:
                result.errors.append(f"Tipo di target non riconosciuto: {target_type}")
                return result

            # Applica l'aggiornamento
            update_result = self.update_belief(request)

            if update_result.success:
                result.success = True
                result.updates_performed.extend(update_result.updates_performed)
                logger.info(f"✅ Feedback utente processato con successo")
            else:
                result.errors.extend(update_result.errors)

            return result

        except Exception as e:
            error_msg = f"Errore processamento feedback: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result

    def apply_temporal_decay_to_all(self) -> InferenceResult:
        """
        Applica decadimento temporale a tutte le entità e relazioni dell'utente.

        Returns:
            InferenceResult: Risultato dell'operazione
        """
        logger.info("🕐 Applicazione decadimento temporale globale")

        result = InferenceResult(success=True)

        try:
            decay_result = apply_temporal_decay(self.user_id)

            result.metadata.update(decay_result)

            if decay_result['entities_updated'] > 0 or decay_result['relationships_updated'] > 0:
                logger.info(f"✅ Decadimento applicato: {decay_result['entities_updated']} entità, {decay_result['relationships_updated']} relazioni")
            else:
                logger.info("ℹ️ Nessun elemento da aggiornare con decadimento temporale")

            return result

        except Exception as e:
            error_msg = f"Errore applicazione decadimento temporale: {str(e)}"
            logger.error(error_msg)
            result.success = False
            result.errors.append(error_msg)
            return result

    def get_confidence_summary(self) -> Dict[str, Any]:
        """
        Fornisce un riassunto completo dello stato di confidenza del grafo.

        Returns:
            dict: Statistiche e insight sulla confidenza
        """
        try:
            stats = get_confidence_statistics(self.user_id)

            # Aggiungi informazioni aggiuntive
            summary = {
                'statistics': stats,
                'engine_settings': {
                    'learning_rate': self.learning_rate,
                    'temporal_decay_enabled': self.temporal_decay_enabled,
                    'corroboration_enabled': self.corroboration_enabled,
                    'evidence_weights': self.evidence_weights
                },
                'last_updated': datetime.now().isoformat(),
                'user_id': self.user_id
            }

            return summary

        except Exception as e:
            logger.error(f"Errore generazione riassunto confidenza: {str(e)}")
            return {
                'error': str(e),
                'user_id': self.user_id,
                'last_updated': datetime.now().isoformat()
            }

    def export_evidence_history(self, entity_id: int = None, relationship_id: int = None,
                              limit: int = 100) -> List[Dict]:
        """
        Esporta la cronologia delle prove per analisi.

        Args:
            entity_id: ID entità specifica (opzionale)
            relationship_id: ID relazione specifica (opzionale)
            limit: Numero massimo di record

        Returns:
            list: Lista delle prove formattate
        """
        try:
            if entity_id:
                evidence = get_entity_evidence_history(entity_id, limit)
            elif relationship_id:
                evidence = get_relationship_evidence_history(relationship_id, limit)
            else:
                # Se non specificato, recupera evidenza generale recente
                from file_utils import db_connect
                with db_connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT * FROM bayesian_evidence
                        WHERE entity_id IN (SELECT id FROM concept_entities WHERE user_id = ?)
                           OR relationship_id IN (SELECT id FROM concept_relationships WHERE user_id = ?)
                        ORDER BY created_at DESC LIMIT ?
                    """, (self.user_id, self.user_id, limit))

                    evidence = [dict(e) for e in cursor.fetchall()]

            return evidence

        except Exception as e:
            logger.error(f"Errore esportazione cronologia prove: {str(e)}")
            return []

# --- FUNZIONI DI UTILITÀ GLOBALI ---

def create_inference_engine(user_id: int, learning_rate: float = 0.3) -> BayesianInferenceEngine:
    """
    Factory function per creare un motore di inferenza configurato.

    Args:
        user_id: ID dell'utente
        learning_rate: Tasso di apprendimento

    Returns:
        BayesianInferenceEngine: Motore configurato e pronto all'uso
    """
    return BayesianInferenceEngine(user_id, learning_rate)

def process_evidence_batch(user_id: int, evidence_batch: List[ConfidenceUpdateRequest]) -> InferenceResult:
    """
    Processa un batch di richieste di aggiornamento della confidenza.

    Args:
        user_id: ID dell'utente
        evidence_batch: Lista di richieste di aggiornamento

    Returns:
        InferenceResult: Risultato aggregato del batch
    """
    logger.info(f"🔄 Processamento batch di {len(evidence_batch)} aggiornamenti")

    engine = BayesianInferenceEngine(user_id)
    overall_result = InferenceResult(success=True)

    for i, request in enumerate(evidence_batch):
        try:
            logger.info(f"📦 Processamento richiesta {i+1}/{len(evidence_batch)}")

            single_result = engine.update_belief(request)

            if single_result.success:
                overall_result.updates_performed.extend(single_result.updates_performed)
                overall_result.entities_created += single_result.entities_created
                overall_result.relationships_created += single_result.relationships_created
            else:
                overall_result.errors.extend(single_result.errors)

        except Exception as e:
            overall_result.errors.append(f"Errore processamento richiesta {i+1}: {str(e)}")

    # Determina successo complessivo
    overall_result.success = len(overall_result.errors) == 0

    logger.info(f"✅ Batch completato: {len(overall_result.updates_performed)} aggiornamenti, {len(overall_result.errors)} errori")

    return overall_result

# --- SISTEMA DI MONITORAGGIO E ANALYTICS ---

class ConfidenceMonitor:
    """
    Sistema di monitoraggio per tracciare le performance del motore di inferenza.
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.metrics = {
            'total_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'avg_confidence_change': 0.0,
            'evidence_types_used': {},
            'last_activity': None
        }

    def record_update(self, previous_confidence: float, new_confidence: float,
                     evidence_type: str, success: bool = True):
        """Registra una metrica di aggiornamento."""
        self.metrics['total_updates'] += 1
        self.metrics['last_activity'] = datetime.now()

        if success:
            self.metrics['successful_updates'] += 1
            confidence_change = abs(new_confidence - previous_confidence)
            self.metrics['avg_confidence_change'] = (
                (self.metrics['avg_confidence_change'] * (self.metrics['successful_updates'] - 1) + confidence_change)
                / self.metrics['successful_updates']
            )
        else:
            self.metrics['failed_updates'] += 1

        # Conta tipi di evidenza
        if evidence_type not in self.metrics['evidence_types_used']:
            self.metrics['evidence_types_used'][evidence_type] = 0
        self.metrics['evidence_types_used'][evidence_type] += 1

    def get_performance_report(self) -> Dict[str, Any]:
        """Genera un report delle performance."""
        success_rate = (
            self.metrics['successful_updates'] / max(1, self.metrics['total_updates'])
        )

        return {
            'user_id': self.user_id,
            'metrics': self.metrics,
            'success_rate': success_rate,
            'report_generated': datetime.now().isoformat(),
            'recommendations': self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Genera raccomandazioni basate sulle metriche."""
        recommendations = []

        if self.metrics['failed_updates'] / max(1, self.metrics['total_updates']) > 0.1:
            recommendations.append("⚠️ Alto tasso di fallimenti - verifica la qualità delle prove")

        if self.metrics['avg_confidence_change'] < 0.05:
            recommendations.append("💡 Bassa variabilità - considera di aumentare il learning rate")

        if len(self.metrics['evidence_types_used']) < 3:
            recommendations.append("🔬 Diversifica le fonti di prova per migliorare l'accuratezza")

        return recommendations

# --- INTERFACCIA PRINCIPALE ---

def main():
    """Funzione principale per test e demo del motore."""
    print("🧠 Motore di Inferenza Bayesiano per la Gestione della Conoscenza")
    print("=" * 70)

    # Demo di creazione motore
    engine = create_inference_engine(user_id=1, learning_rate=0.3)

    print("✅ Motore creato con successo")
    print(f"📊 Learning rate: {engine.learning_rate}")
    print(f"⚖️ Pesi evidenza: {engine.evidence_weights}")

    # Demo richiesta di aggiornamento
    request = ConfidenceUpdateRequest(
        entity_name="Intelligenza Artificiale",
        evidence_type="document_extraction",
        evidence_strength=0.8,
        evidence_description="Concetto estratto da documento accademico",
        user_id=1
    )

    print(f"\n🔄 Test aggiornamento: {request.entity_name}")
    print(f"📝 Descrizione: {request.evidence_description}")

    # Nota: Questo è solo un demo - in produzione servirebbe un database reale
    print("\n💡 Per utilizzare completamente il motore:")
    print("1. Configurare un database SQLite con le tabelle Bayesian")
    print("2. Fornire dati di entità e relazioni reali")
    print("3. Integrare con il sistema di processamento documenti")

if __name__ == "__main__":
    main()
