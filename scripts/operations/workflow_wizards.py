# 🎯 Workflow Wizards for Archivista AI
"""
Interactive workflow wizards to guide users through complex multi-step processes.

This module provides step-by-step guided experiences for:
- Document upload and processing workflows
- Advanced search and query building
- Document editing workflows
- Batch operations wizards
- Knowledge discovery workflows
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

# --- BASE WIZARD FRAMEWORK ---

class WorkflowWizard:
    """Base class for creating interactive workflow wizards."""

    def __init__(self, title: str, description: str, steps: List[Dict[str, Any]]):
        self.title = title
        self.description = description
        self.steps = steps
        self.current_step = 0
        self.wizard_data = {}

    def render(self):
        """Render the complete wizard interface."""
        # Create session state keys for this wizard
        wizard_key = f"wizard_{self.title.lower().replace(' ', '_')}"

        if wizard_key not in st.session_state:
            st.session_state[wizard_key] = {
                'current_step': 0,
                'data': {},
                'completed': False
            }

        wizard_state = st.session_state[wizard_key]

        # Wizard header
        st.markdown(f"### 🎯 {self.title}")
        st.caption(self.description)

        # Progress indicator
        progress = wizard_state['current_step'] / len(self.steps)
        st.progress(progress, text=f"Passo {wizard_state['current_step'] + 1} di {len(self.steps)}")

        # Render current step
        if wizard_state['current_step'] < len(self.steps):
            step = self.steps[wizard_state['current_step']]
            self._render_step(step, wizard_state)
        else:
            self._render_completion(wizard_state)

    def _render_step(self, step: Dict[str, Any], wizard_state: Dict[str, Any]):
        """Render a single wizard step."""
        step_key = f"step_{wizard_state['current_step']}"

        st.markdown(f"#### 📋 {step['title']}")
        st.markdown(step['description'])

        # Render step content based on type
        if step['type'] == 'form':
            self._render_form_step(step, wizard_state)
        elif step['type'] == 'selection':
            self._render_selection_step(step, wizard_state)
        elif step['type'] == 'confirmation':
            self._render_confirmation_step(step, wizard_state)
        elif step['type'] == 'info':
            self._render_info_step(step, wizard_state)

        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if wizard_state['current_step'] > 0:
                if st.button("⬅️ Indietro", key=f"back_{wizard_state['current_step']}"):
                    wizard_state['current_step'] -= 1
                    st.rerun()

        with col2:
            if step.get('optional', False):
                if st.button("⏭️ Salta", key=f"skip_{wizard_state['current_step']}"):
                    wizard_state['current_step'] += 1
                    st.rerun()

        with col3:
            if st.button("▶️ Avanti", key=f"next_{wizard_state['current_step']}", type="primary"):
                if self._validate_step(step, wizard_state):
                    wizard_state['current_step'] += 1
                    st.rerun()

    def _render_form_step(self, step: Dict[str, Any], wizard_state: Dict[str, Any]):
        """Render a form input step."""
        for field in step['fields']:
            field_key = f"{wizard_state['current_step']}_{field['key']}"

            if field['type'] == 'text':
                wizard_state['data'][field['key']] = st.text_input(
                    field['label'],
                    value=wizard_state['data'].get(field['key'], field.get('default', '')),
                    key=field_key,
                    help=field.get('help', '')
                )
            elif field['type'] == 'select':
                wizard_state['data'][field['key']] = st.selectbox(
                    field['label'],
                    options=field['options'],
                    index=field['options'].index(wizard_state['data'].get(field['key'], field.get('default', field['options'][0]))) if wizard_state['data'].get(field['key']) in field['options'] else 0,
                    key=field_key,
                    help=field.get('help', '')
                )
            elif field['type'] == 'multiselect':
                wizard_state['data'][field['key']] = st.multiselect(
                    field['label'],
                    options=field['options'],
                    default=wizard_state['data'].get(field['key'], field.get('default', [])),
                    key=field_key,
                    help=field.get('help', '')
                )
            elif field['type'] == 'checkbox':
                wizard_state['data'][field['key']] = st.checkbox(
                    field['label'],
                    value=wizard_state['data'].get(field['key'], field.get('default', False)),
                    key=field_key,
                    help=field.get('help', '')
                )

    def _render_selection_step(self, step: Dict[str, Any], wizard_state: Dict[str, Any]):
        """Render a selection step."""
        options = step['options']
        selection_key = f"selection_{wizard_state['current_step']}"

        if step.get('display_mode', 'buttons') == 'buttons':
            # Button grid layout
            cols = st.columns(min(len(options), 3))
            for i, option in enumerate(options):
                with cols[i % 3]:
                    if st.button(
                        option['label'],
                        key=f"{selection_key}_{i}",
                        use_container_width=True,
                        help=option.get('description', '')
                    ):
                        wizard_state['data']['selection'] = option['value']
                        st.rerun()
        else:
            # Dropdown/radio selection
            option_labels = [opt['label'] for opt in options]
            current_selection = wizard_state['data'].get('selection', '')

            if step.get('multiple', False):
                selected_indices = [i for i, opt in enumerate(options) if opt['value'] in (current_selection if isinstance(current_selection, list) else [current_selection])]
                selected_labels = st.multiselect(
                    step['title'],
                    options=option_labels,
                    default=[option_labels[i] for i in selected_indices],
                    key=selection_key,
                    help=step.get('help', '')
                )
                wizard_state['data']['selection'] = [options[option_labels.index(label)]['value'] for label in selected_labels]
            else:
                default_index = 0
                for i, opt in enumerate(options):
                    if opt['value'] == current_selection:
                        default_index = i
                        break

                selected_label = st.selectbox(
                    step['title'],
                    options=option_labels,
                    index=default_index,
                    key=selection_key,
                    help=step.get('help', '')
                )
                wizard_state['data']['selection'] = options[option_labels.index(selected_label)]['value']

    def _render_confirmation_step(self, step: Dict[str, Any], wizard_state: Dict[str, Any]):
        """Render a confirmation step showing summary of choices."""
        st.markdown("**📋 Riepilogo delle tue scelte:**")

        # Show summary based on collected data
        for key, value in wizard_state['data'].items():
            if key != 'selection' or not isinstance(value, dict):
                st.info(f"**{key.title()}:** {value}")

        if st.checkbox("✅ Confermo queste impostazioni", key=f"confirm_{wizard_state['current_step']}"):
            wizard_state['confirmed'] = True

    def _render_info_step(self, step: Dict[str, Any], wizard_state: Dict[str, Any]):
        """Render an informational step."""
        st.info(step['content'])

        if step.get('action_text'):
            if st.button(step['action_text'], key=f"info_action_{wizard_state['current_step']}", type="primary"):
                if step.get('action_page'):
                    st.switch_page(step['action_page'])

    def _render_completion(self, wizard_state: Dict[str, Any]):
        """Render completion screen."""
        st.success("🎉 Workflow completato con successo!")

        # Show completion summary
        with st.expander("📋 Riepilogo workflow", expanded=True):
            st.json(wizard_state['data'])

        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Nuovo Workflow", key="new_workflow"):
                # Reset wizard state
                wizard_key = f"wizard_{self.title.lower().replace(' ', '_')}"
                if wizard_key in st.session_state:
                    del st.session_state[wizard_key]
                st.rerun()

        with col2:
            if st.button("🏠 Torna alla Home", key="home_after_wizard"):
                # Navigate to main page
                st.switch_page("pages/1_Chat.py")

    def _validate_step(self, step: Dict[str, Any], wizard_state: Dict[str, Any]) -> bool:
        """Validate current step before proceeding."""
        if step['type'] == 'confirmation':
            return wizard_state.get('data', {}).get('confirmed', False)

        # Add more validation logic as needed
        return True

# --- SPECIFIC WORKFLOW WIZARDS ---

def document_upload_wizard():
    """Wizard for guiding users through document upload and processing."""
    steps = [
        {
            'title': 'Tipo di Documento',
            'description': 'Che tipo di documento vuoi caricare?',
            'type': 'selection',
            'options': [
                {'label': '📄 Documento PDF', 'value': 'pdf', 'description': 'Documenti PDF scientifici o tecnici'},
                {'label': '📝 Documento Word', 'value': 'docx', 'description': 'Documenti Word (.docx)'},
                {'label': '📃 File di Testo', 'value': 'txt', 'description': 'File di testo semplice'},
                {'label': '📊 Presentazione', 'value': 'pptx', 'description': 'Presentazioni PowerPoint'}
            ]
        },
        {
            'title': 'Categoria e Metadati',
            'description': 'Aiutaci a organizzare il tuo documento',
            'type': 'form',
            'fields': [
                {
                    'key': 'title',
                    'label': 'Titolo del documento',
                    'type': 'text',
                    'default': '',
                    'help': 'Titolo descrittivo del documento'
                },
                {
                    'key': 'category',
                    'label': 'Categoria',
                    'type': 'select',
                    'options': ['P1_IL_PALCOSCENICO_COSMICO_E_BIOLOGICO/C01', 'P2_L_ASCESA_DEL_GENERE_HOMO/C04', 'UNCATEGORIZED/C00'],
                    'default': 'UNCATEGORIZED/C00',
                    'help': 'Categoria per organizzare il documento'
                },
                {
                    'key': 'year',
                    'label': 'Anno pubblicazione',
                    'type': 'text',
                    'default': str(datetime.now().year),
                    'help': 'Anno di pubblicazione o creazione'
                }
            ]
        },
        {
            'title': 'Opzioni di Processing',
            'description': 'Come vuoi che elaboriamo il documento?',
            'type': 'form',
            'fields': [
                {
                    'key': 'generate_preview',
                    'label': 'Genera anteprima automatica',
                    'type': 'checkbox',
                    'default': True,
                    'help': 'L\'AI crea automaticamente un riassunto del documento'
                },
                {
                    'key': 'extract_keywords',
                    'label': 'Estrai parole chiave',
                    'type': 'checkbox',
                    'default': True,
                    'help': 'Identifica automaticamente le parole chiave principali'
                },
                {
                    'key': 'priority',
                    'label': 'Priorità processamento',
                    'type': 'select',
                    'options': ['Normale', 'Alta', 'Bassa'],
                    'default': 'Normale',
                    'help': 'Priorità nella coda di processamento'
                }
            ]
        },
        {
            'title': 'Conferma Upload',
            'description': 'Verifica le impostazioni prima di procedere',
            'type': 'confirmation'
        }
    ]

    wizard = WorkflowWizard(
        "Caricamento Documenti Guidato",
        "Ti guidiamo passo dopo passo nel caricamento e processamento dei tuoi documenti",
        steps
    )

    wizard.render()
    return wizard

def advanced_search_wizard():
    """Wizard for building complex search queries."""
    steps = [
        {
            'title': 'Tipo di Ricerca',
            'description': 'Che tipo di ricerca vuoi effettuare?',
            'type': 'selection',
            'options': [
                {'label': '🔍 Ricerca per Parole Chiave', 'value': 'keywords', 'description': 'Cerca documenti contenenti parole specifiche'},
                {'label': '📚 Ricerca per Categoria', 'value': 'category', 'description': 'Esplora documenti per categoria tematica'},
                {'label': '👥 Ricerca per Autore', 'value': 'author', 'description': 'Trova documenti di autori specifici'},
                {'label': '🎯 Ricerca Avanzata', 'value': 'advanced', 'description': 'Ricerca complessa con filtri multipli'}
            ]
        },
        {
            'title': 'Parametri di Ricerca',
            'description': 'Configura i parametri della tua ricerca',
            'type': 'form',
            'fields': [
                {
                    'key': 'query',
                    'label': 'Termini di ricerca',
                    'type': 'text',
                    'default': '',
                    'help': 'Parole chiave o frase da cercare'
                },
                {
                    'key': 'category_filter',
                    'label': 'Filtra per categoria',
                    'type': 'select',
                    'options': ['Tutte', 'P1_IL_PALCOSCENICO_COSMICO_E_BIOLOGICO/C01', 'P2_L_ASCESA_DEL_GENERE_HOMO/C04', 'UNCATEGORIZED/C00'],
                    'default': 'Tutte',
                    'help': 'Limita la ricerca a categorie specifiche'
                },
                {
                    'key': 'year_range',
                    'label': 'Range anni',
                    'type': 'select',
                    'options': ['Tutti', 'Ultimo anno', 'Ultimi 5 anni', '2010-2020', '2000-2010'],
                    'default': 'Tutti',
                    'help': 'Filtra per periodo di pubblicazione'
                }
            ]
        },
        {
            'title': 'Opzioni Risultati',
            'description': 'Come vuoi visualizzare i risultati?',
            'type': 'form',
            'fields': [
                {
                    'key': 'max_results',
                    'label': 'Numero massimo risultati',
                    'type': 'select',
                    'options': ['10', '25', '50', '100'],
                    'default': '25',
                    'help': 'Numero di documenti da mostrare'
                },
                {
                    'key': 'sort_by',
                    'label': 'Ordina per',
                    'type': 'select',
                    'options': ['Rilevanza', 'Data', 'Titolo', 'Autore'],
                    'default': 'Rilevanza',
                    'help': 'Criterio di ordinamento dei risultati'
                },
                {
                    'key': 'show_previews',
                    'label': 'Mostra anteprime',
                    'type': 'checkbox',
                    'default': True,
                    'help': 'Includi anteprime generate dall\'AI'
                }
            ]
        },
        {
            'title': 'Avvia Ricerca',
            'description': 'Conferma e avvia la ricerca',
            'type': 'confirmation'
        }
    ]

    wizard = WorkflowWizard(
        "Ricerca Avanzata Guidata",
        "Costruisci query di ricerca complesse con l'aiuto del nostro assistente",
        steps
    )

    wizard.render()
    return wizard

def document_editing_wizard():
    """Wizard for guiding users through document editing workflows."""
    steps = [
        {
            'title': 'Selezione Documento',
            'description': 'Quale documento vuoi modificare?',
            'type': 'info',
            'content': 'Prima seleziona un documento dalla pagina Archivio o Chat per iniziare il processo di modifica.',
            'action_text': '📚 Vai all\'Archivio',
            'action_page': 'pages/2_Archivio.py'
        },
        {
            'title': 'Tipo di Modifica',
            'description': 'Cosa vuoi modificare?',
            'type': 'selection',
            'options': [
                {'label': '✏️ Modifica Anteprima', 'value': 'preview', 'description': 'Modifica il riassunto generato dall\'AI'},
                {'label': '🏷️ Aggiorna Metadati', 'value': 'metadata', 'description': 'Cambia titolo, autore, categoria'},
                {'label': '📝 Crea Nuova Versione', 'value': 'new_version', 'description': 'Crea un nuovo documento basato su questo'}
            ]
        },
        {
            'title': 'Configurazione Modifiche',
            'description': 'Configura le tue modifiche',
            'type': 'form',
            'fields': [
                {
                    'key': 'preserve_original',
                    'label': 'Mantieni versione originale',
                    'type': 'checkbox',
                    'default': True,
                    'help': 'Crea una copia invece di modificare l\'originale'
                },
                {
                    'key': 'notify_changes',
                    'label': 'Notifica modifiche',
                    'type': 'checkbox',
                    'default': False,
                    'help': 'Invia notifica quando le modifiche sono complete'
                }
            ]
        },
        {
            'title': 'Conferma Modifiche',
            'description': 'Verifica le impostazioni prima di procedere',
            'type': 'confirmation'
        }
    ]

    wizard = WorkflowWizard(
        "Modifica Documenti Guidata",
        "Ti guidiamo attraverso il processo di modifica dei tuoi documenti",
        steps
    )

    wizard.render()
    return wizard

def batch_operations_wizard():
    """Wizard for batch operations on multiple documents."""
    steps = [
        {
            'title': 'Selezione Documenti',
            'description': 'Quali documenti vuoi processare in batch?',
            'type': 'info',
            'content': 'Seleziona prima i documenti nella pagina Archivio usando le checkbox, poi torna qui.',
            'action_text': '📚 Seleziona Documenti',
            'action_page': 'pages/2_Archivio.py'
        },
        {
            'title': 'Tipo di Operazione',
            'description': 'Che operazione vuoi eseguire sui documenti selezionati?',
            'type': 'selection',
            'options': [
                {'label': '🏷️ Applica Categoria', 'value': 'set_category', 'description': 'Assegna stessa categoria a tutti'},
                {'label': '👥 Aggiungi Autore', 'value': 'add_author', 'description': 'Aggiungi autore a tutti i documenti'},
                {'label': '📅 Imposta Anno', 'value': 'set_year', 'description': 'Imposta anno di pubblicazione'},
                {'label': '🤖 Rigenera Anteprime', 'value': 'regenerate_previews', 'description': 'Rigenera anteprime AI'},
                {'label': '📊 Estrai Statistiche', 'value': 'extract_stats', 'description': 'Estrai statistiche dai documenti'}
            ]
        },
        {
            'title': 'Configurazione Batch',
            'description': 'Configura i parametri dell\'operazione batch',
            'type': 'form',
            'fields': [
                {
                    'key': 'new_category',
                    'label': 'Nuova categoria',
                    'type': 'select',
                    'options': ['P1_IL_PALCOSCENICO_COSMICO_E_BIOLOGICO/C01', 'P2_L_ASCESA_DEL_GENERE_HOMO/C04', 'UNCATEGORIZED/C00'],
                    'default': 'UNCATEGORIZED/C00'
                },
                {
                    'key': 'author_name',
                    'label': 'Nome autore',
                    'type': 'text',
                    'default': ''
                },
                {
                    'key': 'publication_year',
                    'label': 'Anno pubblicazione',
                    'type': 'text',
                    'default': str(datetime.now().year)
                }
            ]
        },
        {
            'title': 'Conferma Operazione',
            'description': 'Verifica le impostazioni prima di eseguire l\'operazione batch',
            'type': 'confirmation'
        }
    ]

    wizard = WorkflowWizard(
        "Operazioni Batch Guidate",
        "Esegui operazioni su più documenti contemporaneamente in modo sicuro",
        steps
    )

    wizard.render()
    return wizard

# --- WIZARD SELECTION INTERFACE ---

def show_workflow_wizards_hub():
    """Main hub for accessing all workflow wizards."""
    st.markdown("### 🎯 Workflow Wizards")
    st.caption("Guide interattive per processi complessi")

    # Available wizards
    wizards = [
        {
            'title': '📤 Caricamento Documenti',
            'description': 'Ti guida nel caricamento e processamento ottimale dei documenti',
            'function': document_upload_wizard,
            'icon': '📤'
        },
        {
            'title': '🔍 Ricerca Avanzata',
            'description': 'Costruisci query di ricerca complesse passo dopo passo',
            'function': advanced_search_wizard,
            'icon': '🔍'
        },
        {
            'title': '✏️ Modifica Documenti',
            'description': 'Ti guida attraverso il processo di modifica dei documenti',
            'function': document_editing_wizard,
            'icon': '✏️'
        },
        {
            'title': '⚡ Operazioni Batch',
            'description': 'Esegui operazioni su più documenti in modo sicuro e guidato',
            'function': batch_operations_wizard,
            'icon': '⚡'
        }
    ]

    # Display wizard cards
    cols = st.columns(2)
    for i, wizard in enumerate(wizards):
        with cols[i % 2]:
            with st.container():
                st.markdown(f"**{wizard['icon']} {wizard['title']}**")
                st.caption(wizard['description'])

                if st.button(
                    "🚀 Avvia Wizard",
                    key=f"wizard_{wizard['title'].lower().replace(' ', '_')}",
                    use_container_width=True,
                    type="secondary"
                ):
                    st.session_state.current_wizard = wizard['function']
                    st.rerun()

    # Render active wizard if selected
    if 'current_wizard' in st.session_state:
        st.markdown("---")
        st.session_state.current_wizard()

        # Exit wizard button
        if st.button("❌ Esci dal Wizard", key="exit_wizard"):
            del st.session_state.current_wizard
            st.rerun()

# --- UTILITY FUNCTIONS ---

def get_wizard_progress(wizard_name: str) -> Dict[str, Any]:
    """Get progress data for a specific wizard."""
    wizard_key = f"wizard_{wizard_name.lower().replace(' ', '_')}"
    return st.session_state.get(wizard_key, {'current_step': 0, 'data': {}, 'completed': False})

def reset_wizard(wizard_name: str):
    """Reset a wizard to initial state."""
    wizard_key = f"wizard_{wizard_name.lower().replace(' ', '_')}"
    if wizard_key in st.session_state:
        del st.session_state[wizard_key]

# --- MAIN INTERFACE ---

def render_workflow_wizards_page():
    """Main page for workflow wizards."""
    st.set_page_config(page_title="🎯 Workflow Wizards - Archivista AI", page_icon="🎯", layout="wide")
    st.title("🎯 Workflow Wizards")
    st.caption("Guide interattive per sfruttare al meglio Archivista AI")

    # Show wizards hub
    show_workflow_wizards_hub()

# Export main functions
__all__ = [
    'WorkflowWizard',
    'document_upload_wizard',
    'advanced_search_wizard',
    'document_editing_wizard',
    'batch_operations_wizard',
    'show_workflow_wizards_hub',
    'render_workflow_wizards_page'
]

if __name__ == "__main__":
    render_workflow_wizards_page()
