# -*- coding: utf-8 -*-
"""
Questo modulo definisce la struttura gerarchica della conoscenza
utilizzata per categorizzare automaticamente i documenti.

Include modelli Bayesian per la gestione dinamica della conoscenza con punteggi di confidenza.
"""
import re
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Definisce la base di conoscenza come un dizionario.
KNOWLEDGE_BASE_STRUCTURE = {
    "P1_IL_PALCOSCENICO_COSMICO_E_BIOLOGICO": {
        "name": "Parte I: Il Palcoscenico Cosmico e Biologico",
        "chapters": {
            "C01": "L'Universo e la Terra - La Nascita del Contesto",
            "C02": "L'Origine della Vita - La Scintilla Iniziale",
            "C03": "La Diversificazione della Vita e i Meccanismi dell'Evoluzione"
        }
    },
    "P2_L_ASCESA_DEL_GENERE_HOMO": {
        "name": "Parte II: L'Ascesa del Genere Homo",
        "chapters": {
            "C04": "Dalle Scimmie Antropomorfe ai Primi Ominidi",
            "C05": "Homo erectus e la Prima Espansione Globale",
            "C06": "Diversificazione Ominina e Convivenza nel Pleistocene",
            "C07": "L'Emergere di Homo sapiens",
            "C08": "La Specificità di Homo sapiens: Un Confronto"
        }
    },
    "P3_LO_SVILUPPO_DELLE_CIVILTA_UMANE": {
        "name": "Parte III: Lo Sviluppo delle Civiltà Umane",
        "chapters": {
            "C09": "Dalla Caccia-Raccolta all'Agricoltura",
            "C10": "L'Emergere della Complessità Sociale e dello Stato",
            "C11": "Società, Culture ed Economie nel Mondo Antico e Medievale",
            "C12": "La Modernità e le Grandi Rivoluzioni",
            "C13": "Scienza, Tecnologia e Società",
            "C14": "Il Secolo Breve e l'Era Contemporanea"
        }
    },
    "P4_ANALISI_DELLA_CONDIZIONE_UMANA": {
        "name": "Parte IV: Analisi della Condizione Umana",
        "chapters": {
            "C15": "Il Corpo Umano",
            "C16": "Fondamenti della Mente",
            "C17": "Sviluppo Psicologico, Personalità e Psicopatologia",
            "C18": "Valutazione e Intervento in Psicologia Clinica",
            "C19": "Linguaggio, Simboli e Costruzione di Significato",
            "C20": "Cultura, Società e Strutture Sociali",
            "C21": "Psicologia del Contesto Sociale",
            "C22": "Arte, Estetica ed Espressione Umana",
            "C23": "Etica, Morale e Ricerca di Senso",
            "C24": "Educazione, Apprendimento e Trasmissione Culturale",
            "C25": "Salute, Malattia e Medicina"
        }
    },
    "P5_SFIDE_CONTEMPORANEE_E_PROSPETTIVE_FUTURE": {
        "name": "Parte V: Sfide Contemporanee e Prospettive Future",
        "chapters": {
            "C26": "L'Umanità nel XXI Secolo",
            "C27": "Verso il Futuro - Riflessioni Conclusive"
        }
    }
}

def get_category_choices():
    """Restituisce una lista di tuple (id_capitolo, descrizione) per l'UI."""
    choices = [("Tutte", "Mostra tutte le categorie")]
    for part_id, part_data in KNOWLEDGE_BASE_STRUCTURE.items():
        for chapter_id, chapter_name in part_data["chapters"].items():
            full_id = f"{part_id}/{chapter_id}"
            full_description = f"{part_data['name']} -> {chapter_name}"
            choices.append((full_id, full_description))
    return choices

def get_structure_for_prompt(manual_filepath="Master_Indexing_Manual.md"):
    """
    Loads the detailed indexing manual from a file and formats it
    for an LLM prompt.
    """
    try:
        with open(manual_filepath, 'r', encoding='utf-8') as f:
            manual_content = f.read()
    except FileNotFoundError:
        error_message = (
            f"ERRORE CRITICO: Il file del manuale di indicizzazione '{manual_filepath}' non è stato trovato. "
            "Assicurati che il file esista nella stessa directory dello script."
        )
        print(error_message)
        return error_message

    # The final instruction for the LLM, separated from the manual's content.
    prompt_text = (
        f"{manual_content}\n\n"
        "--- ISTRUZIONE PER L'IA ---\n"
        "Analizza il testo del documento fornito e, basandoti ESCLUSIVAMENTE SUL MANUALE SOPRA, identifica l'ID del capitolo più pertinente.\n"
        "La tua risposta DEVE contenere SOLO l'ID completo del capitolo (formato: PARTE/CAPITOLO, es. P2_L_ASCESA_DEL_GENERE_HOMO/C05). "
        "Non aggiungere alcuna spiegazione, titolo o testo aggiuntivo."
    )
    return prompt_text

