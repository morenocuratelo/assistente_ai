# -*- coding: utf-8 -*-
"""
Funzionalità Avanzate Bayesiane per la Gestione della Conoscenza Dinamica

Questo modulo implementa le caratteristiche avanzate del sistema Bayesiano:
- Corroborazione automatica cross-document
- Decadimento temporale intelligente
- Sistema di raccomandazioni basato sulla confidenza
- Aggregazione multi-utente della confidenza
- Quantificazione avanzata dell'incertezza
"""
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import math

# Import delle nostre strutture dati Bayesian
from knowledge_structure import (
    BayesianKnowledgeEntity,
    BayesianKnowledgeRelationship,
    get_confidence_color,
    get_confidence_label,
    calculate_confidence_update
)

# Import delle funzioni database
from file_utils import (
    db_connect,
    get_user_knowledge_graph,
    get_entities_by_confidence,
    get_relationships_by_confidence,
    apply_temporal_decay,
    get_confidence_statistics
)

# Import del motore di inferenza
from bayesian_inference_engine import (
    create_inference_engine,
    ConfidenceUpdateRequest,
    EvidenceType
)

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- STRUTTURE DATI AVANZATE ---

@dataclass
class CorroborationOpportunity:
    """Rappresenta un'opportunità di corroborazione tra documenti."""
    entity_name: str
    entity_type: str
    documents: List[str] = field(default_factory=list)
    confidence_scores: List[float] = field(default_factory=list)
    corroboration_strength: float = 0.0
    recommended_action: str = ""

@dataclass
class TemporalDecaySchedule:
    """Programma di decadimento temporale intelligente."""
    entity_id: int
    current_confidence: float
    days_since_creation: int
    decay_factor: float
    recommended_decay: float
    reasoning: str = ""

@dataclass
class ConfidenceRecommendation:
    """Raccomandazione per migliorare la confidenza."""
    target_entity_id: int
    target_entity_name: str
    recommendation_type: str
    priority_score: float
    suggested_actions: List[str] = field(default_factory=list)
    expected_confidence_gain: float = 0.0
    reasoning: str = ""

@dataclass
class CrossUserConsensus:
    """Consenso tra utenti su una particolare conoscenza."""
    entity_name: str
    entity_type: str
    user_agreements: Dict[int, float] = field(default_factory=dict)  # user_id -> confidence_score
    consensus_score: float = 0.0
    agreement_level: str = "low"
    recommended_confidence: float = 0.5

# --- SISTEMA DI CORROBORAZIONE AVANZATA ---

