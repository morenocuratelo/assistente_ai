# -*- coding: utf-8 -*-
"""
Questo modulo definisce la struttura gerarchica della conoscenza
utilizzata per categorizzare automaticamente i documenti.
"""
import re

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

def get_structure_for_prompt():
    """Formatta la struttura in una stringa ottimizzata per un prompt LLM."""
    prompt_text = "Analizza il testo fornito e identifica il capitolo più pertinente dalla seguente struttura gerarchica:\n\n"
    for part_id, part_data in KNOWLEDGE_BASE_STRUCTURE.items():
        prompt_text += f"--- {part_data['name']} ---\n"
        for chapter_id, chapter_name in part_data["chapters"].items():
            prompt_text += f"ID: {part_id}/{chapter_id} - {chapter_name}\n"
        prompt_text += "\n"
    prompt_text += "Rispondi SOLO con l'ID del capitolo più appropriato (es. P2_L_ASCESA_DEL_GENERE_HOMO/C05). Non aggiungere altro testo."
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
