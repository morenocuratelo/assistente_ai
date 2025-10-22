# 🎯 Progressive Feature Disclosure System for Archivista AI
"""
System for gradually revealing advanced features based on user experience and behavior.

Features:
- Experience-based feature gating
- Adaptive interface complexity
- User proficiency tracking
- Gradual feature introduction
- Smart defaults based on user level
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

# --- USER PROFICIENCY LEVELS ---

class UserProficiencyLevel(Enum):
    """User proficiency levels for feature disclosure."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

# --- FEATURE DEFINITIONS ---

class FeatureDefinition:
    """Defines a feature and its disclosure rules."""

    def __init__(self, feature_id: str, name: str, description: str,
                 min_level: UserProficiencyLevel, trigger_conditions: Dict[str, Any],
                 dependencies: List[str] = None):
        self.feature_id = feature_id
        self.name = name
        self.description = description
        self.min_level = min_level
        self.trigger_conditions = trigger_conditions
        self.dependencies = dependencies or []

# --- PROFICIENCY TRACKER ---

class UserProficiencyTracker:
    """Tracks user proficiency and determines appropriate feature disclosure."""

    def __init__(self):
        self.proficiency_key = "user_proficiency_data"

    def calculate_proficiency_level(self, user_id: str) -> UserProficiencyLevel:
        """Calculate user's current proficiency level."""
        if user_id not in st.session_state.get(self.proficiency_key, {}):
            return UserProficiencyLevel.BEGINNER

        user_data = st.session_state[self.proficiency_key][user_id]

        # Calculate based on multiple factors
        total_actions = user_data.get('total_actions', 0)
        days_active = user_data.get('days_active', 0)
        features_used = len(user_data.get('features_used', set()))
        complex_operations = user_data.get('complex_operations_completed', 0)

        # Scoring algorithm
        score = 0

        # Action volume (0-30 points)
        score += min(30, total_actions / 10)

        # Days active (0-20 points)
        score += min(20, days_active * 2)

        # Feature diversity (0-25 points)
        score += min(25, features_used * 5)

        # Complex operations (0-25 points)
        score += min(25, complex_operations * 5)

        # Determine level
        if score >= 80:
            return UserProficiencyLevel.EXPERT
        elif score >= 60:
            return UserProficiencyLevel.ADVANCED
        elif score >= 30:
            return UserProficiencyLevel.INTERMEDIATE
        else:
            return UserProficiencyLevel.BEGINNER

    def update_proficiency_data(self, user_id: str, action: str, context: Dict[str, Any] = None):
        """Update proficiency tracking data."""
        if self.proficiency_key not in st.session_state:
            st.session_state[self.proficiency_key] = {}

        if user_id not in st.session_state[self.proficiency_key]:
            st.session_state[self.proficiency_key][user_id] = {
                'first_seen': datetime.now(),
                'total_actions': 0,
                'features_used': set(),
                'complex_operations_completed': 0,
                'last_activity': datetime.now(),
                'proficiency_history': []
            }

        user_data = st.session_state[self.proficiency_key][user_id]

        # Update counters
        user_data['total_actions'] += 1
        user_data['last_activity'] = datetime.now()

        # Track feature usage
        if context and 'feature' in context:
            user_data['features_used'].add(context['feature'])

        # Track complex operations
        complex_actions = ['batch_operation', 'advanced_search', 'workflow_wizard', 'custom_export']
        if action in complex_actions:
            user_data['complex_operations_completed'] += 1

        # Update days active
        days_active = (datetime.now() - user_data['first_seen']).days
        user_data['days_active'] = days_active

        # Store proficiency history
        current_level = self.calculate_proficiency_level(user_id)
        user_data['proficiency_history'].append({
            'timestamp': datetime.now(),
            'level': current_level.value,
            'total_actions': user_data['total_actions']
        })

        # Keep only last 30 history entries
        if len(user_data['proficiency_history']) > 30:
            user_data['proficiency_history'] = user_data['proficiency_history'][-30:]

    def get_available_features(self, user_id: str) -> List[str]:
        """Get list of features available to user based on proficiency."""
        current_level = self.calculate_proficiency_level(user_id)

        # Define feature availability by level
        feature_availability = {
            UserProficiencyLevel.BEGINNER: [
                'basic_chat', 'document_creation', 'simple_archive_view',
                'basic_help', 'welcome_modal'
            ],
            UserProficiencyLevel.INTERMEDIATE: [
                'basic_chat', 'document_creation', 'simple_archive_view',
                'basic_help', 'welcome_modal', 'advanced_templates',
                'archive_dashboard', 'export_basic', 'workflow_wizards_basic'
            ],
            UserProficiencyLevel.ADVANCED: [
                'basic_chat', 'document_creation', 'simple_archive_view',
                'basic_help', 'welcome_modal', 'advanced_templates',
                'archive_dashboard', 'export_basic', 'workflow_wizards_basic',
                'batch_operations', 'advanced_search', 'editor_advanced',
                'smart_suggestions', 'feedback_dashboard'
            ],
            UserProficiencyLevel.EXPERT: [
                'basic_chat', 'document_creation', 'simple_archive_view',
                'basic_help', 'welcome_modal', 'advanced_templates',
                'archive_dashboard', 'export_basic', 'workflow_wizards_basic',
                'batch_operations', 'advanced_search', 'editor_advanced',
                'smart_suggestions', 'feedback_dashboard', 'custom_workflows',
                'advanced_analytics', 'api_access', 'team_features'
            ]
        }

        return feature_availability.get(current_level, feature_availability[UserProficiencyLevel.BEGINNER])