class AdvancedCorroborationEngine:
    """
    Motore avanzato per la detection e applicazione automatica di corroborazione.
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.min_corroboration_documents = 2
        self.corroboration_threshold = 0.7

    def find_corroboration_opportunities(self) -> List[CorroborationOpportunity]:
        """
        Trova opportunità di corroborazione analizzando entità presenti in documenti multipli.

        Returns:
            List[CorroborationOpportunity]: Lista di opportunità di corroborazione
        """
        try:
            opportunities = []

            with db_connect() as conn:
                cursor = conn.cursor()

                # Trova entità che appaiono in documenti multipli
                cursor.execute("""
                    SELECT entity_name, entity_type, source_file_name, confidence_score
                    FROM concept_entities
                    WHERE user_id = ?
                    ORDER BY entity_name, source_file_name
                """, (self.user_id,))

                entities = cursor.fetchall()

            # Raggruppa per nome entità
            entities_by_name = defaultdict(list)
            for entity in entities:
                entities_by_name[entity['entity_name']].append({
                    'type': entity['entity_type'],
                    'source': entity['source_file_name'],
                    'confidence': entity['confidence_score']
                })

            # Analizza opportunità di corroborazione
            for entity_name, occurrences in entities_by_name.items():
                if len(occurrences) >= self.min_corroboration_documents:
                    documents = [occ['source'] for occ in occurrences]
                    confidences = [occ['confidence'] for occ in occurrences]

                    # Calcola forza di corroborazione
                    avg_confidence = sum(confidences) / len(confidences)
                    document_diversity = len(set(documents))
                    corroboration_strength = min(avg_confidence + (document_diversity - 1) * 0.1, 0.9)

                    opportunity = CorroborationOpportunity(
                        entity_name=entity_name,
                        entity_type=occurrences[0]['type'],
                        documents=documents,
                        confidence_scores=confidences,
                        corroboration_strength=corroboration_strength,
                        recommended_action=self._get_corroboration_action(corroboration_strength, document_diversity)
                    )

                    opportunities.append(opportunity)

            # Ordina per forza di corroborazione
            opportunities.sort(key=lambda x: x.corroboration_strength, reverse=True)

            logger.info(f"🔗 Trovate {len(opportunities)} opportunità di corroborazione")
            return opportunities

        except Exception as e:
            logger.error(f"Errore nella ricerca opportunità corroborazione: {str(e)}")
            return []

    def _get_corroboration_action(self, strength: float, diversity: int) -> str:
        """Determina l'azione raccomandata per la corroborazione."""
        if strength >= 0.8 and diversity >= 3:
            return "strong_corroboration"
        elif strength >= 0.7 and diversity >= 2:
            return "moderate_corroboration"
        elif diversity >= 3:
            return "weak_corroboration"
        else:
            return "no_action"

    def apply_automatic_corroboration(self, max_opportunities: int = 10) -> Dict[str, Any]:
        """
        Applica automaticamente la corroborazione alle migliori opportunità.

        Args:
            max_opportunities: Numero massimo di opportunità da processare

        Returns:
            dict: Risultati dell'operazione di corroborazione
        """
        try:
            opportunities = self.find_corroboration_opportunities()

            results = {
                'processed': 0,
                'corroborated': 0,
                'skipped': 0,
                'errors': 0,
                'details': []
            }

            # Processa solo le opportunità più promettenti
            for opportunity in opportunities[:max_opportunities]:
                try:
                    if opportunity.corroboration_strength >= self.corroboration_threshold:
                        # Trova tutte le occorrenze dell'entità
                        with db_connect() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                SELECT id, confidence_score FROM concept_entities
                                WHERE user_id = ? AND entity_name = ?
                            """, (self.user_id, opportunity.entity_name))

                            entity_occurrences = cursor.fetchall()

                        # Applica rafforzamento a tutte le occorrenze
                        for entity_row in entity_occurrences:
                            new_confidence = calculate_confidence_update(
                                entity_row['confidence_score'],
                                opportunity.corroboration_strength,
                                0.3  # Learning rate conservativo per corroborazione
                            )

                            cursor.execute("""
                                UPDATE concept_entities
                                SET confidence_score = ?, updated_at = ?
                                WHERE id = ?
                            """, (new_confidence, datetime.now().isoformat(), entity_row['id']))

                        results['corroborated'] += 1
                        results['details'].append({
                            'entity_name': opportunity.entity_name,
                            'documents': len(opportunity.documents),
                            'corroboration_strength': opportunity.corroboration_strength,
                            'entities_updated': len(entity_occurrences)
                        })

                        logger.info(f"✅ Corroborazione applicata: {opportunity.entity_name}")
                    else:
                        results['skipped'] += 1

                    results['processed'] += 1

                except Exception as e:
                    logger.error(f"Errore applicazione corroborazione {opportunity.entity_name}: {str(e)}")
                    results['errors'] += 1

            # Commit all changes
            with db_connect() as conn:
                conn.commit()

            logger.info(f"🔗 Corroborazione automatica completata: {results}")
            return results

        except Exception as e:
            logger.error(f"Errore generale corroborazione automatica: {str(e)}")
            return {'error': str(e)}

# --- SISTEMA DI DECADIMENTO TEMPORALE INTELLIGENTE ---

class IntelligentTemporalDecayEngine:
    """
    Motore per l'applicazione intelligente del decadimento temporale.
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.decay_config = {
            'max_age_days': 365,  # Entità più vecchie di un anno
            'high_confidence_threshold': 0.8,
            'decay_rates': {
                'recent': 0.0,      # < 30 giorni: no decay
                'medium': -0.02,    # 30-90 giorni: slow decay
                'old': -0.05,       # 90-365 giorni: moderate decay
                'very_old': -0.1    # > 365 giorni: fast decay
            }
        }

    def analyze_temporal_decay_opportunities(self) -> List[TemporalDecaySchedule]:
        """
        Analizza quali entità dovrebbero subire decadimento temporale.

        Returns:
            List[TemporalDecaySchedule]: Lista di programmi di decadimento raccomandati
        """
        try:
            schedules = []

            with db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, entity_name, confidence_score, created_at
                    FROM concept_entities
                    WHERE user_id = ?
                    ORDER BY created_at ASC
                """, (self.user_id,))

                entities = cursor.fetchall()

            current_date = datetime.now()

            for entity in entities:
                created_date = datetime.fromisoformat(entity['created_at'])
                days_since_creation = (current_date - created_date).days

                # Determina categoria di età
                if days_since_creation < 30:
                    age_category = 'recent'
                elif days_since_creation < 90:
                    age_category = 'medium'
                elif days_since_creation < 365:
                    age_category = 'old'
                else:
                    age_category = 'very_old'

                decay_factor = self.decay_config['decay_rates'][age_category]

                # Modifica decay basato sulla confidenza attuale
                current_confidence = entity['confidence_score']
                if current_confidence >= self.decay_config['high_confidence_threshold']:
                    decay_factor *= 0.5  # Riduci decay per entità ad alta confidenza

                recommended_decay = current_confidence * decay_factor if decay_factor < 0 else 0

                schedule = TemporalDecaySchedule(
                    entity_id=entity['id'],
                    current_confidence=current_confidence,
                    days_since_creation=days_since_creation,
                    decay_factor=decay_factor,
                    recommended_decay=recommended_decay,
                    reasoning=self._generate_decay_reasoning(age_category, current_confidence, days_since_creation)
                )

                schedules.append(schedule)

            # Ordina per priorità di decadimento (più vecchio + meno confidente = priorità maggiore)
            schedules.sort(key=lambda x: abs(x.recommended_decay), reverse=True)

            logger.info(f"🕐 Analizzate {len(schedules)} opportunità di decadimento temporale")
            return schedules

        except Exception as e:
            logger.error(f"Errore analisi decadimento temporale: {str(e)}")
            return []

    def _generate_decay_reasoning(self, age_category: str, confidence: float, days: int) -> str:
        """Genera spiegazione per il decadimento raccomandato."""
        reasons = []

        if age_category == 'very_old':
            reasons.append(f"Entità vecchia di {days} giorni")
        elif age_category == 'old':
            reasons.append(f"Entità vecchia di {days} giorni")
        elif age_category == 'medium':
            reasons.append(f"Entità di età media ({days} giorni)")

        if confidence >= 0.8:
            reasons.append("Alta confidenza - decadimento ridotto")
        elif confidence <= 0.4:
            reasons.append("Bassa confidenza - decadimento aumentato")

        return " | ".join(reasons) if reasons else "Nessuna ragione specifica"

    def apply_intelligent_decay(self, max_entities: int = 50) -> Dict[str, Any]:
        """
        Applica decadimento temporale intelligente alle entità selezionate.

        Args:
            max_entities: Numero massimo di entità da processare

        Returns:
            dict: Risultati del decadimento
        """
        try:
            schedules = self.analyze_temporal_decay_opportunities()

            results = {
                'processed': 0,
                'decayed': 0,
                'skipped': 0,
                'total_confidence_lost': 0.0,
                'details': []
            }

            # Processa solo le entità che necessitano decadimento significativo
            for schedule in schedules[:max_entities]:
                try:
                    if abs(schedule.recommended_decay) > 0.01:  # Solo se il decadimento è significativo
                        with db_connect() as conn:
                            cursor = conn.cursor()

                            new_confidence = max(0.1, schedule.current_confidence + schedule.recommended_decay)

                            cursor.execute("""
                                UPDATE concept_entities
                                SET confidence_score = ?, updated_at = ?
                                WHERE id = ?
                            """, (new_confidence, datetime.now().isoformat(), schedule.entity_id))

                            confidence_lost = schedule.current_confidence - new_confidence
                            results['total_confidence_lost'] += confidence_lost

                            results['decayed'] += 1
                            results['details'].append({
                                'entity_id': schedule.entity_id,
                                'old_confidence': schedule.current_confidence,
                                'new_confidence': new_confidence,
                                'confidence_lost': confidence_lost,
                                'reasoning': schedule.reasoning
                            })

                            logger.info(f"🕐 Decadimento applicato: {schedule.entity_id} "
                                      f"({schedule.current_confidence:.3f} → {new_confidence:.3f})")
                    else:
                        results['skipped'] += 1

                    results['processed'] += 1

                except Exception as e:
                    logger.error(f"Errore decadimento entità {schedule.entity_id}: {str(e)}")

            # Commit all changes
            with db_connect() as conn:
                conn.commit()

            logger.info(f"🕐 Decadimento intelligente completato: {results}")
            return results

        except Exception as e:
            logger.error(f"Errore generale decadimento intelligente: {str(e)}")
            return {'error': str(e)}

# --- SISTEMA DI RACCOMANDAZIONI BAYESIANO ---

class BayesianRecommendationEngine:
    """
    Motore per generare raccomandazioni intelligenti basate sui dati di confidenza.
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.recommendation_weights = {
            'low_confidence': 0.8,
            'isolated_entities': 0.6,
            'contradictory_evidence': 0.9,
            'missing_corroboration': 0.7,
            'temporal_staleness': 0.5
        }

    def generate_confidence_recommendations(self) -> List[ConfidenceRecommendation]:
        """
        Genera raccomandazioni per migliorare i punteggi di confidenza.

        Returns:
            List[ConfidenceRecommendation]: Lista di raccomandazioni ordinate per priorità
        """
        try:
            recommendations = []

            # 1. Entità a bassa confidenza che necessitano attenzione
            low_confidence_entities = get_entities_by_confidence(
                self.user_id, min_confidence=0.0, max_confidence=0.4
            )

            for entity in low_confidence_entities[:20]:  # Limita a 20 per performance
                rec = ConfidenceRecommendation(
                    target_entity_id=entity['id'],
                    target_entity_name=entity['entity_name'],
                    recommendation_type='low_confidence',
                    priority_score=self.recommendation_weights['low_confidence'],
                    suggested_actions=[
                        'Verificare accuratezza con fonti esterne',
                        'Richiedere conferma da esperti',
                        'Confrontare con documenti correlati'
                    ],
                    expected_confidence_gain=0.3,
                    reasoning=f"Confidenza molto bassa ({entity['confidence_score']:.2f}) - necessita verifica"
                )
                recommendations.append(rec)

            # 2. Entità isolate (senza relazioni)
            isolated_entities = self._find_isolated_entities()
            for entity in isolated_entities[:15]:
                rec = ConfidenceRecommendation(
                    target_entity_id=entity['id'],
                    target_entity_name=entity['entity_name'],
                    recommendation_type='isolated_entities',
                    priority_score=self.recommendation_weights['isolated_entities'],
                    suggested_actions=[
                        'Trovare documenti correlati',
                        'Stabilire connessioni con altre entità',
                        'Verificare esistenza del concetto'
                    ],
                    expected_confidence_gain=0.2,
                    reasoning="Entità senza relazioni - potrebbe essere non significativa"
                )
                recommendations.append(rec)

            # 3. Entità con evidenza contraddittoria
            contradictory_entities = self._find_contradictory_entities()
            for entity in contradictory_entities[:10]:
                rec = ConfidenceRecommendation(
                    target_entity_id=entity['id'],
                    target_entity_name=entity['entity_name'],
                    recommendation_type='contradictory_evidence',
                    priority_score=self.recommendation_weights['contradictory_evidence'],
                    suggested_actions=[
                        'Risolvere contraddizioni tra documenti',
                        'Verificare fonti primarie',
                        'Consultare esperti del settore'
                    ],
                    expected_confidence_gain=0.4,
                    reasoning="Evidenza contraddittoria rilevata - necessita risoluzione"
                )
                recommendations.append(rec)

            # Ordina per priorità
            recommendations.sort(key=lambda x: x.priority_score, reverse=True)

            logger.info(f"💡 Generate {len(recommendations)} raccomandazioni di confidenza")
            return recommendations

        except Exception as e:
            logger.error(f"Errore generazione raccomandazioni: {str(e)}")
            return []

    def _find_isolated_entities(self) -> List[Dict]:
        """Trova entità senza relazioni."""
        try:
            with db_connect() as conn:
                cursor = conn.cursor()

                # Trova entità senza relazioni in uscita
                cursor.execute("""
                    SELECT e.id, e.entity_name, e.confidence_score
                    FROM concept_entities e
                    LEFT JOIN concept_relationships r ON (
                        e.id = r.source_entity_id OR e.id = r.target_entity_id
                    )
                    WHERE e.user_id = ? AND r.id IS NULL
                    ORDER BY e.confidence_score ASC
                """, (self.user_id,))

                isolated = cursor.fetchall()
                return [dict(entity) for entity in isolated]

        except Exception as e:
            logger.error(f"Errore ricerca entità isolate: {str(e)}")
            return []

    def _find_contradictory_entities(self) -> List[Dict]:
        """Trova entità con evidenza contraddittoria."""
        try:
            # Questa è una versione semplificata - in produzione potresti voler
            # implementare analisi più sofisticata delle contraddizioni
            with db_connect() as conn:
                cursor = conn.cursor()

                # Trova entità con ampia varianza nei punteggi di confidenza
                cursor.execute("""
                    SELECT entity_name,
                           COUNT(*) as occurrences,
                           AVG(confidence_score) as avg_confidence,
                           MAX(confidence_score) - MIN(confidence_score) as confidence_range
                    FROM concept_entities
                    WHERE user_id = ?
                    GROUP BY entity_name
                    HAVING occurrences > 1 AND confidence_range > 0.3
                    ORDER BY confidence_range DESC
                """, (self.user_id,))

                contradictory = cursor.fetchall()
                return [dict(entity) for entity in contradictory]

        except Exception as e:
            logger.error(f"Errore ricerca entità contraddittorie: {str(e)}")
            return []

