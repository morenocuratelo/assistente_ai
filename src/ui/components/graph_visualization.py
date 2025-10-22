"""
GraphVisualization component.

Componente specializzato per la visualizzazione del grafo della conoscenza
con integrazione Bayesiana e filtri di confidenza.
"""

import streamlit as st
import pandas as pd
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from .base import BaseComponent

logger = logging.getLogger(__name__)


class GraphVisualization(BaseComponent):
    """Visualizzatore grafo della conoscenza con filtri Bayesiani."""

    def __init__(self, on_entity_select: Optional[Callable] = None):
        """Inizializza GraphVisualization.

        Args:
            on_entity_select: Callback per selezione entità
        """
        super().__init__(component_id="graph_visualization", title="Graph Visualization")
        self.on_entity_select = on_entity_select
        self.selected_entity = None
        self.min_confidence = 0.3
        self.graph_data = None
        self.filtered_entities = []
        self.filtered_relationships = []

        # Inizializza servizi
        self._initialize_services()

    def _initialize_services(self):
        """Inizializza servizi per grafo della conoscenza."""
        try:
            # Import servizi necessari
            from file_utils import get_user_knowledge_graph, get_entity_neighbors
            from knowledge_structure import get_confidence_color, get_confidence_label

            # Salva riferimenti per uso successivo
            self._get_user_knowledge_graph = get_user_knowledge_graph
            self._get_entity_neighbors = get_entity_neighbors
            self._get_confidence_color = get_confidence_color
            self._get_confidence_label = get_confidence_label

            logger.info("✅ GraphVisualization servizi inizializzati")

        except Exception as e:
            logger.error(f"❌ Errore inizializzazione GraphVisualization: {e}")
            st.error(f"Errore inizializzazione GraphVisualization: {e}")

    def render_controls(self):
        """Render controlli e filtri del grafo."""
        st.header("🧠 Grafo della Conoscenza")

        # Toolbar principale
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.caption("Esplora le connessioni concettuali estratte dai tuoi documenti")

        with col2:
            if st.button("🔄 Aggiorna Grafo"):
                self._refresh_graph_data()
                st.rerun()

        with col3:
            if st.button("📊 Statistiche"):
                st.session_state.show_graph_stats = True

        st.markdown("---")

        # Controlli filtri
        st.subheader("🔍 Controlli Visualizzazione")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Filtro confidenza
            self.min_confidence = st.slider(
                "Confidenza Minima",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.1,
                key="confidence_filter",
                help="Mostra solo entità e relazioni con confidenza >= valore selezionato"
            )

        with col2:
            # Filtro tipo entità
            entity_types = self._get_entity_types()
            selected_type = st.selectbox(
                "Tipo Entità",
                ["Tutte"] + entity_types,
                key="entity_type_filter"
            )
            self.selected_entity_type = selected_type if selected_type != "Tutte" else None

        with col3:
            # Selezione entità focale
            entity_names = self._get_entity_names()
            selected_entity = st.selectbox(
                "Entità Focale",
                ["Nessuna selezione"] + entity_names,
                key="entity_focus"
            )
            self.selected_entity = selected_entity if selected_entity != "Nessuna selezione" else None

        # Azioni entità focale
        if self.selected_entity:
            col1, col2 = st.columns(2)

            with col1:
                if st.button("🧲 Mostra Vicini", key="show_neighbors"):
                    self._show_entity_neighbors()

            with col2:
                if st.button("📋 Cronologia Prove", key="show_evidence"):
                    self._show_entity_evidence()

    def render_graph_overview(self):
        """Render panoramica grafo con statistiche."""
        try:
            # Verifica se utente è loggato
            if 'user_id' not in st.session_state or not st.session_state['user_id']:
                st.warning("🔐 Effettua il login per visualizzare il grafo della conoscenza")
                return

            user_id = st.session_state['user_id']

            # Carica dati grafo
            if self.graph_data is None:
                self._load_graph_data(user_id)

            if not self.graph_data or not self.graph_data.get('entities'):
                self._render_empty_graph_state()
                return

            # Applica filtri
            self._apply_filters()

            # Statistiche principali
            self._render_graph_statistics()

            # Entità per tipo
            self._render_entities_by_type()

            # Relazioni concettuali
            self._render_relationships()

            # Esplorazione interattiva
            self._render_interactive_exploration()

        except Exception as e:
            st.error(f"❌ Errore caricamento grafo: {e}")

    def _load_graph_data(self, user_id: int):
        """Carica dati grafo della conoscenza."""
        try:
            self.graph_data = self._get_user_knowledge_graph(user_id)
            logger.info(f"Grafo caricato: {len(self.graph_data.get('entities', []))} entità")
        except Exception as e:
            logger.error(f"Errore caricamento grafo: {e}")
            self.graph_data = {'entities': [], 'relationships': []}

    def _refresh_graph_data(self):
        """Aggiorna dati grafo."""
        try:
            if 'user_id' in st.session_state:
                user_id = st.session_state['user_id']
                self._load_graph_data(user_id)
                st.success("✅ Grafo aggiornato")
        except Exception as e:
            st.error(f"Errore aggiornamento grafo: {e}")

    def _apply_filters(self):
        """Applica filtri ai dati del grafo."""
        try:
            entities = self.graph_data.get('entities', [])
            relationships = self.graph_data.get('relationships', [])

            # Filtro confidenza
            self.filtered_entities = [
                e for e in entities
                if e.get('confidence_score', 0) >= self.min_confidence
            ]

            self.filtered_relationships = [
                r for r in relationships
                if r.get('confidence_score', 0) >= self.min_confidence
            ]

            # Filtro tipo entità
            if self.selected_entity_type:
                self.filtered_entities = [
                    e for e in self.filtered_entities
                    if e.get('entity_type') == self.selected_entity_type
                ]

            logger.info(f"Filtri applicati: {len(self.filtered_entities)} entità, {len(self.filtered_relationships)} relazioni")

        except Exception as e:
            logger.error(f"Errore applicazione filtri: {e}")
            self.filtered_entities = []
            self.filtered_relationships = []

    def _render_graph_statistics(self):
        """Render statistiche grafo."""
        st.subheader("📊 Statistiche Grafo")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("🔵 Entità", len(self.filtered_entities))

        with col2:
            st.metric("🔗 Relazioni", len(self.filtered_relationships))

        with col3:
            entity_types = len(set([e['entity_type'] for e in self.filtered_entities]))
            st.metric("🏷️ Tipi", entity_types)

        with col4:
            sources = len(set([e.get('source_file_name', 'N/A') for e in self.filtered_entities]))
            st.metric("📄 Documenti", sources)

        # Info filtri attivi
        if self.min_confidence > 0.0 or self.selected_entity_type:
            st.info(f"🔍 **Filtri Attivi**: Confidenza ≥ {self.min_confidence:.1%}" +
                   (f" | Tipo: {self.selected_entity_type}" if self.selected_entity_type else ""))

    def _render_entities_by_type(self):
        """Render entità raggruppate per tipo."""
        st.subheader("🏷️ Entità per Tipo")

        # Raggruppa entità per tipo
        entities_by_type = {}
        for entity in self.filtered_entities:
            entity_type = entity.get('entity_type', 'Sconosciuto')
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)

        # Render per tipo
        for entity_type, entities in entities_by_type.items():
            with st.expander(f"📂 {entity_type.title()} ({len(entities)})", expanded=len(entities) < 10):
                for entity in entities[:10]:  # Max 10 per tipo
                    self._render_entity_card(entity)

    def _render_entity_card(self, entity: Dict[str, Any]):
        """Render card singola entità."""
        confidence_score = entity.get('confidence_score', 0.5)
        confidence_color = self._get_confidence_color(confidence_score)
        confidence_label = self._get_confidence_label(confidence_score)

        # Card styling
        st.markdown(f"""
        <div style="
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
            background: linear-gradient(135deg, {confidence_color}15, {confidence_color}05);
        ">
            <h5>{entity.get('entity_name', 'Senza nome')}</h5>
            <p style="font-size: 0.9em; margin: 4px 0;">
                {entity.get('entity_description', 'Nessuna descrizione')[:100]}
                {'...' if len(entity.get('entity_description', '')) > 100 else ''}
            </p>
            <div style="margin-top: 8px;">
                <span style="
                    background: {confidence_color};
                    color: white;
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 0.8em;
                ">
                    {confidence_label}
                </span>
                <span style="font-size: 0.8em; margin-left: 8px;">
                    📄 {entity.get('source_file_name', 'N/A')}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Azioni entità
        col1, col2 = st.columns(2)

        with col1:
            if st.button("👁️ Esplora", key=f"explore_{entity.get('id')}"):
                self._explore_entity(entity)

        with col2:
            if st.button("📊 Dettagli", key=f"details_{entity.get('id')}"):
                self._show_entity_details(entity)

    def _render_relationships(self):
        """Render relazioni concettuali."""
        st.subheader("🔗 Relazioni Concettuali")

        if not self.filtered_relationships:
            st.info("📭 Nessuna relazione trovata con i filtri attuali")
            return

        # Crea dataframe relazioni
        relationships_data = []
        for rel in self.filtered_relationships[:50]:  # Limita per performance
            confidence_score = rel.get('confidence_score', 0.5)
            confidence_color = self._get_confidence_color(confidence_score)
            confidence_label = self._get_confidence_label(confidence_score)

            relationships_data.append({
                "Sorgente": f"{rel.get('source_name', 'N/A')} ({rel.get('source_type', 'N/A')})",
                "Relazione": rel.get('relationship_type', 'N/A').replace('_', ' ').title(),
                "Destinazione": f"{rel.get('target_name', 'N/A')} ({rel.get('target_type', 'N/A')})",
                "Confidenza": confidence_label,
                "Documento": rel.get('source_file_name', 'N/A')
            })

        if relationships_data:
            rel_df = pd.DataFrame(relationships_data)
            st.dataframe(rel_df, use_container_width=True)

    def _render_interactive_exploration(self):
        """Render esplorazione interattiva."""
        st.subheader("🎯 Esplorazione Interattiva")

        # Entità più influenti
        if self.filtered_relationships:
            influential_entities = self._calculate_influential_entities()

            if influential_entities:
                st.write("**🌟 Entità più influenti:**")

                for entity_name, influence_score, avg_confidence in influential_entities[:10]:
                    confidence_emoji = self._get_confidence_emoji(avg_confidence)
                    st.write(f"• **{entity_name}** {confidence_emoji} - Influenza: {influence_score:.2f}")

    def _render_empty_graph_state(self):
        """Render stato vuoto grafo."""
        st.info("🎯 **Il grafo della conoscenza è vuoto!**")

        st.markdown("""
        **Come popolare il grafo:**

        1. **📤 Carica documenti** nella sezione Archivio
        2. **🤖 L'AI analizzerà automaticamente**:
           - Concetti e teorie principali
           - Autori e contributori
           - Formule e metodologie
           - Relazioni tra concetti
        3. **📊 Torna qui** per esplorare le connessioni!

        **Documenti ideali:**
        - 📚 Libri di testo accademici
        - 📄 Articoli scientifici
        - 🎓 Tesi e dissertazioni
        - 📝 Appunti strutturati
        """)

        col1, col2 = st.columns([1, 2])

        with col1:
            if st.button("📤 Vai all'Archivio", type="primary"):
                st.session_state.active_tab = "archive"
                st.rerun()

        with col2:
            st.markdown("""
            *💡 Suggerimento: Inizia con documenti PDF o DOCX ben strutturati
            per risultati di estrazione ottimali.*
            """)

    def _get_entity_types(self) -> List[str]:
        """Ottieni tipi entità disponibili."""
        try:
            if self.graph_data and self.graph_data.get('entities'):
                return sorted(list(set([e.get('entity_type', '') for e in self.graph_data['entities']])))
            return []
        except Exception:
            return []

    def _get_entity_names(self) -> List[str]:
        """Ottieni nomi entità disponibili."""
        try:
            if self.graph_data and self.graph_data.get('entities'):
                return sorted([e.get('entity_name', '') for e in self.graph_data['entities']])
            return []
        except Exception:
            return []

    def _get_confidence_emoji(self, confidence_score: float) -> str:
        """Restituisce emoji per punteggio confidenza."""
        if confidence_score >= 0.8:
            return "🟢"
        elif confidence_score >= 0.6:
            return "🟡"
        elif confidence_score >= 0.3:
            return "🟠"
        else:
            return "🔴"

    def _show_entity_neighbors(self):
        """Mostra entità vicine."""
        try:
            if not self.selected_entity:
                return

            user_id = st.session_state['user_id']
            neighbors_data = self._get_entity_neighbors(user_id, self.selected_entity)

            st.subheader(f"🧲 Vicini di: {self.selected_entity}")

            if neighbors_data.get('relationships'):
                for rel in neighbors_data['relationships'][:10]:
                    other_entity = rel.get('target_name') if rel.get('source_name') == self.selected_entity else rel.get('source_name')
                    confidence_emoji = self._get_confidence_emoji(rel.get('confidence_score', 0.5))

                    st.write(f"• **{other_entity}** ({rel.get('relationship_type', 'N/A')}) {confidence_emoji}")
            else:
                st.info("Nessun vicino trovato")

        except Exception as e:
            st.error(f"Errore recupero vicini: {e}")

    def _show_entity_evidence(self):
        """Mostra cronologia prove entità."""
        try:
            if not self.selected_entity:
                return

            st.subheader(f"📋 Prove: {self.selected_entity}")

            # Placeholder per cronologia prove
            st.info("📝 Cronologia prove da implementare")

        except Exception as e:
            st.error(f"Errore cronologia prove: {e}")

    def _explore_entity(self, entity: Dict[str, Any]):
        """Esplora entità selezionata."""
        try:
            self.selected_entity = entity.get('entity_name')
            if self.on_entity_select:
                self.on_entity_select(entity)
            st.success(f"Entità '{entity.get('entity_name')}' selezionata")
        except Exception as e:
            st.error(f"Errore esplorazione entità: {e}")

    def _show_entity_details(self, entity: Dict[str, Any]):
        """Mostra dettagli entità."""
        try:
            st.subheader(f"📊 Dettagli: {entity.get('entity_name')}")

            # Info principali
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Tipo:** {entity.get('entity_type', 'N/A')}")
                st.write(f"**Documento:** {entity.get('source_file_name', 'N/A')}")

            with col2:
                confidence_score = entity.get('confidence_score', 0.5)
                st.write(f"**Confidenza:** {confidence_score:.1%}")
                st.write(f"**Livello:** {self._get_confidence_label(confidence_score)}")

            # Descrizione
            if entity.get('entity_description'):
                st.write(f"**Descrizione:** {entity.get('entity_description')}")

            # Progress bar confidenza
            st.progress(confidence_score, text=f"Confidenza: {confidence_score:.1%}")

        except Exception as e:
            st.error(f"Errore dettagli entità: {e}")

    def _calculate_influential_entities(self) -> List[tuple]:
        """Calcola entità più influenti."""
        try:
            entity_connections = {}
            entity_confidence_sum = {}

            for rel in self.filtered_relationships:
                source_name = rel.get('source_name', '')
                target_name = rel.get('target_name', '')
                rel_confidence = rel.get('confidence_score', 0.5)

                # Pondera connessioni per confidenza
                entity_connections[source_name] = entity_connections.get(source_name, 0) + rel_confidence
                entity_connections[target_name] = entity_connections.get(target_name, 0) + rel_confidence

                # Somma confidenza per media
                if source_name not in entity_confidence_sum:
                    entity_confidence_sum[source_name] = []
                if target_name not in entity_confidence_sum:
                    entity_confidence_sum[target_name] = []

                entity_confidence_sum[source_name].append(rel_confidence)
                entity_confidence_sum[target_name].append(rel_confidence)

            # Calcola entità più influenti
            influential_entities = []
            for entity_name, total_weight in entity_connections.items():
                if entity_name in [e.get('entity_name') for e in self.filtered_entities]:
                    avg_confidence = sum(entity_confidence_sum[entity_name]) / len(entity_confidence_sum[entity_name])
                    influential_entities.append((entity_name, total_weight, avg_confidence))

            influential_entities.sort(key=lambda x: x[1], reverse=True)
            return influential_entities

        except Exception as e:
            logger.error(f"Errore calcolo entità influenti: {e}")
            return []

    def render(self):
        """Render componente principale."""
        # Render controlli
        self.render_controls()

        st.markdown("---")

        # Render panoramica grafo
        self.render_graph_overview()


def create_graph_visualization(on_entity_select: Optional[Callable] = None) -> GraphVisualization:
    """Factory function per creare GraphVisualization."""
    return GraphVisualization(on_entity_select)