def is_valid_category_id(category_id):
    """Verifica se un ID di categoria è valido."""
    if not category_id or not isinstance(category_id, str):
        return False

    parts = category_id.split('/')
    if len(parts) != 2:
        return False

    part_id, chapter_id = parts

    return (part_id in KNOWLEDGE_BASE_STRUCTURE and
            chapter_id in KNOWLEDGE_BASE_STRUCTURE[part_id]["chapters"])

# --- MODELLI BAYESIAN PER LA GESTIONE DINAMICA DELLA CONOSCENZA ---

class BayesianKnowledgeEntity(BaseModel):
    """
    Modello Pydantic per le entità concettuali con gestione Bayesiana della confidenza.

    Ogni entità rappresenta un concetto, teoria, autore, formula, tecnica o metodo
    estratto dai documenti, con un punteggio di confidenza dinamico.
    """
    entity_id: Optional[int] = Field(None, description="ID univoco nel database")
    user_id: int = Field(..., description="ID dell'utente proprietario")
    entity_type: str = Field(..., description="Tipo di entità (concept, theory, author, formula, technique, method)")
    entity_name: str = Field(..., description="Nome dell'entità")
    entity_description: Optional[str] = Field(None, description="Descrizione dell'entità")
    source_file_name: str = Field(..., description="Documento sorgente da cui è stata estratta")
    confidence_score: float = Field(0.75, ge=0.0, le=1.0, description="Punteggio di confidenza Bayesiano (0.0-1.0)")
    evidence_count: int = Field(0, description="Numero di prove che hanno contribuito al punteggio")
    created_at: datetime = Field(default_factory=datetime.now, description="Data di creazione")
    updated_at: datetime = Field(default_factory=datetime.now, description="Ultimo aggiornamento")

    class Config:
        from_attributes = True

class BayesianKnowledgeRelationship(BaseModel):
    """
    Modello Pydantic per le relazioni concettuali con gestione Bayesiana della confidenza.

    Ogni relazione rappresenta un collegamento significativo tra entità,
    con un punteggio di confidenza che evolve basandosi sulle prove.
    """
    relationship_id: Optional[int] = Field(None, description="ID univoco nel database")
    user_id: int = Field(..., description="ID dell'utente proprietario")
    source_entity_id: int = Field(..., description="ID dell'entità sorgente")
    target_entity_id: int = Field(..., description="ID dell'entità destinazione")
    relationship_type: str = Field(..., description="Tipo di relazione (proposed_by, related_to, part_of, prerequisite_for, example_of, contradicts, extends)")
    relationship_description: Optional[str] = Field(None, description="Descrizione della relazione")
    confidence_score: float = Field(0.75, ge=0.0, le=1.0, description="Punteggio di confidenza Bayesiano (0.0-1.0)")
    evidence_count: int = Field(0, description="Numero di prove che hanno contribuito al punteggio")
    created_at: datetime = Field(default_factory=datetime.now, description="Data di creazione")
    updated_at: datetime = Field(default_factory=datetime.now, description="Ultimo aggiornamento")

    class Config:
        from_attributes = True

class EvidenceRecord(BaseModel):
    """
    Modello per registrare le prove che contribuiscono all'aggiornamento Bayesiano.
    """
    evidence_id: Optional[int] = Field(None, description="ID univoco della prova")
    entity_id: Optional[int] = Field(None, description="ID dell'entità coinvolta")
    relationship_id: Optional[int] = Field(None, description="ID della relazione coinvolta")
    evidence_type: str = Field(..., description="Tipo di prova (document_extraction, user_feedback, corroboration, contradiction)")
    evidence_source: str = Field(..., description="Fonte della prova (file_name, user_id, etc.)")
    evidence_strength: float = Field(..., ge=0.0, le=1.0, description="Forza della prova (0.0-1.0)")
    evidence_description: str = Field(..., description="Descrizione della prova")
    previous_confidence: float = Field(..., description="Punteggio di confidenza precedente")
    new_confidence: float = Field(..., description="Nuovo punteggio di confidenza")
    created_at: datetime = Field(default_factory=datetime.now, description="Data della prova")

    class Config:
        from_attributes = True