# --- SISTEMA DI AGGREGAZIONE MULTI-UTENTE ---

class MultiUserConfidenceAggregator:
    """
    Sistema per aggregare la confidenza tra utenti multipli.
    """

    def __init__(self):
        self.aggregation_methods = {
            'weighted_average': self._weighted_average_aggregation,
            'majority_vote': self._majority_vote_aggregation,
            'expert_weighted': self._expert_weighted_aggregation
        }

    def aggregate_cross_user_consensus(self, entity_name: str) -> CrossUserConsensus:
        """
        Aggrega il consenso tra utenti per una particolare entità.

        Args:
            entity_name: Nome dell'entità da analizzare

        Returns:
            CrossUserConsensus: Consenso aggregato tra utenti
        """
        try:
            user_agreements = {}

            with db_connect() as conn:
                cursor = conn.cursor()

                # Trova tutti gli utenti che hanno questa entità
                cursor.execute("""
                    SELECT DISTINCT user_id FROM concept_entities WHERE entity_name = ?
                """, (entity_name,))

                users_with_entity = [row['user_id'] for row in cursor.fetchall()]

                # Per ogni utente, trova il punteggio di confidenza medio per questa entità
                for uid in users_with_entity:
                    cursor.execute("""
                        SELECT AVG(confidence_score) as avg_confidence
                        FROM concept_entities
                        WHERE user_id = ? AND entity_name = ?
                    """, (uid, entity_name))

                    result = cursor.fetchone()
                    if result and result['avg_confidence']:
                        user_agreements[uid] = result['avg_confidence']

            if not user_agreements:
                return CrossUserConsensus(
                    entity_name=entity_name,
                    consensus_score=0.0,
                    agreement_level="none"
                )

            # Calcola consenso usando media pesata
            consensus_score = self._calculate_weighted_consensus(user_agreements)

            # Determina livello di accordo
            confidence_values = list(user_agreements.values())
            std_dev = self._calculate_standard_deviation(confidence_values)

            if std_dev < 0.1:
                agreement_level = "high"
            elif std_dev < 0.2:
                agreement_level = "medium"
            else:
                agreement_level = "low"

            return CrossUserConsensus(
                entity_name=entity_name,
                user_agreements=user_agreements,
                consensus_score=consensus_score,
                agreement_level=agreement_level,
                recommended_confidence=consensus_score
            )

        except Exception as e:
            logger.error(f"Errore aggregazione consenso multi-utente: {str(e)}")
            return CrossUserConsensus(
                entity_name=entity_name,
                consensus_score=0.0,
                agreement_level="error"
            )

    def _calculate_weighted_consensus(self, user_agreements: Dict[int, float]) -> float:
        """Calcola consenso pesato basato sulla coerenza interna dell'utente."""
        if not user_agreements:
            return 0.0

        # Per semplicità, usa media semplice
        # In produzione potresti voler pesare per attività utente, expertise, etc.
        return sum(user_agreements.values()) / len(user_agreements)

    def _calculate_standard_deviation(self, values: List[float]) -> float:
        """Calcola deviazione standard."""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