# Global proficiency tracker
proficiency_tracker = UserProficiencyTracker()

# --- FEATURE DISCLOSURE MANAGER ---

class FeatureDisclosureManager:
    """Manages progressive disclosure of features."""

    def __init__(self):
        self.disclosure_key = "feature_disclosure_state"

    def should_show_feature(self, user_id: str, feature_id: str) -> bool:
        """Determine if a feature should be shown to user."""
        available_features = proficiency_tracker.get_available_features(user_id)
        return feature_id in available_features

    def get_feature_introduction_text(self, feature_id: str) -> str:
        """Get introduction text for a feature."""
        introductions = {
            'workflow_wizards_basic': "🎯 **Novità**: Scopri i Workflow Wizards per operazioni guidate!",
            'batch_operations': "⚡ **Funzionalità Avanzata**: Operazioni batch per lavorare su più documenti",
            'advanced_search': "🔍 **Ricerca Avanzata**: Costruisci query complesse con filtri sofisticati",
            'smart_suggestions': "🤖 **AI Personalizzata**: Suggerimenti intelligenti basati sul tuo utilizzo",
            'feedback_dashboard': "📊 **Monitoraggio**: Traccia lo stato di tutte le operazioni"
        }
        return introductions.get(feature_id, f"✨ **Nuova Funzionalità**: {feature_id}")

    def record_feature_interaction(self, user_id: str, feature_id: str, interaction_type: str):
        """Record user interaction with a feature."""
        proficiency_tracker.update_proficiency_data(user_id, f"used_{feature_id}", {'feature': feature_id})

    def show_feature_introduction(self, user_id: str, feature_id: str):
        """Show introduction for a newly available feature."""
        if not self.should_show_feature(user_id, feature_id):
            return False

        # Check if already shown
        shown_key = f"feature_intro_shown_{feature_id}_{user_id}"
        if st.session_state.get(shown_key, False):
            return False

        # Mark as shown
        st.session_state[shown_key] = True

        # Show introduction
        intro_text = self.get_feature_introduction_text(feature_id)

        @st.dialog(f"✨ Nuova Funzionalità Disponibile!")
        def feature_intro_dialog():
            st.markdown(intro_text)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Prova Subito", type="primary", use_container_width=True):
                    st.session_state[f"launch_feature_{feature_id}"] = True
                    st.rerun()

            with col2:
                if st.button("⏭️ Ricorda Dopo", use_container_width=True):
                    st.rerun()

        feature_intro_dialog()
        return True

# Global feature disclosure manager
feature_manager = FeatureDisclosureManager()

# --- ADAPTIVE INTERFACE COMPONENTS ---

def create_progressive_button(feature_id: str, label: str, help_text: str = "", button_type: str = "secondary"):
    """Create a button that shows progressively based on user level."""
    if 'user_id' not in st.session_state:
        return None

    user_id = st.session_state['user_id']

    if not feature_manager.should_show_feature(user_id, feature_id):
        return None

    # Record interaction when clicked
    if st.button(label, key=f"btn_{feature_id}", help=help_text, type=button_type, use_container_width=True):
        feature_manager.record_feature_interaction(user_id, feature_id, 'button_click')
        return True

    return False

