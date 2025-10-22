# 🤖 Smart Suggestions & AI Assistance for Archivista AI
"""
AI-powered intelligent suggestion system that learns from user behavior
and provides personalized, contextual recommendations.

Features:
- Dynamic suggestion system based on user behavior patterns
- Intelligent document type detection and recommendations
- Personalized tips based on usage patterns
- Contextual prompts that adapt to user state
- Learning system that improves suggestions over time
"""

import streamlit as st
import pandas as pd
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import re

# --- USER BEHAVIOR ANALYZER ---

class UserBehaviorAnalyzer:
    """Analyzes user behavior patterns to provide personalized suggestions."""

    def __init__(self):
        self.behavior_key = "user_behavior_patterns"
        self.suggestions_key = "smart_suggestions_cache"

    def record_user_action(self, user_id: str, action: str, context: Dict[str, Any] = None):
        """Record a user action for behavior analysis."""
        if self.behavior_key not in st.session_state:
            st.session_state[self.behavior_key] = defaultdict(list)

        behavior_record = {
            'timestamp': datetime.now(),
            'action': action,
            'context': context or {},
            'session_id': st.session_state.get('current_session_id', 'unknown')
        }

        st.session_state[self.behavior_key][user_id].append(behavior_record)

        # Keep only last 1000 actions per user
        if len(st.session_state[self.behavior_key][user_id]) > 1000:
            st.session_state[self.behavior_key][user_id] = st.session_state[self.behavior_key][user_id][-1000:]

    def get_user_behavior_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of user behavior patterns."""
        if user_id not in st.session_state.get(self.behavior_key, {}):
            return {'action_counts': {}, 'patterns': [], 'preferences': {}}

        actions = st.session_state[self.behavior_key][user_id]

        # Analyze action frequencies
        action_counts = Counter(action['action'] for action in actions)

        # Find common patterns
        patterns = self._identify_patterns(actions)

        # Extract preferences
        preferences = self._extract_preferences(actions)

        return {
            'action_counts': dict(action_counts),
            'patterns': patterns,
            'preferences': preferences,
            'total_actions': len(actions),
            'first_action': actions[0]['timestamp'] if actions else None,
            'last_action': actions[-1]['timestamp'] if actions else None
        }

    def _identify_patterns(self, actions: List[Dict]) -> List[str]:
        """Identify common behavior patterns."""
        patterns = []

        # Pattern: Frequent document creation
        creation_actions = [a for a in actions if 'create' in a['action'] or 'new' in a['action']]
        if len(creation_actions) > 5:
            patterns.append("frequent_document_creator")

        # Pattern: Heavy chat user
        chat_actions = [a for a in actions if 'chat' in a['action'] or 'message' in a['action']]
        if len(chat_actions) > 10:
            patterns.append("heavy_chat_user")

        # Pattern: Archive explorer
        archive_actions = [a for a in actions if 'archive' in a['action'] or 'browse' in a['action']]
        if len(archive_actions) > 8:
            patterns.append("archive_explorer")

        # Pattern: Template user
        template_actions = [a for a in actions if 'template' in a['action']]
        if len(template_actions) > 3:
            patterns.append("template_user")

        return patterns

    def _extract_preferences(self, actions: List[Dict]) -> Dict[str, Any]:
        """Extract user preferences from behavior."""
        preferences = {}

        # Find preferred document types
        doc_type_actions = [a for a in actions if a['context'].get('document_type')]
        if doc_type_actions:
            doc_types = [a['context']['document_type'] for a in doc_type_actions]
            preferences['preferred_doc_types'] = Counter(doc_types).most_common(3)

        # Find preferred categories
        category_actions = [a for a in actions if a['context'].get('category')]
        if category_actions:
            categories = [a['context']['category'] for a in category_actions]
            preferences['preferred_categories'] = Counter(categories).most_common(3)

        # Find preferred times
        timestamps = [a['timestamp'] for a in actions]
        if len(timestamps) > 10:
            hours = [ts.hour for ts in timestamps]
            preferences['active_hours'] = Counter(hours).most_common(3)

        return preferences

# Global behavior analyzer
behavior_analyzer = UserBehaviorAnalyzer()

# --- INTELLIGENT DOCUMENT TYPE DETECTION ---

class DocumentTypeDetector:
    """AI-powered document type detection and recommendations."""

    def __init__(self):
        self.type_patterns = {
            'research_paper': {
                'keywords': ['abstract', 'introduction', 'methodology', 'results', 'conclusion', 'references'],
                'patterns': [r'\babstract\b', r'\bdoi\b', r'\bcitation', r'\breferences?\b'],
                'confidence': 0.8
            },
            'meeting_notes': {
                'keywords': ['meeting', 'agenda', 'participants', 'discussion', 'action items', 'decisions'],
                'patterns': [r'\bagenda\b', r'\bparticipants?\b', r'\baction items?\b'],
                'confidence': 0.9
            },
            'project_proposal': {
                'keywords': ['proposal', 'project', 'objectives', 'timeline', 'budget', 'deliverables'],
                'patterns': [r'\bobjectives?\b', r'\btimeline\b', r'\bdeliverables?\b'],
                'confidence': 0.85
            },
            'technical_documentation': {
                'keywords': ['api', 'function', 'parameter', 'return', 'example', 'code'],
                'patterns': [r'\bapi\b', r'\bfunction\b', r'\bparameter\b', r'\bexample\b'],
                'confidence': 0.75
            },
            'book_summary': {
                'keywords': ['chapter', 'author', 'plot', 'characters', 'themes', 'analysis'],
                'patterns': [r'\bchapter\b', r'\bauthor\b', r'\bplot\b', r'\bcharacters?\b'],
                'confidence': 0.7
            }
        }

    def detect_document_type(self, content: str, title: str = "", filename: str = "") -> Dict[str, Any]:
        """Detect document type using AI-powered analysis."""
        content_lower = (content + " " + title + " " + filename).lower()

        scores = {}

        for doc_type, patterns in self.type_patterns.items():
            score = 0
            matches = 0

            # Keyword matching
            for keyword in patterns['keywords']:
                if keyword.lower() in content_lower:
                    score += 1
                    matches += 1

            # Pattern matching
            for pattern in patterns['patterns']:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    score += 0.5
                    matches += 1

            # Calculate confidence
            if matches > 0:
                # Boost score for longer content (more context)
                length_bonus = min(0.3, len(content) / 10000)
                scores[doc_type] = (score + length_bonus) * patterns['confidence']

        # Return top 3 matches
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return {
            'primary_type': sorted_scores[0][0] if sorted_scores else 'general_document',
            'confidence': sorted_scores[0][1] if sorted_scores else 0,
            'all_scores': dict(sorted_scores[:3])
        }

    def get_type_recommendations(self, detected_type: str) -> Dict[str, Any]:
        """Get recommendations based on detected document type."""
        recommendations = {
            'research_paper': {
                'suggested_template': 'Nota ricerca',
                'suggested_category': 'P1_IL_PALCOSCENICO_COSMICO_E_BIOLOGICO/C01',
                'tips': [
                    'Usa la struttura: Abstract → Metodologia → Risultati → Conclusioni',
                    'Includi riferimenti bibliografici per credibilità',
                    'Aggiungi parole chiave per future ricerche'
                ]
            },
            'meeting_notes': {
                'suggested_template': 'Appunti riunione',
                'suggested_category': 'UNCATEGORIZED/C00',
                'tips': [
                    'Registra sempre data, partecipanti e moderatore',
                    'Separa chiaramente agenda, discussione e decisioni',
                    'Evidenzia gli action items per follow-up'
                ]
            },
            'project_proposal': {
                'suggested_template': 'Idea progetto',
                'suggested_category': 'P2_L_ASCESA_DEL_GENERE_HOMO/C04',
                'tips': [
                    'Definisci chiaramente obiettivi e deliverables',
                    'Includi timeline realistica e milestones',
                    'Specifica risorse necessarie e benefici attesi'
                ]
            },
            'technical_documentation': {
                'suggested_template': 'Documento vuoto',
                'suggested_category': 'UNCATEGORIZED/C00',
                'tips': [
                    'Includi esempi pratici di utilizzo',
                    'Documenta tutti i parametri e opzioni',
                    'Aggiungi sezione troubleshooting'
                ]
            },
            'book_summary': {
                'suggested_template': 'Riassunto libro',
                'suggested_category': 'P1_IL_PALCOSCENICO_COSMICO_E_BIOLOGICO/C01',
                'tips': [
                    'Includi contesto e background dell\'autore',
                    'Evidenzia temi principali e messaggi chiave',
                    'Aggiungi tue riflessioni personali'
                ]
            }
        }

        return recommendations.get(detected_type, {
            'suggested_template': 'Documento vuoto',
            'suggested_category': 'UNCATEGORIZED/C00',
            'tips': ['Struttura il contenuto con sezioni chiare', 'Includi informazioni chiave']
        })

# Global document type detector
doc_type_detector = DocumentTypeDetector()

# --- PERSONALIZED RECOMMENDATION ENGINE ---

class PersonalizedRecommendationEngine:
    """Generates personalized recommendations based on user behavior and context."""

    def __init__(self):
        self.recommendation_cache_key = "personalized_recommendations"

    def get_personalized_suggestions(self, user_id: str, current_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get personalized suggestions based on user behavior and current context."""
        behavior_summary = behavior_analyzer.get_user_behavior_summary(user_id)

        suggestions = []

        # Context-based suggestions
        current_page = current_context.get('current_page', '')
        has_documents = current_context.get('has_documents', False)

        # Personalized suggestions based on behavior patterns
        if 'frequent_document_creator' in behavior_summary['patterns']:
            suggestions.append({
                'type': 'action',
                'title': '🚀 Crea Nuovo Documento',
                'description': 'Basato sui tuoi pattern, sembri amare creare contenuti. Prova il nostro assistente guidato!',
                'action': 'create_document',
                'confidence': 0.9,
                'reasoning': 'L\'utente crea documenti frequentemente'
            })

        if 'heavy_chat_user' in behavior_summary['patterns']:
            suggestions.append({
                'type': 'feature',
                'title': '💬 Esplora Chat Avanzata',
                'description': 'Hai usato molto la chat. Prova le nostre sessioni avanzate con memoria persistente!',
                'action': 'explore_chat_features',
                'confidence': 0.85,
                'reasoning': 'L\'utente utilizza frequentemente la chat'
            })

        if 'archive_explorer' in behavior_summary['patterns']:
            suggestions.append({
                'type': 'feature',
                'title': '🔍 Scopri Funzionalità Avanzate',
                'description': 'Ti piace esplorare l\'archivio. Prova le operazioni batch e l\'esportazione avanzata!',
                'action': 'explore_batch_operations',
                'confidence': 0.8,
                'reasoning': 'L\'utente esplora frequentemente l\'archivio'
            })

        # Time-based suggestions
        if behavior_summary.get('preferences', {}).get('active_hours'):
            current_hour = datetime.now().hour
            active_hours = [hour for hour, count in behavior_summary['preferences']['active_hours']]

            if current_hour in active_hours:
                suggestions.append({
                    'type': 'tip',
                    'title': '⏰ Orario di Massima Produttività',
                    'description': f'Statisticamente sei più attivo intorno alle {current_hour}:00. Ottimo momento per creare contenuti!',
                    'action': 'productivity_tip',
                    'confidence': 0.7,
                    'reasoning': 'Suggerimento basato su pattern temporali'
                })

        # Document-based suggestions
        if has_documents and current_page == 'chat':
            suggestions.append({
                'type': 'query',
                'title': '🔍 Domanda Intelligente',
                'description': 'Basato sui tuoi documenti, prova a chiedere: "Quali sono i temi principali nei miei documenti recenti?"',
                'action': 'suggest_query',
                'confidence': 0.75,
                'reasoning': 'Suggerimento contestuale per utenti con documenti'
            })

        # Filter and sort by confidence
        suggestions = [s for s in suggestions if s['confidence'] > 0.6]
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)

        return suggestions[:5]  # Return top 5 suggestions

    def get_next_best_action(self, user_id: str, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest the next best action based on user journey."""
        behavior_summary = behavior_analyzer.get_user_behavior_summary(user_id)

        # New user journey
        if behavior_summary['total_actions'] < 5:
            return {
                'action': 'complete_onboarding',
                'title': '🎯 Completa l\'Onboarding',
                'description': 'Scopri tutte le funzionalità con il nostro tour guidato',
                'confidence': 0.95
            }

        # User with documents but low engagement
        if current_state.get('has_documents', False) and behavior_summary['patterns']:
            if 'frequent_document_creator' in behavior_summary['patterns']:
                return {
                    'action': 'try_chat',
                    'title': '💬 Prova la Chat AI',
                    'description': 'Hai creato molti documenti. Prova a far domande su di essi!',
                    'confidence': 0.85
                }

        # Advanced user suggestions
        if behavior_summary['total_actions'] > 50:
            return {
                'action': 'explore_advanced',
                'title': '🚀 Funzionalità Avanzate',
                'description': 'Scopri operazioni batch, esportazione e workflow avanzati',
                'confidence': 0.8
            }

        # Default suggestion
        return {
            'action': 'general_guidance',
            'title': '📚 Esplora l\'Archivio',
            'description': 'Scopri e organizza i tuoi documenti esistenti',
            'confidence': 0.6
        }

# Global recommendation engine
recommendation_engine = PersonalizedRecommendationEngine()

# --- CONTEXTUAL PROMPT GENERATOR ---

class ContextualPromptGenerator:
    """Generates contextual prompts based on user state and context."""

    def __init__(self):
        self.prompt_templates = {
            'empty_chat_with_docs': [
                'Analizza i temi principali nei tuoi documenti recenti',
                'Confronta documenti della stessa categoria',
                'Trova documenti correlati a "{recent_topic}"',
                'Quali sono gli autori più frequenti nei tuoi documenti?'
            ],
            'empty_chat_no_docs': [
                'Prima carica qualche documento per iniziare',
                'Crea il tuo primo documento con i template guidati',
                'Esplora la struttura di categorie disponibile'
            ],
            'empty_archive': [
                'Carica documenti nella cartella documenti_da_processare',
                'Crea documenti direttamente nell\'app',
                'Importa da fonti esterne'
            ],
            'after_document_creation': [
                'Fai domande sul documento appena creato',
                'Modifica l\'anteprima generata dall\'AI',
                'Condividi il documento con altri'
            ]
        }

    def generate_prompts(self, context: str, context_data: Dict[str, Any] = None) -> List[str]:
        """Generate contextual prompts for a given situation."""
        templates = self.prompt_templates.get(context, [])

        if not templates:
            return []

        prompts = []

        for template in templates:
            try:
                # Try to format with context data
                if context_data:
                    prompt = template.format(**context_data)
                else:
                    prompt = template
                prompts.append(prompt)
            except:
                # If formatting fails, use template as-is
                prompts.append(template)

        return prompts

    def get_smart_prompts(self, user_id: str, current_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get smart prompts based on user behavior and context."""
        context_key = current_context.get('context_key', 'general')
        context_data = current_context.get('context_data', {})

        # Generate base prompts
        base_prompts = self.generate_prompts(context_key, context_data)

        # Personalize based on user behavior
        behavior_summary = behavior_analyzer.get_user_behavior_summary(user_id)

        personalized_prompts = []

        for prompt in base_prompts:
            # Calculate relevance score
            relevance_score = self._calculate_prompt_relevance(prompt, behavior_summary, current_context)

            personalized_prompts.append({
                'prompt': prompt,
                'relevance_score': relevance_score,
                'category': self._categorize_prompt(prompt),
                'context': context_key
            })

        # Sort by relevance and return top prompts
        personalized_prompts.sort(key=lambda x: x['relevance_score'], reverse=True)

        return personalized_prompts[:4]

    def _calculate_prompt_relevance(self, prompt: str, behavior_summary: Dict, context: Dict) -> float:
        """Calculate how relevant a prompt is for the current user."""
        score = 0.5  # Base score

        # Boost score for user's preferred topics
        if 'preferred_categories' in behavior_summary.get('preferences', {}):
            user_categories = [cat for cat, count in behavior_summary['preferences']['preferred_categories']]
            prompt_lower = prompt.lower()

            for category in user_categories:
                if category.lower() in prompt_lower:
                    score += 0.2
                    break

        # Boost score for user's behavior patterns
        if 'frequent_document_creator' in behavior_summary.get('patterns', []):
            if any(word in prompt.lower() for word in ['crea', 'nuovo', 'documento']):
                score += 0.15

        if 'heavy_chat_user' in behavior_summary.get('patterns', []):
            if any(word in prompt.lower() for word in ['chiedi', 'domanda', 'analizza']):
                score += 0.15

        # Context relevance
        current_page = context.get('current_page', '')
        if current_page == 'chat' and 'chat' in prompt.lower():
            score += 0.1

        return min(1.0, score)  # Cap at 1.0

    def _categorize_prompt(self, prompt: str) -> str:
        """Categorize a prompt for better organization."""
        prompt_lower = prompt.lower()

        if any(word in prompt_lower for word in ['crea', 'nuovo', 'carica']):
            return 'creation'
        elif any(word in prompt_lower for word in ['chiedi', 'domanda', 'analizza']):
            return 'query'
        elif any(word in prompt_lower for word in ['confronta', 'relazioni']):
            return 'analysis'
        else:
            return 'general'

# Global prompt generator
prompt_generator = ContextualPromptGenerator()

# --- SMART SUGGESTION DISPLAY ---

def show_smart_suggestions(user_id: str, context: Dict[str, Any]):
    """Display smart suggestions based on user behavior and context."""
    st.markdown("### 💡 Suggerimenti Intelligenti")

    # Get personalized suggestions
    personalized_suggestions = recommendation_engine.get_personalized_suggestions(user_id, context)

    # Get smart prompts
    smart_prompts = prompt_generator.get_smart_prompts(user_id, context)

    # Combine and display
    all_suggestions = []

    # Add personalized suggestions
    for suggestion in personalized_suggestions:
        all_suggestions.append({
            'type': 'personalized',
            'title': suggestion['title'],
            'description': suggestion['description'],
            'confidence': suggestion['confidence'],
            'action': suggestion['action']
        })

    # Add smart prompts
    for prompt_data in smart_prompts:
        all_suggestions.append({
            'type': 'prompt',
            'title': '🎯 Suggerimento',
            'description': prompt_data['prompt'],
            'confidence': prompt_data['relevance_score'],
            'action': 'use_prompt',
            'prompt': prompt_data['prompt']
        })

    # Display suggestions
    if all_suggestions:
        for i, suggestion in enumerate(all_suggestions[:3]):  # Show top 3
            with st.expander(f"{suggestion['title']} ({suggestion['confidence']:.0%})", expanded=False):
                st.markdown(f"**{suggestion['description']}**")

                # Action button based on type
                if suggestion['type'] == 'prompt':
                    if st.button("📤 Usa questo suggerimento", key=f"smart_prompt_{i}"):
                        st.session_state.smart_suggestion = suggestion['prompt']
                        st.success(f"Suggerimento copiato! Incollalo nella chat.")
                else:
                    if st.button("🚀 Prova", key=f"smart_action_{i}"):
                        if suggestion['action'] == 'create_document':
                            st.switch_page("pages/4_Nuovo.py")
                        elif suggestion['action'] == 'try_chat':
                            st.switch_page("pages/1_Chat.py")
                        elif suggestion['action'] == 'explore_batch_operations':
                            st.switch_page("pages/7_Workflow_Wizards.py")
    else:
        st.info("💭 Nessun suggerimento intelligente disponibile al momento.")

# --- USAGE PATTERN ANALYZER ---

def analyze_and_show_insights(user_id: str):
    """Analyze user patterns and show insights."""
    behavior_summary = behavior_analyzer.get_user_behavior_summary(user_id)

    if behavior_summary['total_actions'] < 10:
        st.info("📊 Continuando a usare l'app, riceverai suggerimenti sempre più personalizzati!")
        return

    st.markdown("### 📈 I Tuoi Pattern di Utilizzo")

    # Show insights
    insights = []

    if 'frequent_document_creator' in behavior_summary['patterns']:
        insights.append("🎨 **Creatore di Contenuti**: Crei molti documenti - perfetto per sfruttare i nostri template!")

    if 'heavy_chat_user' in behavior_summary['patterns']:
        insights.append("💬 **Utilizzatore Chat**: Ami fare domande - prova le nostre funzionalità avanzate!")

    if 'archive_explorer' in behavior_summary['patterns']:
        insights.append("🔍 **Esploratore**: Ti piace organizzare - scopri le operazioni batch!")

    if behavior_summary.get('preferences', {}).get('active_hours'):
        active_hour = behavior_summary['preferences']['active_hours'][0][0]
        insights.append(f"⏰ **Orario Preferito**: Sei più attivo intorno alle {active_hour}:00")

    for insight in insights:
        st.markdown(f"• {insight}")

    # Show statistics
    with st.expander("📊 Statistiche Dettagliate", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.metric("📈 Azioni Totali", behavior_summary['total_actions'])
            if behavior_summary['first_action']:
                st.metric("🎯 Primo Utilizzo", behavior_summary['first_action'].strftime('%d/%m/%Y'))

        with col2:
            st.metric("🎭 Pattern Identificati", len(behavior_summary['patterns']))
            if behavior_summary['last_action']:
                st.metric("🕐 Ultima Attività", behavior_summary['last_action'].strftime('%d/%m/%Y'))

# --- INTEGRATION FUNCTIONS ---

def record_user_action(user_id: str, action: str, context: Dict[str, Any] = None):
    """Record a user action for behavior analysis."""
    behavior_analyzer.record_user_action(user_id, action, context)

def get_contextual_suggestions(user_id: str, current_page: str = "", has_documents: bool = False):
    """Get contextual suggestions for current user state."""
    context = {
        'current_page': current_page,
        'has_documents': has_documents,
        'context_key': f"{current_page}_{'with' if has_documents else 'no'}_docs"
    }

    return recommendation_engine.get_personalized_suggestions(user_id, context)

# --- MAIN SMART SUGGESTIONS INTERFACE ---

def render_smart_suggestions_page():
    """Main page for smart suggestions and AI assistance."""
    st.set_page_config(page_title="🤖 Smart Suggestions - Archivista AI", page_icon="🤖", layout="wide")

    st.title("🤖 Smart Suggestions & AI Assistance")
    st.caption("Suggerimenti intelligenti personalizzati basati sul tuo comportamento")

    # Check authentication
    if 'user_id' not in st.session_state or not st.session_state['user_id']:
        st.error("**Accesso Richiesto** 🔒")
        st.markdown("Devi essere loggato per vedere i suggerimenti personalizzati.")
        return

    user_id = st.session_state['user_id']

    # Record page visit
    record_user_action(user_id, 'viewed_smart_suggestions')

    # Show behavior insights
    analyze_and_show_insights(user_id)

    st.markdown("---")

    # Show smart suggestions
    try:
        papers_df = get_papers_dataframe()
        has_documents = not papers_df.empty
    except:
        has_documents = False

    context = {
        'current_page': 'smart_suggestions',
        'has_documents': has_documents,
        'context_key': 'smart_suggestions_page'
    }

    show_smart_suggestions(user_id, context)

# --- UTILITY FUNCTIONS ---

def get_papers_dataframe():
    """Get papers dataframe (imported from file_utils)."""
    from file_utils import get_papers_dataframe
    return get_papers_dataframe()

# Export main functions
__all__ = [
    'UserBehaviorAnalyzer',
    'behavior_analyzer',
    'DocumentTypeDetector',
    'doc_type_detector',
    'PersonalizedRecommendationEngine',
    'recommendation_engine',
    'ContextualPromptGenerator',
    'prompt_generator',
    'show_smart_suggestions',
    'record_user_action',
    'get_contextual_suggestions',
    'analyze_and_show_insights',
    'render_smart_suggestions_page'
]

if __name__ == "__main__":
    render_smart_suggestions_page()
