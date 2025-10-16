import streamlit as st
import pandas as pd
import json
import networkx as nx
from streamlit.components.v1 import html
from file_utils import get_user_knowledge_graph, get_entity_neighbors
# Import delle funzioni Bayesian per la visualizzazione della confidenza
from knowledge_structure import (
    get_confidence_color,
    get_confidence_label,
    get_entities_by_confidence,
    get_relationships_by_confidence,
    get_confidence_statistics
)
from bayesian_inference_engine import create_inference_engine

# --- HELPER FUNCTIONS FOR BAYESIAN VISUALIZATION ---

def get_confidence_emoji(confidence_score: float) -> str:
    """Restituisce un'emoji rappresentativa del punteggio di confidenza."""
    if confidence_score >= 0.8:
        return "🟢"  # Verde - alta confidenza
    elif confidence_score >= 0.6:
        return "🟡"  # Giallo - confidenza media
    elif confidence_score >= 0.3:
        return "🟠"  # Arancione - bassa confidenza
    else:
        return "🔴"  # Rosso - molto bassa confidenza

def get_evidence_emoji(evidence_type: str) -> str:
    """Restituisce un'emoji rappresentativa del tipo di prova."""
    emoji_map = {
        'document_extraction': '📄',
        'user_feedback_positive': '👍',
        'user_feedback_negative': '👎',
        'corroboration': '🔗',
        'contradiction': '❌',
        'temporal_decay': '🕐',
        'cross_reference': '🔄',
        'authority_endorsement': '👑'
    }
    return emoji_map.get(evidence_type, '📝')

def create_confidence_gauge(confidence_score: float) -> str:
    """Crea una rappresentazione visuale a gauge del punteggio di confidenza."""
    filled = int(confidence_score * 10)
    empty = 10 - filled
    gauge = "🟢" * filled + "⚪" * empty
    return f"{gauge} {confidence_score:.1%}"

def get_entity_confidence_badge(entity) -> str:
    """Crea un badge visuale per l'entità basato sulla confidenza."""
    confidence = entity.get('confidence_score', 0.5)
    color = get_confidence_color(confidence)
    label = get_confidence_label(confidence)

    # Crea un badge HTML-style
    return f"""
    <div style="
        display: inline-block;
        padding: 2px 8px;
        margin: 2px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
        color: white;
        background: linear-gradient(135deg, {color}, {color}dd);
        border: 1px solid {color};
    ">
        {label}
    </div>
    """

# --- AUTHENTICATION CHECK ---
if 'user_id' not in st.session_state or not st.session_state['user_id']:
    st.error("🚫 Accesso negato. Effettua prima il login.")
    st.stop()

user_id = st.session_state['user_id']
username = st.session_state.get('username', 'User')

# --- PAGE CONFIG ---
st.title("🧠 Grafo della Conoscenza")
st.markdown(f"**Benvenuto, {username}!** Esplora le connessioni concettuali estratte dai tuoi documenti accademici.")

# --- LOAD KNOWLEDGE GRAPH ---
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_knowledge_graph(user_id):
    """Load knowledge graph with caching for performance"""
    return get_user_knowledge_graph(user_id)

graph_data = load_knowledge_graph(user_id)

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🔍 Controlli Grafo")

# Bayesian Confidence Controls
st.sidebar.subheader("🎯 Filtri Confidenza")

# Confidence threshold slider
min_confidence = st.sidebar.slider(
    "Confidenza Minima",
    min_value=0.0,
    max_value=1.0,
    value=0.3,
    step=0.1,
    help="Mostra solo entità e relazioni con confidenza >= valore selezionato"
)

# Confidence statistics toggle
show_confidence_stats = st.sidebar.checkbox("📊 Mostra Statistiche Confidenza", value=True)

# Entity type filter
entity_types = ["All"] + sorted(list(set([e['entity_type'] for e in graph_data['entities']])))
selected_entity_type = st.sidebar.selectbox("Tipo Entità", entity_types)