def create_progressive_expander(feature_id: str, label: str, content_func: callable = None):
    """Create an expander that shows progressively based on user level."""
    if 'user_id' not in st.session_state:
        return

    user_id = st.session_state['user_id']

    if not feature_manager.should_show_feature(user_id, feature_id):
        return

    # Show introduction if newly available
    feature_manager.show_feature_introduction(user_id, feature_id)

    with st.expander(f"🔓 {label}", expanded=False):
        if content_func:
            content_func()
        else:
            st.info(f"Contenuto per {label}")

def show_user_proficiency_status(user_id: str):
    """Show user's current proficiency level and progress."""
    current_level = proficiency_tracker.calculate_proficiency_level(user_id)
    user_data = st.session_state.get('user_proficiency_data', {}).get(user_id, {})

    st.markdown("### 📊 Il Tuo Livello")

    # Level badge
    level_config = {
        UserProficiencyLevel.BEGINNER: {"icon": "🌱", "color": "#28a745", "name": "Principiante"},
        UserProficiencyLevel.INTERMEDIATE: {"icon": "🚀", "color": "#007bff", "name": "Intermedio"},
        UserProficiencyLevel.ADVANCED: {"icon": "⚡", "color": "#ffc107", "name": "Avanzato"},
        UserProficiencyLevel.EXPERT: {"icon": "👑", "color": "#dc3545", "name": "Esperto"}
    }

    level_info = level_config.get(current_level, level_config[UserProficiencyLevel.BEGINNER])

    st.markdown(f"""
    <div style="
        background-color: {level_info['color']};
        color: white;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    ">
        <h3>{level_info['icon']} {level_info['name']}</h3>
    </div>
    """, unsafe_allow_html=True)

    # Progress to next level
    next_level_thresholds = {
        UserProficiencyLevel.BEGINNER: 30,
        UserProficiencyLevel.INTERMEDIATE: 60,
        UserProficiencyLevel.ADVANCED: 80,
    }

    current_score = _calculate_proficiency_score(user_id)
    next_threshold = next_level_thresholds.get(current_level, 100)

    if current_level != UserProficiencyLevel.EXPERT:
        progress_to_next = min(1.0, current_score / next_threshold)
        st.progress(progress_to_next, text=f"Progresso verso {level_config.get(current_level, {}).get('name', 'Livello successivo')}")

        remaining = next_threshold - current_score
        st.caption(f"💡 **{remaining} punti** per raggiungere il livello successivo")

