"""
Dashboard di Monitoraggio per il Framework di Diagnosi Errori
Fornisce interfaccia real-time per il tracciamento dello stato di processamento.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

from error_diagnosis_framework import (
    get_processing_status_summary,
    get_error_dashboard_data,
    resolve_error,
    get_files_requiring_intervention,
    error_framework
)
from file_utils import get_papers_dataframe

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="📊 Dashboard Monitoraggio - Archivista AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNZIONI CACHE PER PERFORMANCE ---

@st.cache_data(ttl=30)  # Cache per 30 secondi
def get_dashboard_metrics():
    """Recupera tutte le metriche per la dashboard"""
    return {
        'processing_summary': get_processing_status_summary(),
        'error_data': get_error_dashboard_data(),
        'intervention_files': get_files_requiring_intervention()
    }

@st.cache_data(ttl=60)  # Cache per 1 minuto
def get_historical_metrics(days=7):
    """Recupera metriche storiche per i trend"""
    metrics = error_framework.get_processing_metrics(days)
    return metrics

# --- COMPONENTI DASHBOARD ---

def render_header():
    """Render header della dashboard"""
    st.title("📊 Dashboard Monitoraggio Processamento")
    st.markdown("### Monitoraggio in tempo reale del sistema di processamento documenti")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🔄 Ultimo Aggiornamento", datetime.now().strftime("%H:%M:%S"))

    with col2:
        if st.button("🔄 Aggiorna Dati", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    with col3:
        auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=True)
        if auto_refresh:
            time.sleep(30)
            st.rerun()

def render_processing_overview(metrics):
    """Render panoramica processamento"""
    st.header("📈 Stato Processamento")

    summary = metrics['processing_summary']

    # Metriche principali
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total = summary.get('total_files', 0)
        st.metric("📚 Totale File", total)

    with col2:
        failed = summary.get('failed_files', 0)
        st.metric("❌ File Falliti", failed)

    with col3:
        success_rate = ((total - failed) / total * 100) if total > 0 else 0
        st.metric("✅ Tasso Successo", f"{success_rate:.1f}%")

    with col4:
        recent_errors = len(summary.get('recent_errors', []))
        st.metric("🚨 Errori Recenti", recent_errors)

    # Grafico stati processamento
    if summary.get('state_counts'):
        st.subheader("📊 Distribuzione Stati")

        state_data = []
        for state, count in summary['state_counts'].items():
            state_data.append({
                'Stato': state.replace('_', ' ').title(),
                'Conteggio': count,
                'Categoria': 'Completati' if state == 'COMPLETED' else 'Falliti' if state.startswith('FAILED_') else 'In Corso'
            })

        if state_data:
            df = pd.DataFrame(state_data)

            fig = px.bar(df, x='Stato', y='Conteggio', color='Categoria',
                        color_discrete_map={
                            'Completati': 'green',
                            'Falliti': 'red',
                            'In Corso': 'blue'
                        })

            st.plotly_chart(fig, use_container_width=True)

def render_error_analysis(metrics):
    """Render analisi errori"""
    st.header("🚨 Analisi Errori")

    error_data = metrics['error_data']

    if not error_data.get('errors_by_category'):
        st.info("✅ Nessun errore registrato!")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 Errori per Categoria")

        # Tabella errori per categoria
        error_df = pd.DataFrame(error_data['errors_by_category'])
        if not error_df.empty:
            st.dataframe(error_df, use_container_width=True)

    with col2:
        st.subheader("⚡ Errori per Severità")

        # Grafico errori per severità
        severity_df = pd.DataFrame(error_data['errors_by_severity'])
        if not severity_df.empty:
            fig = px.pie(severity_df, values='count', names='error_type',
                        title="Distribuzione per Severità")
            st.plotly_chart(fig)

    # Trend errori
    st.subheader("📅 Trend Errori (7 giorni)")

    trends_df = pd.DataFrame(error_data['error_trends'])
    if not trends_df.empty:
        fig = px.line(trends_df, x='date', y='count', title="Andamento Errori Giornaliero")
        st.plotly_chart(fig)
    else:
        st.info("📊 Nessun trend disponibile")

def render_files_requiring_intervention(metrics):
    """Render file che richiedono intervento manuale"""
    st.header("🔧 File che Richiedono Intervento")

    intervention_files = metrics['intervention_files']

    if not intervention_files:
        st.success("✅ Tutti i file sono processati correttamente!")
        return

    st.warning(f"⚠️ {len(intervention_files)} file richiedono attenzione manuale")

    for file_info in intervention_files[:10]:  # Mostra max 10
        with st.expander(f"📄 {file_info['file_name']} - {file_info['processing_state']}"):
            col1, col2 = st.columns([0.7, 0.3])

            with col1:
                st.markdown(f"**Stato:** {file_info['processing_state']}")
                st.markdown(f"**Fase:** {file_info['current_phase']}")
                if file_info['error_message']:
                    st.markdown(f"**Errore:** {file_info['error_message']}")
                st.markdown(f"**Ultimo aggiornamento:** {file_info['updated_at']}")

            with col2:
                st.markdown("**⚡ Azioni Rapide:**")

                if st.button("🔄 Riprova", key=f"retry_{file_info['file_name']}"):
                    success = error_framework.reset_processing_status(file_info['file_name'])
                    if success:
                        st.success(f"✅ Stato di {file_info['file_name']} resettato per nuovo tentativo")
                        st.rerun()
                    else:
                        st.error("❌ Errore nel reset del processamento")

                if st.button("🚫 Sposta in Quarantena", key=f"quarantine_{file_info['file_name']}"):
                    # Qui andrebbe implementata la logica di quarantena manuale
                    st.info("🚧 Funzionalità di quarantena manuale da implementare")

def render_recent_activity(metrics):
    """Render attività recente"""
    st.header("🕐 Attività Recente")

    summary = metrics['processing_summary']

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 File Processati di Recente")

        recent_files = summary.get('recent_files', [])
        if recent_files:
            for file_info in recent_files:
                status_icon = {
                    'COMPLETED': '✅',
                    'PROCESSING': '🔄',
                    'FAILED_PARSING': '❌',
                    'PENDING': '⏳'
                }.get(file_info['processing_state'], '📄')

                st.write(f"{status_icon} **{file_info['file_name']}**")
                st.caption(f"Stato: {file_info['processing_state']} | {file_info['updated_at']}")
        else:
            st.info("Nessun file recente")

    with col2:
        st.subheader("🚨 Errori Recenti")

        recent_errors = summary.get('recent_errors', [])
        if recent_errors:
            for error_info in recent_errors:
                st.write(f"❌ **{error_info['file_name']}**")
                st.caption(f"Errore: {error_info['error_message'][:100]}...")
                st.caption(f"📅 {error_info['created_at']}")
        else:
            st.info("Nessun errore recente")

def render_system_health():
    """Render stato di salute del sistema"""
    st.header("💚 Stato Salute Sistema")

    try:
        # Verifica connessione database
        from file_utils import db_connect
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM papers")
            db_status = "✅ OK"

        # Verifica servizi AI
        from config import initialize_services
        try:
            initialize_services()
            ai_status = "✅ OK"
        except:
            ai_status = "❌ Non disponibile"

        # Verifica worker Celery
        celery_status = "⚠️ Da verificare"

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("🗄️ Database", db_status)

        with col2:
            st.metric("🤖 Servizi AI", ai_status)

        with col3:
            st.metric("⚙️ Worker Celery", celery_status)

    except Exception as e:
        st.error(f"❌ Errore nel controllo stato sistema: {e}")

def render_quarantine_management():
    """Render gestione quarantena"""
    st.header("🚫 Gestione Quarantena")

    try:
        quarantined_files = error_framework.get_quarantined_files(limit=20)

        if not quarantined_files:
            st.success("✅ Nessun file in quarantena!")
            return

        st.warning(f"⚠️ {len(quarantined_files)} file in quarantena")

        for file_info in quarantined_files:
            with st.expander(f"📁 {file_info['file_name']} - {file_info['failure_reason'][:50]}..."):
                col1, col2 = st.columns([0.7, 0.3])

                with col1:
                    st.markdown(f"**File:** {file_info['file_name']}")
                    st.markdown(f"**Motivo fallimento:** {file_info['failure_reason']}")
                    st.markdown(f"**Categoria errore:** {file_info['failure_category']}")
                    st.markdown(f"**Percorso quarantena:** {file_info['quarantine_path']}")
                    st.markdown(f"**Data quarantena:** {file_info['created_at']}")

                    if file_info['error_details']:
                        with st.expander("🔍 Dettagli Tecnici"):
                            st.json(json.loads(file_info['error_details']))

                with col2:
                    st.markdown("**⚡ Azioni:**")

                    if st.button("🔄 Riprova", key=f"quarantine_retry_{file_info['file_name']}"):
                        success = error_framework.reset_processing_status(file_info['file_name'])
                        if success:
                            st.success(f"✅ {file_info['file_name']} pronto per nuovo tentativo")
                            st.rerun()
                        else:
                            st.error("❌ Errore nel reset")

                    if st.button("🗑️ Elimina", key=f"quarantine_delete_{file_info['file_name']}"):
                        # Implementa logica eliminazione
                        st.info("🚧 Funzionalità eliminazione da implementare")

    except Exception as e:
        st.error(f"❌ Errore nel caricamento quarantena: {e}")

def render_performance_metrics():
    """Render metriche di performance"""
    st.header("📊 Metriche Performance")

    try:
        historical_metrics = get_historical_metrics(7)

        if not historical_metrics:
            st.info("📈 Nessuna metrica storica disponibile")
            return

        # Crea dataframe per i grafici
        metrics_data = []
        for metric in historical_metrics:
            metrics_data.append({
                'Data': metric.date_period,
                'Totale': metric.total_files,
                'Completati': metric.files_completed,
                'Falliti': metric.files_failed,
                'Tasso Errore': metric.error_rate,
                'In Quarantena': metric.quarantine_count
            })

        df = pd.DataFrame(metrics_data)

        if not df.empty:
            # Grafico tasso di errore
            fig_error_rate = px.line(df, x='Data', y='Tasso Errore',
                                   title="Tasso di Errore nel Tempo")
            st.plotly_chart(fig_error_rate)

            # Grafico volumi
            fig_volumes = go.Figure()
            fig_volumes.add_trace(go.Bar(name='Completati', x=df['Data'], y=df['Completati']))
            fig_volumes.add_trace(go.Bar(name='Falliti', x=df['Data'], y=df['Falliti']))
            fig_volumes.update_layout(title="Volumi di Processamento", barmode='stack')
            st.plotly_chart(fig_volumes)

    except Exception as e:
        st.error(f"❌ Errore nel caricamento metriche performance: {e}")

# --- PAGINA PRINCIPALE ---

def main():
    """Pagina principale dashboard"""
    render_header()

    # Carica metriche
    try:
        metrics = get_dashboard_metrics()
    except Exception as e:
        st.error(f"❌ Errore nel caricamento dati dashboard: {e}")
        st.stop()

    # Tabs per organizzare contenuti
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Panoramica",
        "🚨 Analisi Errori",
        "🔧 Interventi",
        "🚫 Quarantena",
        "📊 Performance"
    ])

    with tab1:
        render_processing_overview(metrics)
        st.markdown("---")
        render_recent_activity(metrics)
        st.markdown("---")
        render_system_health()

    with tab2:
        render_error_analysis(metrics)

    with tab3:
        render_files_requiring_intervention(metrics)

    with tab4:
        render_quarantine_management()

    with tab5:
        render_performance_metrics()

    # Footer con informazioni tecniche
    st.markdown("---")
    with st.expander("🔧 Informazioni Tecniche"):
        st.markdown("""
        **Dashboard Monitoraggio v2.0**

        **Funzionalità:**
        - ✅ Monitoraggio stato processamento in tempo reale
        - ✅ Classificazione automatica errori
        - ✅ Sistema quarantena per file problematici
        - ✅ Metriche performance storiche
        - ✅ Analisi trend errori
        - ✅ Azioni correttive rapide

        **Stati Processamento:**
        - `PENDING`: File rilevato ma non accodato
        - `QUEUED`: Task inviato a Celery
        - `PROCESSING`: Worker ha iniziato elaborazione
        - `FAILED_*`: Errori specifici per fase
        - `COMPLETED`: Processo completato con successo
        - `MANUAL_INTERVENTION_REQUIRED`: Richiede attenzione umana

        **Categorie Errori:**
        - `IOError`: Problemi lettura/scrittura file
        - `ConnectionError`: Problemi connessione servizi
        - `APIError`: Errori API/LLM
        - `FormatError`: Formato dati non valido
        - `IndexingError`: Problemi indicizzazione
        - `ArchivingError`: Problemi archiviazione
        """)

if __name__ == "__main__":
    main()