# --- MOTORE DI QUANTIFICAZIONE DELL'INCERTEZZA ---

class UncertaintyQuantifier:
    """
    Sistema avanzato per quantificare l'incertezza nella conoscenza.
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.uncertainty_factors = {
            'evidence_sparsity': 0.3,
            'source_reliability': 0.25,
            'temporal_decay': 0.2,
            'user_disagreement': 0.15,
            'domain_complexity': 0.1
        }

    def quantify_entity_uncertainty(self, entity_id: int) -> Dict[str, Any]:
        """
        Quantifica l'incertezza per una specifica entità.

        Args:
            entity_id: ID dell'entità da analizzare

        Returns:
            dict: Metriche di incertezza dettagliate
        """
        try:
            with db_connect() as conn:
                cursor = conn.cursor()

                # Recupera informazioni entità
                cursor.execute("""
                    SELECT * FROM concept_entities WHERE id = ?
                """, (entity_id,))

                entity = cursor.fetchone()
                if not entity:
                    return {'error': 'Entità non trovata'}

            uncertainty_metrics = {
                'entity_id': entity_id,
                'entity_name': entity['entity_name'],
                'total_uncertainty': 0.0,
                'factors': {},
                'recommendations': []
            }

            # 1. Evidence Sparsity (scarsità di prove)
            evidence_count = self._count_entity_evidence(entity_id)
            sparsity_uncertainty = max(0, 1.0 - (evidence_count / 10.0))  # Più prove = meno incertezza
            uncertainty_metrics['factors']['evidence_sparsity'] = sparsity_uncertainty

            # 2. Source Reliability (affidabilità fonti)
            source_reliability = self._assess_source_reliability(entity['source_file_name'])
            reliability_uncertainty = 1.0 - source_reliability
            uncertainty_metrics['factors']['source_reliability'] = reliability_uncertainty

            # 3. Temporal Decay (decadimento temporale)
            temporal_uncertainty = self._calculate_temporal_uncertainty(entity['created_at'])
            uncertainty_metrics['factors']['temporal_decay'] = temporal_uncertainty

            # 4. User Disagreement (disaccordo utenti)
            user_agreement_uncertainty = self._calculate_user_agreement_uncertainty(entity['entity_name'])
            uncertainty_metrics['factors']['user_disagreement'] = user_agreement_uncertainty

            # 5. Domain Complexity (complessità dominio)
            complexity_uncertainty = self._assess_domain_complexity(entity['entity_type'])
            uncertainty_metrics['factors']['domain_complexity'] = complexity_uncertainty

            # Calcola incertezza totale pesata
            total_uncertainty = sum(
                uncertainty_metrics['factors'][factor] * weight
                for factor, weight in self.uncertainty_factors.items()
            )

            uncertainty_metrics['total_uncertainty'] = min(1.0, total_uncertainty)
            uncertainty_metrics['confidence_equivalent'] = 1.0 - total_uncertainty

            # Genera raccomandazioni
            uncertainty_metrics['recommendations'] = self._generate_uncertainty_recommendations(
                uncertainty_metrics['factors']
            )

            return uncertainty_metrics

        except Exception as e:
            logger.error(f"Errore quantificazione incertezza entità {entity_id}: {str(e)}")
            return {'error': str(e)}

    def _count_entity_evidence(self, entity_id: int) -> int:
        """Conta il numero di prove per un'entità."""
        try:
            with db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as evidence_count FROM bayesian_evidence WHERE entity_id = ?
                """, (entity_id,))

                result = cursor.fetchone()
                return result['evidence_count'] if result else 0

        except Exception as e:
            logger.error(f"Errore conteggio prove entità {entity_id}: {str(e)}")
            return 0

    def _assess_source_reliability(self, source_file: str) -> float:
        """Valuta l'affidabilità di una fonte."""
        # Implementazione semplificata - in produzione potresti voler
        # analizzare il tipo di documento, autore, pubblicazione, etc.
        if 'academic' in source_file.lower() or 'research' in source_file.lower():
            return 0.9
        elif 'review' in source_file.lower() or 'meta' in source_file.lower():
            return 0.8
        else:
            return 0.6

    def _calculate_temporal_uncertainty(self, created_at: str) -> float:
        """Calcola incertezza basata sull'età dell'informazione."""
        try:
            created_date = datetime.fromisoformat(created_at)
            days_old = (datetime.now() - created_date).days

            if days_old < 30:
                return 0.1  # Recente = bassa incertezza
            elif days_old < 180:
                return 0.3  # Medio = incertezza media
            elif days_old < 365:
                return 0.5  # Vecchio = incertezza alta
            else:
                return 0.7  # Molto vecchio = incertezza molto alta

        except Exception:
            return 0.5

    def _calculate_user_agreement_uncertainty(self, entity_name: str) -> float:
        """Calcola incertezza basata sul disaccordo tra utenti."""
        try:
            consensus = MultiUserConfidenceAggregator().aggregate_cross_user_consensus(entity_name)

            if consensus.agreement_level == "high":
                return 0.1
            elif consensus.agreement_level == "medium":
                return 0.3
            else:
                return 0.6

        except Exception:
            return 0.4

    def _assess_domain_complexity(self, entity_type: str) -> float:
        """Valuta la complessità del dominio dell'entità."""
        complexity_map = {
            'concept': 0.3,
            'theory': 0.5,
            'formula': 0.2,
            'technique': 0.4,
            'method': 0.4,
            'author': 0.1
        }
        return complexity_map.get(entity_type, 0.3)

    def _generate_uncertainty_recommendations(self, factors: Dict[str, float]) -> List[str]:
        """Genera raccomandazioni basate sui fattori di incertezza."""
        recommendations = []

        if factors.get('evidence_sparsity', 0) > 0.5:
            recommendations.append("Aggiungere più prove documentali")

        if factors.get('source_reliability', 0) > 0.5:
            recommendations.append("Verificare affidabilità delle fonti")

        if factors.get('temporal_decay', 0) > 0.5:
            recommendations.append("Aggiornare informazioni datate")

        if factors.get('user_disagreement', 0) > 0.5:
            recommendations.append("Risolvere disaccordo tra utenti")

        return recommendations