def _calculate_proficiency_score(user_id: str) -> int:
    """Calculate numerical proficiency score."""
    user_data = st.session_state.get('user_proficiency_data', {}).get(user_id, {})
    return (user_data.get('total_actions', 0) // 10) + (user_data.get('days_active', 0) * 2)

# --- FEATURE GATING DECORATOR ---

def requires_proficiency(min_level: UserProficiencyLevel):
    """Decorator for functions that require minimum proficiency level."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if 'user_id' not in st.session_state:
                st.error("Accesso richiesto per questa funzionalità")
                return None

            user_level = proficiency_tracker.calculate_proficiency_level(st.session_state['user_id'])

            if user_level.value >= min_level.value:
                return func(*args, **kwargs)
            else:
                # Show upgrade suggestion
                st.info(f"🔒 **Funzionalità Avanzata**: Questa funzione richiede il livello '{min_level.value}' o superiore.")
                st.info("💡 **Continua a usare l'app** per sbloccare funzionalità avanzate!")

                level_names = {
                    UserProficiencyLevel.BEGINNER: "Principiante",
                    UserProficiencyLevel.INTERMEDIATE: "Intermedio",
                    UserProficiencyLevel.ADVANCED: "Avanzato",
                    UserProficiencyLevel.EXPERT: "Esperto"
                }

                current_name = level_names.get(user_level, "Sconosciuto")
                required_name = level_names.get(min_level, "Sconosciuto")

                st.caption(f"📊 **Tuo livello attuale:** {current_name} → **Livello richiesto:** {required_name}")

                return None
        return wrapper
    return decorator

# --- ADAPTIVE INTERFACE BUILDER ---

def build_adaptive_interface(user_id: str, interface_config: Dict[str, Any]):
    """Build interface that adapts to user proficiency level."""
    current_level = proficiency_tracker.calculate_proficiency_level(user_id)

    st.markdown("### 🎛️ Impostazioni Interfaccia")

    # Show current level
    show_user_proficiency_status(user_id)

    # Adaptive options based on level
    if current_level == UserProficiencyLevel.BEGINNER:
        st.info("🌱 **Modalità Semplificata**: Stai vedendo l'interfaccia base ottimizzata per l'apprendimento.")

        if st.checkbox("🔍 Mostra Suggerimenti Avanzati", key="show_advanced_hints"):
            st.info("💡 **Suggerimento**: Prova a creare qualche documento per sbloccare funzionalità avanzate!")

    elif current_level == UserProficiencyLevel.INTERMEDIATE:
        st.success("🚀 **Modalità Intermedia**: Hai sbloccato funzionalità avanzate!")

        # Show available advanced features
        available_features = proficiency_tracker.get_available_features(user_id)
        advanced_features = [f for f in available_features if f not in [
            'basic_chat', 'document_creation', 'simple_archive_view', 'basic_help'
        ]]

        if advanced_features:
            st.markdown("**🔓 Funzionalità Sbloccate:**")
            for feature in advanced_features[:3]:  # Show first 3
                feature_manager.show_feature_introduction(user_id, feature)

    elif current_level == UserProficiencyLevel.ADVANCED:
        st.success("⚡ **Modalità Avanzata**: Hai accesso a tutte le funzionalità principali!")

        # Show expert features if available
        col1, col2 = st.columns(2)
        with col1:
            create_progressive_button("batch_operations", "⚡ Operazioni Batch", "Lavora su più documenti contemporaneamente")
        with col2:
            create_progressive_button("advanced_search", "🔍 Ricerca Avanzata", "Query complesse con filtri sofisticati")

    else:  # EXPERT
        st.success("👑 **Modalità Esperto**: Accesso completo a tutte le funzionalità!")

        # Show all advanced features
        st.markdown("**🎯 Funzionalità Esperto:**")

        expert_features = [
            ("⚡ Operazioni Batch", "batch_operations"),
            ("🔍 Ricerca Avanzata", "advanced_search"),
            ("📊 Analytics", "advanced_analytics"),
            ("🔧 API Access", "api_access")
        ]

        cols = st.columns(2)
        for i, (label, feature_id) in enumerate(expert_features):
            with cols[i % 2]:
                create_progressive_button(feature_id, label, f"Funzionalità esperto: {label}")

# --- INITIALIZATION ---

def init_progressive_disclosure(user_id: str):
    """Initialize progressive disclosure system for user."""
    if "progressive_disclosure_initialized" not in st.session_state:
        st.session_state.progressive_disclosure_initialized = True

        # Update proficiency data
        proficiency_tracker.update_proficiency_data(user_id, 'system_initialized')

# --- INTEGRATION HELPERS ---

def record_feature_usage(user_id: str, feature_id: str):
    """Record usage of a specific feature."""
    feature_manager.record_feature_interaction(user_id, feature_id, 'feature_used')
    proficiency_tracker.update_proficiency_data(user_id, f'used_{feature_id}', {'feature': feature_id})

def should_show_feature(user_id: str, feature_id: str) -> bool:
    """Check if feature should be shown to user."""
    return feature_manager.should_show_feature(user_id, feature_id)

# --- MAIN INTERFACE ---

def render_progressive_disclosure_page():
    """Main page for progressive feature disclosure management."""
    st.set_page_config(page_title="🎛️ Impostazioni Avanzate - Archivista AI", page_icon="🎛️", layout="wide")

    st.title("🎛️ Impostazioni Avanzate")
    st.caption("Gestisci le funzionalità disponibili e il tuo livello di accesso")

    if 'user_id' not in st.session_state or not st.session_state['user_id']:
        st.error("**Accesso Richiesto** 🔒")
        return

    user_id = st.session_state['user_id']

    # Initialize system
    init_progressive_disclosure(user_id)

    # Build adaptive interface
    build_adaptive_interface(user_id, {})

    # Show feature introduction for newly unlocked features
    available_features = proficiency_tracker.get_available_features(user_id)

    for feature in available_features[-3:]:  # Check last 3 features
        feature_manager.show_feature_introduction(user_id, feature)

# Export main functions
__all__ = [
    'UserProficiencyLevel',
    'FeatureDefinition',
    'UserProficiencyTracker',
    'proficiency_tracker',
    'FeatureDisclosureManager',
    'feature_manager',
    'create_progressive_button',
    'create_progressive_expander',
    'show_user_proficiency_status',
    'requires_proficiency',
    'build_adaptive_interface',
    'init_progressive_disclosure',
    'record_feature_usage',
    'should_show_feature',
    'render_progressive_disclosure_page'
]

if __name__ == "__main__":
    render_progressive_disclosure_page()
