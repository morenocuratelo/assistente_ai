# 🤖 Smart Suggestions Page - AI-Powered Personalization
"""
Dedicated page for AI-powered smart suggestions and personalized assistance.

This page provides:
- Behavior analysis and insights
- Personalized recommendations
- Intelligent document type detection
- Contextual prompts based on usage patterns
- Learning system that adapts to user preferences
"""

import streamlit as st
from smart_suggestions import (
    analyze_and_show_insights,
    show_smart_suggestions,
    record_user_action,
    get_papers_dataframe,
    recommendation_engine
)

def main():
    """Main function for the Smart Suggestions page."""
    st.set_page_config(page_title="🤖 Smart Suggestions - Archivista AI", page_icon="🤖", layout="wide")

    st.title("🤖 Smart Suggestions & AI Assistance")
    st.caption("Suggerimenti intelligenti personalizzati basati sul tuo comportamento e preferenze")

    # Check authentication
    if 'user_id' not in st.session_state or not st.session_state['user_id']:
        st.error("**Accesso Richiesto** 🔒")
        st.markdown("Devi essere loggato per vedere i suggerimenti personalizzati.")
        if st.button("🔐 Vai al Login"):
            st.switch_page("pages/login.py")
        return

    user_id = st.session_state['user_id']

    # Record page visit for behavior analysis
    record_user_action(user_id, 'viewed_smart_suggestions_page')

    # Show introduction
    st.markdown("""
    ### 🧠 Come Funziona l'AI

    Il nostro sistema di suggerimenti intelligenti impara dal tuo comportamento per offrirti:

    - **🎯 Suggerimenti Personalizzati** basati sui tuoi pattern di utilizzo
    - **📋 Prompts Contestuali** adattati alla tua situazione attuale
    - **🎨 Template Intelligenti** raccomandati per il tuo tipo di contenuto
    - **⏰ Orari Ottimali** per le tue attività più produttive

    Più usi l'app, più i suggerimenti diventano accurati e utili!
    """)

    # Analyze and show user insights
    analyze_and_show_insights(user_id)

    st.markdown("---")

    # Show current smart suggestions
    try:
        papers_df = get_papers_dataframe()
        has_documents = not papers_df.empty
    except:
        has_documents = False

    # Determine context for suggestions
    context = {
        'current_page': 'smart_suggestions',
        'has_documents': has_documents,
        'context_key': 'smart_suggestions_page'
    }

    show_smart_suggestions(user_id, context)

    # Show next best action
    st.markdown("---")
    st.markdown("### 🎯 Prossima Azione Consigliata")

    next_action = recommendation_engine.get_next_best_action(user_id, {
        'has_documents': has_documents,
        'total_actions': len(st.session_state.get('user_behavior_patterns', {}).get(user_id, []))
    })

    st.info(f"**{next_action['title']}**")
    st.caption(next_action['description'])

    if st.button("🚀 Segui Suggerimento", key="next_action_button", type="primary"):
        if next_action['action'] == 'complete_onboarding':
            st.switch_page("pages/1_Chat.py")  # Will trigger welcome modal
        elif next_action['action'] == 'try_chat':
            st.switch_page("pages/1_Chat.py")
        elif next_action['action'] == 'explore_advanced':
            st.switch_page("pages/7_Workflow_Wizards.py")

    # Show learning progress
    st.markdown("---")
    st.markdown("### 📊 Apprendimento AI")

    behavior_data = st.session_state.get('user_behavior_patterns', {}).get(user_id, [])
    total_actions = len(behavior_data)

    if total_actions < 10:
        st.info("🌱 **In Apprendimento**: L'AI sta ancora imparando i tuoi pattern. Continuando a usare l'app, i suggerimenti miglioreranno!")
    elif total_actions < 50:
        st.success("🚀 **Apprendimento Attivo**: L'AI ha identificato alcuni tuoi pattern e sta affinando i suggerimenti.")
    else:
        st.success("🎯 **Completamente Personalizzato**: L'AI conosce bene i tuoi pattern e offre suggerimenti altamente personalizzati!")

    # Progress bar for AI learning
    learning_progress = min(1.0, total_actions / 100)  # 100 actions for "fully trained"
    st.progress(learning_progress, text=f"Apprendimento AI: {learning_progress:.1%}")

if __name__ == "__main__":
    main()