# Selected entity for neighborhood view
if graph_data['entities']:
    entity_options = ["Nessuna selezione (grafo completo)"] + sorted([e['entity_name'] for e in graph_data['entities']])
    selected_entity = st.sidebar.selectbox("Entità Focalizzata", entity_options)

    if st.sidebar.button("🧲 Mostra Vicini"):
        if selected_entity != "Nessuna selezione (grafo completo)":
            st.sidebar.subheader("Entità Connesse")
            neighbors_data = get_entity_neighbors(user_id, selected_entity)
            for relation in neighbors_data['relationships'][:10]:  # Show max 10
                other_entity = relation['target_name'] if relation['source_name'] == selected_entity else relation['source_name']
                confidence_emoji = get_confidence_emoji(relation.get('confidence_score', 0.5))
                st.sidebar.write(f"• {other_entity} ({relation['relationship_type']}) {confidence_emoji}")

# Evidence history for selected entity
if selected_entity and selected_entity != "Nessuna selezione (grafo completo)":
    st.sidebar.subheader("📋 Cronologia Prove")
    selected_entity_data = next((e for e in graph_data['entities'] if e['entity_name'] == selected_entity), None)
    if selected_entity_data:
        from file_utils import get_entity_evidence_history
        evidence_history = get_entity_evidence_history(selected_entity_data['id'], limit=5)

        if evidence_history:
            for evidence in evidence_history:
                evidence_emoji = get_evidence_emoji(evidence['evidence_type'])
                st.sidebar.caption(f"{evidence_emoji} {evidence['evidence_description'][:30]}...")
                st.sidebar.caption(f"📅 {evidence['created_at'][:10]} | 💪 {evidence['evidence_strength']:.2f}")
        else:
            st.sidebar.info("Nessuna prova registrata")

# --- MAIN CONTENT ---

if not graph_data['entities']:
    st.info("🎯 **Nessuna entità trovata!**")
    st.markdown("""
    Il grafo della conoscenza si popola automaticamente quando carichi documenti accademici.

    **Come funziona:**
    1. Carica documenti (PDF, DOCX, ecc.) nella sezione Archivio
    2. Mentre vengono processati, l'AI estrae automaticamente:
       - **Concetti**: Idee principali e teorie
       - **Relazioni**: Come i concetti sono collegati
       - **Autori**: Contributi degli scienziati
       - **Formule**: Equazioni matematiche
    3. Torna qui per esplorare le connessioni!

    💡 **Prova con documenti scientifici o accademici per risultati migliori.**
    """)
