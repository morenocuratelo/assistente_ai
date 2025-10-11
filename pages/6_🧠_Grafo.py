import streamlit as st
import pandas as pd
import json
import networkx as nx
from streamlit.components.v1 import html
from file_utils import get_user_knowledge_graph, get_entity_neighbors

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
                st.sidebar.write(f"• {other_entity} ({relation['relationship_type']})")

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

    st.divider()

    # Filter entities by type
    filtered_entities = graph_data['entities']
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
                    for i, entity in enumerate(source_entities):
                        confidence_color = "🟢" if entity['confidence_score'] > 0.8 else "🟡" if entity['confidence_score'] > 0.5 else "🔴"

                        st.markdown(f"""
                        {i+1}. **{entity['entity_name']}** {confidence_color}
                        - *{entity.get('entity_description', 'Nessuna descrizione')}*
                        - Confidenza: {entity['confidence_score']:.2f}
                        """)

                    st.divider()

    # Relazioni
    st.subheader("🔗 Relazioni Concettuali")

    if graph_data['relationships']:
        # Filter relationships for selected entities
        filtered_relationships = graph_data['relationships']
        if selected_entity_type != "All":
            filtered_relationships = [r for r in filtered_relationships
                                    if r['source_type'] == selected_entity_type or r['target_type'] == selected_entity_type]

        st.write(f"**{len(filtered_relationships)} relazioni trovate**")

        # Display relationships in a table
        relationships_data = []
        for rel in filtered_relationships[:100]:  # Limit to 100 for performance
            relationships_data.append({
                "Da": f"{rel['source_name']} ({rel['source_type']})",
                "Relazione": rel['relationship_type'].replace('_', ' ').title(),
                "A": f"{rel['target_name']} ({rel['target_type']})",
                "Confidenza": f"{rel['confidence_score']:.2f}",
                "Documento": rel.get('source_file_name', 'N/A')
            })

        if relationships_data:
            st.dataframe(pd.DataFrame(relationships_data), use_container_width=True,
                        column_config={
                            "Da": st.column_config.TextColumn("Entità Sorgente", width="medium"),
                            "Relazione": st.column_config.TextColumn("Tipo Relazione", width="medium"),
                            "A": st.column_config.TextColumn("Entità Destinazione", width="medium"),
                            "Confidenza": st.column_config.TextColumn("Confidenza AI", width="small"),
                            "Documento": st.column_config.TextColumn("Fonte", width="medium")
                        })

        # Simple graph visualization (text-based for now)
        st.subheader("🌟 Esplora Connessioni")

        # Most connected entities
        if filtered_relationships:
            entity_connections = {}
            for rel in filtered_relationships:
                entity_connections[rel['source_name']] = entity_connections.get(rel['source_name'], 0) + 1
                entity_connections[rel['target_name']] = entity_connections.get(rel['target_name'], 0) + 1

            most_connected = sorted(entity_connections.items(), key=lambda x: x[1], reverse=True)[:10]

            if most_connected:
                st.write("**🎯 Entità più connesse:**")
                for entity_name, connections in most_connected:
                    entity_info = next((e for e in filtered_entities if e['entity_name'] == entity_name), None)
                    if entity_info:
                        st.write(f"• **{entity_name}** ({entity_info['entity_type']}) - {connections} connessioni")
    else:
        st.info("Nessuna relazione trovata. Carica più documenti per vedere le connessioni!")

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