# --- MOTORE PRINCIPALE DELLE FUNZIONALITÀ AVANZATE ---

class AdvancedBayesianFeatures:
    """
    Motore principale che coordina tutte le funzionalità avanzate Bayesiane.
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.corroboration_engine = AdvancedCorroborationEngine(user_id)
        self.decay_engine = IntelligentTemporalDecayEngine(user_id)
        self.recommendation_engine = BayesianRecommendationEngine(user_id)
        self.uncertainty_quantifier = UncertaintyQuantifier(user_id)
        self.consensus_aggregator = MultiUserConfidenceAggregator()

    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """
        Esegue un'analisi completa di tutte le funzionalità avanzate.

        Returns:
            dict: Risultati completi dell'analisi avanzata
        """
        try:
            logger.info(f"🔬 Avvio analisi avanzata completa per user {self.user_id}")

            results = {
                'timestamp': datetime.now().isoformat(),
                'user_id': self.user_id,
                'corroboration_opportunities': [],
                'decay_schedules': [],
                'confidence_recommendations': [],
                'uncertainty_analyses': [],
                'cross_user_consensus': [],
                'summary': {}
            }

            # 1. Analisi opportunità corroborazione
            corroboration_opportunities = self.corroboration_engine.find_corroboration_opportunities()
            results['corroboration_opportunities'] = [
                {
                    'entity_name': opp.entity_name,
                    'entity_type': opp.entity_type,
                    'document_count': len(opp.documents),
                    'corroboration_strength': opp.corroboration_strength,
                    'recommended_action': opp.recommended_action
                }
                for opp in corroboration_opportunities[:10]  # Limita a 10 per performance
            ]

            # 2. Analisi programmi decadimento
            decay_schedules = self.decay_engine.analyze_temporal_decay_opportunities()
            results['decay_schedules'] = [
                {
                    'entity_id': schedule.entity_id,
                    'current_confidence': schedule.current_confidence,
                    'days_since_creation': schedule.days_since_creation,
                    'recommended_decay': schedule.recommended_decay,
                    'reasoning': schedule.reasoning
                }
                for schedule in decay_schedules[:15]  # Limita a 15 per performance
            ]

            # 3. Generazione raccomandazioni
            recommendations = self.recommendation_engine.generate_confidence_recommendations()
            results['confidence_recommendations'] = [
                {
                    'entity_name': rec.target_entity_name,
                    'recommendation_type': rec.recommendation_type,
                    'priority_score': rec.priority_score,
                    'suggested_actions': rec.suggested_actions,
                    'expected_gain': rec.expected_confidence_gain,
                    'reasoning': rec.reasoning
                }
                for rec in recommendations[:10]  # Limita a 10 per performance
            ]

            # 4. Analisi incertezza per entità chiave
            # Trova entità più importanti per l'analisi
            important_entities = get_entities_by_confidence(
                self.user_id, min_confidence=0.5, max_confidence=1.0
            )[:5]  # Prime 5 entità

            for entity in important_entities:
                uncertainty_analysis = self.uncertainty_quantifier.quantify_entity_uncertainty(entity['id'])
                if 'error' not in uncertainty_analysis:
                    results['uncertainty_analyses'].append({
                        'entity_name': entity['entity_name'],
                        'total_uncertainty': uncertainty_analysis['total_uncertainty'],
                        'confidence_equivalent': uncertainty_analysis['confidence_equivalent'],
                        'top_factors': self._get_top_uncertainty_factors(uncertainty_analysis['factors']),
                        'recommendations': uncertainty_analysis['recommendations']
                    })

            # 5. Analisi consenso multi-utente per entità chiave
            entity_names = list(set([e['entity_name'] for e in important_entities]))
            for entity_name in entity_names[:3]:  # Limita a 3 per performance
                consensus = self.consensus_aggregator.aggregate_cross_user_consensus(entity_name)
                results['cross_user_consensus'].append({
                    'entity_name': consensus.entity_name,
                    'user_count': len(consensus.user_agreements),
                    'consensus_score': consensus.consensus_score,
                    'agreement_level': consensus.agreement_level,
                    'recommended_confidence': consensus.recommended_confidence
                })

            # 6. Genera riassunto
            results['summary'] = self._generate_comprehensive_summary(results)

            logger.info(f"✅ Analisi avanzata completata per user {self.user_id}")
            return results

        except Exception as e:
            logger.error(f"Errore analisi avanzata completa: {str(e)}")
            return {'error': str(e)}

    def _get_top_uncertainty_factors(self, factors: Dict[str, float]) -> List[Tuple[str, float]]:
        """Restituisce i fattori di incertezza più significativi."""
        sorted_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)
        return sorted_factors[:3]  # Primi 3 fattori

    def _generate_comprehensive_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un riassunto completo dell'analisi."""
        summary = {
            'total_opportunities': len(results['corroboration_opportunities']),
            'total_recommendations': len(results['confidence_recommendations']),
            'total_uncertainty_analyses': len(results['uncertainty_analyses']),
            'high_priority_recommendations': 0,
            'avg_uncertainty': 0.0,
            'key_insights': []
        }

        # Conta raccomandazioni ad alta priorità
        for rec in results['confidence_recommendations']:
            if rec['priority_score'] >= 0.7:
                summary['high_priority_recommendations'] += 1

        # Calcola incertezza media
        if results['uncertainty_analyses']:
            avg_uncertainty = sum(
                analysis['total_uncertainty'] for analysis in results['uncertainty_analyses']
            ) / len(results['uncertainty_analyses'])
            summary['avg_uncertainty'] = avg_uncertainty

        # Genera insight chiave
        if summary['high_priority_recommendations'] > 0:
            summary['key_insights'].append(f"🎯 {summary['high_priority_recommendations']} raccomandazioni ad alta priorità richiedono attenzione")

        if summary['avg_uncertainty'] > 0.5:
            summary['key_insights'].append("⚠️ Alta incertezza media - considera revisione delle fonti")

        if results['corroboration_opportunities']:
            strong_opportunities = sum(1 for opp in results['corroboration_opportunities']
                                     if opp['corroboration_strength'] >= 0.8)
            if strong_opportunities > 0:
                summary['key_insights'].append(f"🔗 {strong_opportunities} forti opportunità di corroborazione disponibili")

        return summary