else:
    # Statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        entities_count = len(graph_data['entities'])
        st.metric("🔵 Entità", entities_count)

    with col2:
        relationships_count = len(graph_data['relationships'])
        st.metric("🔗 Relazioni", relationships_count)

    with col3:
        entity_types = len(set([e['entity_type'] for e in graph_data['entities']]))
        st.metric("🏷️ Tipi Entità", entity_types)

    with col4:
        sources_count = len(set([e['source_file_name'] for e in graph_data['entities']]))
        st.metric("📄 Documenti Sorgente", sources_count)

    # Bayesian Confidence Statistics
    if show_confidence_stats:
        st.subheader("📊 Statistiche Confidenza")

        # Get confidence statistics
        confidence_stats = get_confidence_statistics(user_id)

        if confidence_stats['summary']['total_knowledge_items'] > 0:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                avg_confidence = confidence_stats['summary']['avg_confidence']
                st.metric(
                    "🎯 Confidenza Media",
                    f"{avg_confidence:.2f}",
                    help="Punteggio medio di confidenza di tutte le entità e relazioni"
                )

            with col2:
                high_confidence_ratio = confidence_stats['summary']['high_confidence_ratio']
                st.metric(
                    "🟢 Alta Confidenza",
                    f"{high_confidence_ratio:.1%}",
                    help="Percentuale di elementi con confidenza >= 0.8"
                )

            with col3:
                total_items = confidence_stats['summary']['total_knowledge_items']
                st.metric(
                    "📈 Elementi Totali",
                    total_items,
                    help="Totale entità + relazioni nel grafo della conoscenza"
                )

            with col4:
                # Calculate confidence trend (mock for now)
                confidence_trend = "📈 Stabile"
                st.metric(
                    "📊 Trend",
                    confidence_trend,
                    help="Evoluzione recente dei punteggi di confidenza"
                )

            # Confidence distribution chart
            st.write("**📊 Distribuzione Confidenza**")

            # Create simple bar chart data
            high_conf = confidence_stats['entities']['high_confidence'] + confidence_stats['relationships']['high_confidence']
            med_conf = confidence_stats['entities']['medium_confidence'] + confidence_stats['relationships']['medium_confidence']
            low_conf = confidence_stats['entities']['low_confidence'] + confidence_stats['relationships']['low_confidence']

            chart_data = pd.DataFrame({
                'Livello': ['Alta (≥0.8)', 'Media (0.6-0.8)', 'Bassa (<0.6)'],
                'Conteggio': [high_conf, med_conf, low_conf]
            })

            st.bar_chart(chart_data.set_index('Livello'))

            # Confidence insights
            st.info(f"""
            💡 **Insight sulla Confidenza:**
            - **{high_conf} elementi** hanno alta affidabilità (≥80% confidenza)
            - **{med_conf} elementi** hanno confidenza media (60-80%)
            - **{low_conf} elementi** necessitano più prove (<60% confidenza)
            - **Confidenza complessiva**: {avg_confidence:.1%} - {'Eccellente' if avg_confidence >= 0.8 else 'Buona' if avg_confidence >= 0.6 else 'Da migliorare'}
            """)
        else:
            st.info("📊 Nessun dato di confidenza disponibile. Carica documenti per iniziare!")

    st.divider()

    # Apply confidence filtering
    filtered_entities = [e for e in graph_data['entities'] if e.get('confidence_score', 0) >= min_confidence]
    filtered_relationships = [r for r in graph_data['relationships'] if r.get('confidence_score', 0) >= min_confidence]

    # Show filtering results
    if min_confidence > 0.0:
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"🔍 **Filtro Attivo**: Confidenza ≥ {min_confidence:.1%}")
        with col2:
            st.info(f"📊 **Risultati**: {len(filtered_entities)} entità, {len(filtered_relationships)} relazioni")

    # Filter entities by type (applied after confidence filtering)
    if selected_entity_type != "All":
        filtered_entities = [e for e in filtered_entities if e['entity_type'] == selected_entity_type]

    # Entità per Tipo
    st.subheader("🏷️ Entità per Tipo")

    entity_type_counts = {}
    for entity in graph_data['entities']:
        entity_type = entity['entity_type']
        if entity_type not in entity_type_counts:
            entity_type_counts[entity_type] = []
        entity_type_counts[entity_type].append(entity)

    # Display entity type sections
    for entity_type, entities in entity_type_counts.items():
        if selected_entity_type == "All" or selected_entity_type == entity_type:
            with st.expander(f"📂 {entity_type.title()} ({len(entities)})", expanded=(len(entities) < 20)):
                st.write(f"**{len(entities)} entità di tipo '{entity_type}'**")

                # Group by source file for better organization
                entities_by_source = {}
                for entity in entities:
                    source = entity['source_file_name']
                    if source not in entities_by_source:
                        entities_by_source[source] = []
                    entities_by_source[source].append(entity)

                for source_file, source_entities in entities_by_source.items():
                    st.write(f"**Documento: {source_file}**")

                    # Sort entities by confidence (highest first)
                    sorted_entities = sorted(source_entities, key=lambda x: x.get('confidence_score', 0), reverse=True)

                    for i, entity in enumerate(sorted_entities):
                        confidence_score = entity.get('confidence_score', 0.5)
                        confidence_emoji = get_confidence_emoji(confidence_score)
                        confidence_gauge = create_confidence_gauge(confidence_score)
                        confidence_label = get_confidence_label(confidence_score)

                        # Create expandable entity card
                        with st.expander(f"{i+1}. {entity['entity_name']} {confidence_emoji}", expanded=False):
                            col1, col2 = st.columns([0.7, 0.3])

                            with col1:
                                st.markdown(f"""
                                **📝 Descrizione:** {entity.get('entity_description', 'Nessuna descrizione disponibile')}

                                **🎯 Confidenza:** {confidence_gauge}
                                **🏷️ Livello:** {confidence_label}
                                **📄 Fonte:** {entity.get('source_file_name', 'Sconosciuta')}
                                **⏰ Creato:** {entity.get('created_at', 'N/A')[:10] if entity.get('created_at') else 'N/A'}
                                """)

                            with col2:
                                # Confidence meter visualization
                                st.markdown("**📊 Misuratore**")
                                st.progress(confidence_score, text=f"{confidence_score:.1%}")

                                # Quick action buttons
                                entity_id = entity.get('id')
                                if entity_id:
                                    col_a, col_b = st.columns(2)
                                    with col_a:
                                        if st.button("👍", key=f"like_{entity_id}", help="Conferma questa entità"):
                                            # Process positive feedback
                                            from archivista_processing import process_user_feedback_bayesian_task
                                            process_user_feedback_bayesian_task.delay(
                                                user_id=user_id,
                                                target_type="entity",
                                                target_id=entity_id,
                                                feedback_type="positive",
                                                feedback_text=f"Confermato: {entity['entity_name']}"
                                            )
                                            st.success("Feedback registrato!")
                                            st.rerun()

                                    with col_b:
                                        if st.button("👎", key=f"dislike_{entity_id}", help="Correggi questa entità"):
                                            # Process negative feedback
                                            process_user_feedback_bayesian_task.delay(
                                                user_id=user_id,
                                                target_type="entity",
                                                target_id=entity_id,
                                                feedback_type="negative",
                                                feedback_text=f"Correzione richiesta: {entity['entity_name']}"
                                            )
                                            st.warning("Feedback registrato!")

                    st.divider()

    # Relazioni
    st.subheader("🔗 Relazioni Concettuali")

    if filtered_relationships:
        st.write(f"**{len(filtered_relationships)} relazioni trovate**")

        # Enhanced relationships display with confidence visualization
        relationships_data = []
        for rel in filtered_relationships[:100]:  # Limit to 100 for performance
            confidence_score = rel.get('confidence_score', 0.5)
            confidence_emoji = get_confidence_emoji(confidence_score)
            confidence_gauge = create_confidence_gauge(confidence_score)

            relationships_data.append({
                "Da": f"{rel['source_name']} ({rel['source_type']})",
                "Relazione": rel['relationship_type'].replace('_', ' ').title(),
                "A": f"{rel['target_name']} ({rel['target_type']})",
                "Confidenza": confidence_gauge,
                "Livello": get_confidence_label(confidence_score),
                "Documento": rel.get('source_file_name', 'N/A')
            })

        if relationships_data:
            # Create enhanced dataframe with confidence styling
            rel_df = pd.DataFrame(relationships_data)

            st.dataframe(rel_df, use_container_width=True,
                        column_config={
                            "Da": st.column_config.TextColumn("Entità Sorgente", width="medium"),
                            "Relazione": st.column_config.TextColumn("Tipo Relazione", width="medium"),
                            "A": st.column_config.TextColumn("Entità Destinazione", width="medium"),
                            "Confidenza": st.column_config.TextColumn("Confidenza", width="medium"),
                            "Livello": st.column_config.TextColumn("Livello", width="small"),
                            "Documento": st.column_config.TextColumn("Fonte", width="medium")
                        })

        # Interactive confidence-based exploration
        st.subheader("🎯 Esplorazione Interattiva")

        # Confidence-based entity clustering
        if filtered_entities:
            # Group entities by confidence levels
            high_confidence = [e for e in filtered_entities if e.get('confidence_score', 0) >= 0.8]
            med_confidence = [e for e in filtered_entities if 0.6 <= e.get('confidence_score', 0) < 0.8]
            low_confidence = [e for e in filtered_entities if e.get('confidence_score', 0) < 0.6]

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("🟢 Alta Confidenza", len(high_confidence))
                if high_confidence:
                    with st.expander("📋 Entità ad Alta Confidenza", expanded=False):
                        for entity in high_confidence[:5]:
                            st.write(f"• **{entity['entity_name']}** ({entity['entity_type']})")

            with col2:
                st.metric("🟡 Confidenza Media", len(med_confidence))
                if med_confidence:
                    with st.expander("📋 Entità a Confidenza Media", expanded=False):
                        for entity in med_confidence[:5]:
                            st.write(f"• **{entity['entity_name']}** ({entity['entity_type']})")

            with col3:
                st.metric("🔴 Bassa Confidenza", len(low_confidence))
                if low_confidence:
                    with st.expander("📋 Entità a Bassa Confidenza", expanded=False):
                        for entity in low_confidence[:5]:
                            st.write(f"• **{entity['entity_name']}** ({entity['entity_type']})")

        # Most connected entities with confidence weighting
        if filtered_relationships:
            st.subheader("🌟 Entità più Influenti")

            entity_connections = {}
            entity_confidence_sum = {}

            for rel in filtered_relationships:
                source_name = rel['source_name']
                target_name = rel['target_name']
                rel_confidence = rel.get('confidence_score', 0.5)

                # Weighted connections by confidence
                entity_connections[source_name] = entity_connections.get(source_name, 0) + rel_confidence
                entity_connections[target_name] = entity_connections.get(target_name, 0) + rel_confidence

                # Sum confidence for averaging
                if source_name not in entity_confidence_sum:
                    entity_confidence_sum[source_name] = []
                if target_name not in entity_confidence_sum:
                    entity_confidence_sum[target_name] = []

                entity_confidence_sum[source_name].append(rel_confidence)
                entity_confidence_sum[target_name].append(rel_confidence)

            # Calculate most influential entities (connections weighted by confidence)
            influential_entities = []
            for entity_name, total_weight in entity_connections.items():
                avg_confidence = sum(entity_confidence_sum[entity_name]) / len(entity_confidence_sum[entity_name])
                influential_entities.append((entity_name, total_weight, avg_confidence))

            influential_entities.sort(key=lambda x: x[1], reverse=True)

            if influential_entities:
                st.write("**🎯 Entità più influenti (ponderate per confidenza):**")

                for entity_name, influence_score, avg_confidence in influential_entities[:10]:
                    entity_info = next((e for e in filtered_entities if e['entity_name'] == entity_name), None)
                    if entity_info:
                        confidence_emoji = get_confidence_emoji(avg_confidence)
                        st.write(f"• **{entity_name}** {confidence_emoji} - Influenza: {influence_score:.2f}")
                        st.caption(f"  Tipo: {entity_info['entity_type']} | Confidenza media: {avg_confidence:.2f}")
    else:
        st.info("🔍 **Nessuna relazione trovata con i filtri attuali.** Prova ad abbassare la confidenza minima o carica più documenti!")

    # Bayesian Confidence Actions
    st.subheader("🎮 Azioni Bayesiane")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Applica Decadimento Temporale", help="Riduci gradualmente la confidenza delle informazioni più vecchie"):
            from archivista_processing import apply_temporal_decay_bayesian_task
            decay_task = apply_temporal_decay_bayesian_task.delay(user_id)
            st.success("Decadimento temporale avviato!")
            st.info("Le informazioni più vecchie perderanno gradualmente confidenza.")

    with col2:
        if st.button("📊 Aggiorna Statistiche", help="Ricalcola le statistiche di confidenza"):
            st.rerun()

    with col3:
        if st.button("🔍 Esporta Cronologia Prove", help="Scarica la cronologia completa delle prove"):
            # Create evidence export
            all_evidence = []
            for entity in filtered_entities:
                entity_evidence = get_entity_evidence_history(entity.get('id'), limit=10)
                all_evidence.extend(entity_evidence)

            if all_evidence:
                evidence_df = pd.DataFrame(all_evidence)
                csv_data = evidence_df.to_csv(index=False)
                st.download_button(
                    label="📥 Scarica CSV",
                    data=csv_data,
                    file_name=f"evidence_history_user_{user_id}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Nessuna prova disponibile per l'esportazione.")

    # Generazione domande AI
    st.divider()
    st.subheader("🤖 Genera Domande AI")

    st.info("💡 **Funzione future:** Genera automaticamente domande di verifica per i concetti appresi!")

    if st.button("🚀 Abilita Generatore Domande AI", disabled=True):
        st.warning("Funzionalità in sviluppo per la prossima versione!")

    st.markdown("""
    **Presto disponibile:**
    - 📝 Quiz multi-scelta basati sui tuoi documenti
    - ❓ Domande aperte su concetti specifici
    - 🎭 Simulazione esami orali interattivi
    - 📊 Tracciamento progressi e aree di miglioramento
    """)

# --- BOTTOM INFO ---
st.divider()
st.markdown("""
### 🔬 Come Funziona l'Analisi AI

Il grafo della conoscenza viene costruito automaticamente attraverso:

1. **📖 Lettura Documenti**: L'AI analizza tutto il contenuto caricato
2. **🧠 Riconoscimento Entità**: Identifica concetti, autori, formule, teorie
3. **🔗 Analisi Relazioni**: Capisce come le idee sono collegate
4. **🌐 Mappatura Connessioni**: Crea una rete interattiva di conoscenze

**Le entità rilevate comprendono:**
- 🔵 **Concetti**: Idee astratte e argomenti principali
- 🔶 **Teorie**: Teorie specifiche nominate
- 👤 **Autori**: Contributori e scienziati
- ⚗️ **Tecniche**: Metodologie e approcci
- 🧮 **Formule**: Leggi e equazioni matematiche
""")