class ConfidenceUpdateRequest(BaseModel):
    """
    Modello per le richieste di aggiornamento della confidenza.
    """
    entity_id: Optional[int] = Field(None, description="ID dell'entità da aggiornare")
    relationship_id: Optional[int] = Field(None, description="ID della relazione da aggiornare")
    entity_name: Optional[str] = Field(None, description="Nome dell'entità (se ID non disponibile)")
    evidence_type: str = Field(..., description="Tipo di prova")
    evidence_strength: float = Field(..., ge=0.0, le=1.0, description="Forza della prova")
    evidence_description: str = Field(..., description="Descrizione della prova")
    user_id: int = Field(..., description="ID dell'utente che fornisce la prova")

# --- FUNZIONI DI UTILITÀ PER LA GESTIONE BAYESIANA ---

def get_default_confidence_score() -> float:
    """
    Restituisce il punteggio di confidenza di default per nuove entità/relazioni.
    Utilizziamo 0.75 come valore "ragionevolmente certo" ma non assoluto.
    """
    return 0.75

def get_evidence_strength(evidence_type: str) -> float:
    """
    Restituisce la forza di default per un tipo di prova specifico.

    Args:
        evidence_type: Tipo di prova (document_extraction, user_feedback, corroboration, contradiction)

    Returns:
        float: Forza della prova (0.0-1.0)
    """
    strength_map = {
        'document_extraction': 0.6,    # Moderata - estrazione AI
        'user_feedback_positive': 0.9, # Alta - conferma utente
        'user_feedback_negative': 0.1, # Molto bassa - smentita utente
        'corroboration': 0.7,          # Buona - conferma incrociata
        'contradiction': 0.2,          # Bassa - contraddizione
        'temporal_decay': -0.05        # Leggera riduzione nel tempo
    }
    return strength_map.get(evidence_type, 0.5)

def calculate_confidence_update(current_confidence: float, evidence_strength: float, learning_rate: float = 0.3) -> float:
    """
    Calcola il nuovo punteggio di confidenza usando una formula Bayesian-inspired.

    Args:
        current_confidence: Punteggio attuale (0.0-1.0)
        evidence_strength: Forza della nuova prova (-1.0 to 1.0)
        learning_rate: Tasso di apprendimento per l'aggiornamento (0.0-1.0)

    Returns:
        float: Nuovo punteggio di confidenza
    """
    # Applica l'aggiornamento con learning rate
    if evidence_strength >= 0:
        # Prova positiva: aumenta la confidenza
        new_confidence = current_confidence * (1 - learning_rate) + evidence_strength * learning_rate
    else:
        # Prova negativa: diminuisce drasticamente la confidenza
        new_confidence = current_confidence * (1 - learning_rate) + abs(evidence_strength) * learning_rate * 0.5

    # Assicurati che il valore sia nel range valido
    return max(0.0, min(1.0, new_confidence))

def get_confidence_color(confidence_score: float) -> str:
    """
    Restituisce un colore rappresentativo del punteggio di confidenza.

    Args:
        confidence_score: Punteggio di confidenza (0.0-1.0)

    Returns:
        str: Colore in formato hex
    """
    if confidence_score >= 0.8:
        return "#28a745"  # Verde brillante - alta confidenza
    elif confidence_score >= 0.6:
        return "#ffc107"  # Giallo - confidenza media
    elif confidence_score >= 0.4:
        return "#fd7e14"  # Arancione - bassa confidenza
    else:
        return "#dc3545"  # Rosso - molto bassa confidenza

def get_confidence_label(confidence_score: float) -> str:
    """
    Restituisce un'etichetta testuale per il punteggio di confidenza.

    Args:
        confidence_score: Punteggio di confidenza (0.0-1.0)

    Returns:
        str: Etichetta descrittiva
    """
    if confidence_score >= 0.8:
        return "Alta Confidenza"
    elif confidence_score >= 0.6:
        return "Confidenza Media"
    elif confidence_score >= 0.3:
        return "Bassa Confidenza"
    else:
        return "Molto Bassa Confidenza"

def validate_confidence_score(confidence_score: float) -> bool:
    """
    Valida che un punteggio di confidenza sia nel range corretto.

    Args:
        confidence_score: Punteggio da validare

    Returns:
        bool: True se valido
    """
    return 0.0 <= confidence_score <= 1.0