# --- FUNZIONI DI UTILITÀ GLOBALI ---

def run_advanced_bayesian_analysis(user_id: int) -> Dict[str, Any]:
    """
    Funzione principale per eseguire l'analisi avanzata Bayesiana.

    Args:
        user_id: ID dell'utente da analizzare

    Returns:
        dict: Risultati completi dell'analisi
    """
    engine = AdvancedBayesianFeatures(user_id)
    return engine.run_comprehensive_analysis()

def apply_automatic_improvements(user_id: int, max_actions: int = 5) -> Dict[str, Any]:
    """
    Applica automaticamente miglioramenti al grafo della conoscenza.

    Args:
        user_id: ID dell'utente
        max_actions: Numero massimo di azioni automatiche da applicare

    Returns:
        dict: Risultati dei miglioramenti automatici
    """
    try:
        logger.info(f"🚀 Applicazione miglioramenti automatici per user {user_id}")

        results = {
            'corroboration_applied': 0,
            'decay_applied': 0,
            'total_actions': 0,
            'errors': []
        }

        # 1. Applica corroborazione automatica
        corroboration_engine = AdvancedCorroborationEngine(user_id)
        corroboration_result = corroboration_engine.apply_automatic_corroboration(max_actions)

        if 'corroborated' in corroboration_result:
            results['corroboration_applied'] = corroboration_result['corroborated']
            results['total_actions'] += corroboration_result['processed']

        # 2. Applica decadimento intelligente
        decay_engine = IntelligentTemporalDecayEngine(user_id)
        decay_result = decay_engine.apply_intelligent_decay(max_actions)

        if 'decayed' in decay_result:
            results['decay_applied'] = decay_result['decayed']
            results['total_actions'] += decay_result['processed']

        logger.info(f"✅ Miglioramenti automatici applicati: {results}")
        return results

    except Exception as e:
        logger.error(f"Errore applicazione miglioramenti automatici: {str(e)}")
        return {'error': str(e)}

# --- INTERFACCIA PRINCIPALE ---

def main():
    """Funzione principale per test e demo delle funzionalità avanzate."""
    print("🔬 Funzionalità Avanzate Bayesiane per la Gestione della Conoscenza")
    print("=" * 80)

    # Demo di creazione motori avanzati
    corroboration_engine = AdvancedCorroborationEngine(user_id=1)
    decay_engine = IntelligentTemporalDecayEngine(user_id=1)
    recommendation_engine = BayesianRecommendationEngine(user_id=1)

    print("✅ Motori avanzati creati con successo")
    print(f"🔗 Corroboration threshold: {corroboration_engine.corroboration_threshold}")
    print(f"🕐 Max age days: {decay_engine.decay_config['max_age_days']}")
    print(f"💡 Recommendation weights: {recommendation_engine.recommendation_weights}")

    # Nota: Questo è solo un demo - in produzione servirebbero dati reali
    print("\n💡 Per utilizzare completamente le funzionalità avanzate:")
    print("1. Popolare il database con entità e relazioni reali")
    print("2. Avere documenti multipli per la corroborazione")
    print("3. Avere utenti multipli per l'aggregazione del consenso")
    print("4. Eseguire analisi periodiche per il decadimento temporale")

if __name__ == "__main__":
    main()
