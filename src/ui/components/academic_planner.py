"""
AcademicPlanner component.

Componente specializzato per la pianificazione accademica
con calendario, timeline e gestione scadenze.
"""

import streamlit as st
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, date, timedelta
import calendar

from .base import BaseComponent

logger = logging.getLogger(__name__)


class AcademicPlanner(BaseComponent):
    """Pianificatore accademico avanzato con calendario e timeline."""

    def __init__(self, on_task_update: Optional[Callable] = None):
        """Inizializza AcademicPlanner.

        Args:
            on_task_update: Callback per aggiornamento attività
        """
        super().__init__(component_id="academic_planner", title="Academic Planner")
        self.on_task_update = on_task_update
        self.selected_date = date.today()
        self.view_mode = "month"  # month, week, day
        self.tasks_cache = []

        # Inizializza servizi
        self._initialize_services()

    def _initialize_services(self):
        """Inizializza servizi per pianificazione accademica."""
        try:
            # Import servizi necessari
            from src.services.career_service import create_career_service

            # Usa database esistente
            db_path = "db_memoria/metadata.sqlite"
            self.career_service = create_career_service(db_path)

            logger.info("✅ AcademicPlanner servizi inizializzati")

        except Exception as e:
            logger.error(f"❌ Errore inizializzazione AcademicPlanner: {e}")
            st.error(f"Errore inizializzazione AcademicPlanner: {e}")

    def render_calendar_view(self):
        """Render vista calendario mensile."""
        st.header("📅 Calendario Accademico")

        # Controlli calendario
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            # Selettore mese/anno
            current_month = st.session_state.get('calendar_month', self.selected_date.month)
            current_year = st.session_state.get('calendar_year', self.selected_date.year)

            month_col, year_col = st.columns(2)
            with month_col:
                month = st.selectbox(
                    "Mese",
                    range(1, 13),
                    index=current_month - 1,
                    key="month_selector",
                    format_func=lambda x: calendar.month_name[x]
                )
            with year_col:
                year = st.selectbox(
                    "Anno",
                    range(current_year - 1, current_year + 2),
                    index=1,
                    key="year_selector"
                )

            # Aggiorna data selezionata
            self.selected_date = date(year, month, 1)

        with col2:
            # Selettore vista
            view_mode = st.selectbox(
                "Vista",
                ["Mese", "Settimana", "Giorno"],
                key="view_mode_selector"
            )
            self.view_mode = view_mode.lower()

        with col3:
            # Azioni rapide
            if st.button("🎯 Oggi", key="today_btn"):
                self.selected_date = date.today()
                st.rerun()

        # Render calendario
        if self.view_mode == "mese":
            self._render_month_view()
        elif self.view_mode == "settimana":
            self._render_week_view()
        else:
            self._render_day_view()

    def _render_month_view(self):
        """Render vista calendario mensile."""
        # Crea calendario per il mese selezionato
        cal = calendar.monthcalendar(self.selected_date.year, self.selected_date.month)

        # Header giorni settimana
        days_header = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
        header_cols = st.columns(7)

        for i, day in enumerate(days_header):
            with header_cols[i]:
                st.markdown(f"**{day}**")

        # Giorni del mese
        for week in cal:
            day_cols = st.columns(7)

            for i, day in enumerate(week):
                with day_cols[i]:
                    if day != 0:
                        day_date = date(self.selected_date.year, self.selected_date.month, day)

                        # Evidenzia giorno corrente
                        is_today = day_date == date.today()
                        background_color = "#e3f2fd" if is_today else "transparent"

                        st.markdown(f"""
                        <div style="
                            background-color: {background_color};
                            border: 1px solid #ddd;
                            border-radius: 4px;
                            padding: 8px;
                            text-align: center;
                            min-height: 80px;
                        ">
                            <div style="font-weight: bold; margin-bottom: 4px;">{day}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Mostra attività per questo giorno
                        day_tasks = self._get_tasks_for_date(day_date)
                        if day_tasks:
                            for task in day_tasks[:2]:  # Max 2 task visibili
                                priority_colors = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                                status_icons = {'pending': '⏳', 'in_progress': '🔄', 'completed': '✅'}

                                st.markdown(f"""
                                {status_icons.get(task['status'], '❓')} {task['title'][:15]}{'...' if len(task['title']) > 15 else ''}
                                """)

                            if len(day_tasks) > 2:
                                st.caption(f"+{len(day_tasks) - 2} altre")

                        # Pulsante aggiungi attività
                        if st.button("➕", key=f"add_task_{day_date.isoformat()}", help="Aggiungi attività"):
                            st.session_state.task_date = day_date
                            st.session_state.show_task_creator = True
                            st.rerun()

    def _render_week_view(self):
        """Render vista calendario settimanale."""
        # Calcola inizio settimana (lunedì)
        start_of_week = self.selected_date - timedelta(days=self.selected_date.weekday())

        st.subheader(f"📅 Settimana del {start_of_week.strftime('%d/%m/%Y')}")

        # Giorni della settimana
        week_days = [start_of_week + timedelta(days=i) for i in range(7)]

        # Header giorni
        day_cols = st.columns(7)
        for i, day_date in enumerate(week_days):
            with day_cols[i]:
                is_today = day_date == date.today()
                background_color = "#e3f2fd" if is_today else "transparent"

                st.markdown(f"""
                <div style="
                    background-color: {background_color};
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 8px;
                    text-align: center;
                ">
                    <div style="font-weight: bold;">{day_date.strftime('%d/%m')}</div>
                    <div style="font-size: 0.8em;">{day_date.strftime('%A')[:3]}</div>
                </div>
                """, unsafe_allow_html=True)

        # Orari e attività (simulazione)
        st.markdown("---")
        st.subheader("⏰ Orario Giornaliero")

        # Layout orario
        time_slots = [f"{h:02d}:00" for h in range(8, 20)]  # 8:00 - 19:00

        for time_slot in time_slots:
            col1, col2 = st.columns([1, 6])

            with col1:
                st.caption(time_slot)

            with col2:
                # Mostra attività per questo orario
                slot_tasks = self._get_tasks_for_time_slot(time_slot)
                if slot_tasks:
                    for task in slot_tasks:
                        priority_colors = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                        st.markdown(f"""
                        {priority_colors.get(task['priority'], '⚪')} **{task['title']}**
                        - {task['course_name'] if task.get('course_name') else 'Generale'}
                        """)
                else:
                    st.caption("Libero")

    def _render_day_view(self):
        """Render vista giornaliera dettagliata."""
        st.subheader(f"📅 {self.selected_date.strftime('%A %d %B %Y')}")

        # Statistiche giorno
        day_tasks = self._get_tasks_for_date(self.selected_date)
        completed_tasks = [t for t in day_tasks if t['status'] == 'completed']

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📋 Totale Attività", len(day_tasks))

        with col2:
            st.metric("✅ Completate", len(completed_tasks))

        with col3:
            st.metric("⏳ In Corso", len([t for t in day_tasks if t['status'] == 'in_progress']))

        with col4:
            completion_rate = (len(completed_tasks) / len(day_tasks) * 100) if day_tasks else 0
            st.metric("📊 Completamento", f"{completion_rate:.0f}%")

        st.markdown("---")

        # Timeline giornaliera
        if day_tasks:
            st.subheader("⏰ Timeline Giornaliera")

            # Ordina per orario/scadenza
            sorted_tasks = sorted(day_tasks, key=lambda x: x.get('due_date', ''))

            for task in sorted_tasks:
                priority_colors = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                status_icons = {'pending': '⏳', 'in_progress': '🔄', 'completed': '✅'}

                with st.expander(f"{status_icons.get(task['status'], '❓')} {task['title']}"):
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        st.write(f"**Corso:** {task.get('course_name', 'N/A')}")
                        st.write(f"**Tipo:** {task.get('task_type', 'N/A').replace('_', ' ').title()}")
                        if task.get('description'):
                            st.write(f"**Descrizione:** {task['description']}")

                    with col2:
                        st.write(f"**Priorità:** {priority_colors.get(task['priority'], '⚪')} {task['priority'].title()}")
                        st.write(f"**Stato:** {status_icons.get(task['status'], '❓')} {task['status'].replace('_', ' ').title()}")

                        if task.get('due_date'):
                            st.write(f"**Scadenza:** {task['due_date']}")

                    with col3:
                        # Azioni task
                        if task['status'] != 'completed':
                            if st.button("✅ Completa", key=f"complete_{task['id']}"):
                                self._update_task_status(task['id'], 'completed')
                                st.rerun()

                        if st.button("📝 Modifica", key=f"edit_{task['id']}"):
                            st.session_state.edit_task = task
                            st.rerun()
        else:
            st.info("🎉 Nessuna attività per questo giorno!")
            st.write("Goditi il tuo tempo libero o pianifica nuove attività.")

    def render_task_manager(self):
        """Render gestore attività accademiche."""
        st.header("🎯 Gestione Attività Accademiche")

        # Toolbar gestione attività
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            # Filtro stato
            status_filter = st.selectbox(
                "Stato",
                ["Tutti", "Da fare", "In corso", "Completati"],
                key="task_status_filter"
            )

        with col2:
            # Filtro priorità
            priority_filter = st.selectbox(
                "Priorità",
                ["Tutte", "Alta", "Media", "Bassa"],
                key="task_priority_filter"
            )

        with col3:
            # Azione rapida
            if st.button("➕ Nuova Attività", type="primary"):
                st.session_state.show_task_creator = True

        st.markdown("---")

        try:
            # Recupera attività utente
            if 'user_id' not in st.session_state or not st.session_state['user_id']:
                st.warning("🔐 Effettua il login per visualizzare le attività")
                return

            user_id = st.session_state['user_id']
            tasks_result = self.career_service.repository.get_user_tasks(user_id)

            if tasks_result:
                # Applica filtri
                filtered_tasks = self._apply_task_filters(tasks_result, status_filter, priority_filter)

                if filtered_tasks:
                    st.subheader(f"📋 Attività ({len(filtered_tasks)})")

                    # Layout kanban
                    self._render_kanban_board(filtered_tasks)
                else:
                    st.info("📭 Nessuna attività trovata con i filtri selezionati")
                    self._render_empty_task_state()
            else:
                st.info("📭 Nessuna attività trovata")
                self._render_empty_task_state()

        except Exception as e:
            st.error(f"❌ Errore caricamento attività: {e}")

    def _render_kanban_board(self, tasks: List[Dict[str, Any]]):
        """Render board kanban per attività."""
        # Colonne kanban
        col1, col2, col3 = st.columns(3)

        # Da fare
        with col1:
            st.markdown("### ⏳ Da Fare")
            pending_tasks = [t for t in tasks if t['status'] == 'pending']

            for task in pending_tasks:
                self._render_task_card(task, "pending")

        # In corso
        with col2:
            st.markdown("### 🔄 In Corso")
            in_progress_tasks = [t for t in tasks if t['status'] == 'in_progress']

            for task in in_progress_tasks:
                self._render_task_card(task, "in_progress")

        # Completate
        with col3:
            st.markdown("### ✅ Completate")
            completed_tasks = [t for t in tasks if t['status'] == 'completed']

            for task in completed_tasks:
                self._render_task_card(task, "completed")

    def _render_task_card(self, task: Dict[str, Any], column: str):
        """Render card attività per kanban."""
        priority_colors = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        priority_color = priority_colors.get(task['priority'], '⚪')

        # Card styling based on status
        card_class = f"task-card task-{task['status']}"

        st.markdown(f"""
        <div class="{card_class}" style="margin-bottom: 10px; padding: 12px; border-radius: 6px;">
            <h5>{task['title']}</h5>
            <p style="font-size: 0.9em; margin: 4px 0;">{task.get('description', 'Nessuna descrizione')[:50]}{'...' if len(task.get('description', '')) > 50 else ''}</p>
            <div style="margin-top: 8px;">
                <span style="font-size: 0.8em;">{priority_color} {task['priority'].title()}</span>
                {f'<span style="font-size: 0.8em; margin-left: 8px;">📅 {task.get("due_date", "")}</span>' if task.get('due_date') else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Azioni task
        action_col1, action_col2, action_col3 = st.columns([1, 1, 1])

        with action_col1:
            if column == "pending" and st.button("▶️ Inizia", key=f"start_{task['id']}"):
                self._update_task_status(task['id'], 'in_progress')
                st.rerun()

        with action_col2:
            if column == "in_progress" and st.button("✅ Fine", key=f"complete_{task['id']}"):
                self._update_task_status(task['id'], 'completed')
                st.rerun()

        with action_col3:
            if st.button("📝", key=f"edit_{task['id']}", help="Modifica"):
                st.session_state.edit_task = task
                st.rerun()

    def _apply_task_filters(self, tasks: List[Dict[str, Any]], status_filter: str, priority_filter: str) -> List[Dict[str, Any]]:
        """Applica filtri alle attività."""
        filtered_tasks = tasks

        # Filtro stato
        if status_filter == "Da fare":
            filtered_tasks = [t for t in filtered_tasks if t['status'] == 'pending']
        elif status_filter == "In corso":
            filtered_tasks = [t for t in filtered_tasks if t['status'] == 'in_progress']
        elif status_filter == "Completati":
            filtered_tasks = [t for t in filtered_tasks if t['status'] == 'completed']

        # Filtro priorità
        if priority_filter == "Alta":
            filtered_tasks = [t for t in filtered_tasks if t['priority'] == 'high']
        elif priority_filter == "Media":
            filtered_tasks = [t for t in filtered_tasks if t['priority'] == 'medium']
        elif priority_filter == "Bassa":
            filtered_tasks = [t for t in filtered_tasks if t['priority'] == 'low']

        return filtered_tasks

    def _get_tasks_for_date(self, target_date: date) -> List[Dict[str, Any]]:
        """Recupera attività per una data specifica."""
        try:
            # Placeholder - in implementazione completa useresti query specifiche
            all_tasks = self.tasks_cache

            # Filtra per data
            day_tasks = []
            for task in all_tasks:
                if task.get('due_date'):
                    try:
                        task_date = datetime.fromisoformat(task['due_date']).date()
                        if task_date == target_date:
                            day_tasks.append(task)
                    except:
                        continue

            return day_tasks

        except Exception as e:
            logger.error(f"Errore recupero attività per data {target_date}: {e}")
            return []

    def _get_tasks_for_time_slot(self, time_slot: str) -> List[Dict[str, Any]]:
        """Recupera attività per fascia oraria."""
        try:
            # Placeholder - in implementazione completa useresti query specifiche
            return []
        except Exception as e:
            logger.error(f"Errore recupero attività per fascia {time_slot}: {e}")
            return []

    def _update_task_status(self, task_id: Any, new_status: str):
        """Aggiorna stato attività."""
        try:
            # Placeholder - in implementazione completa useresti il servizio
            logger.info(f"Aggiornamento stato attività {task_id} -> {new_status}")

            # Callback se fornito
            if self.on_task_update:
                self.on_task_update(task_id, new_status)

        except Exception as e:
            logger.error(f"Errore aggiornamento stato attività {task_id}: {e}")
            st.error(f"Errore aggiornamento attività: {e}")

    def _render_empty_task_state(self):
        """Render stato vuoto attività con call-to-action."""
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h3>🎯 Inizia a pianificare!</h3>
            <p>Le attività accademiche ti aiutano a organizzare lo studio e rispettare le scadenze.</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.button("➕ Crea la tua prima attività", type="primary", use_container_width=True):
                st.session_state.show_task_creator = True

    def render_task_creator(self):
        """Render modal creazione attività."""
        with st.expander("➕ Crea Nuova Attività", expanded=True):
            with st.form("academic_task_form"):
                title = st.text_input("Titolo Attività *", key="task_title")
                description = st.text_area("Descrizione", key="task_description")

                col1, col2 = st.columns(2)
                with col1:
                    priority = st.selectbox("Priorità", ["low", "medium", "high"], index=1)
                    task_type = st.selectbox("Tipo", ["short_term", "medium_term", "long_term"])

                with col2:
                    due_date = st.date_input("Scadenza", key="task_due_date")
                    course_id = st.selectbox("Corso Associato", ["Nessuno", "Corso 1", "Corso 2"])  # Placeholder

                submit_col, cancel_col = st.columns(2)
                with submit_col:
                    if st.form_submit_button("✅ Crea Attività", type="primary"):
                        if title.strip():
                            success = self._create_academic_task({
                                'title': title.strip(),
                                'description': description.strip() if description else None,
                                'priority': priority,
                                'task_type': task_type,
                                'due_date': due_date.isoformat(),
                                'course_id': course_id if course_id != "Nessuno" else None
                            })
                            if success:
                                st.success("✅ Attività accademica creata!")
                                st.session_state.show_task_creator = False
                                st.rerun()
                            else:
                                st.error("❌ Errore creazione attività")
                        else:
                            st.error("Il titolo dell'attività è obbligatorio")

                with cancel_col:
                    if st.form_submit_button("❌ Annulla"):
                        st.session_state.show_task_creator = False
                        st.rerun()

    def _create_academic_task(self, task_data: Dict[str, Any]) -> bool:
        """Crea attività accademica."""
        try:
            # Placeholder - in implementazione completa useresti il servizio
            logger.info(f"Creazione attività accademica: {task_data.get('title')}")

            # Aggiungi alla cache locale
            task_data['id'] = len(self.tasks_cache) + 1
            task_data['status'] = 'pending'
            task_data['created_at'] = datetime.now().isoformat()
            self.tasks_cache.append(task_data)

            return True

        except Exception as e:
            logger.error(f"Errore creazione attività accademica: {e}")
            return False

    def refresh_tasks(self):
        """Aggiorna cache attività."""
        try:
            # Placeholder - in implementazione completa useresti il servizio
            self.tasks_cache = []
            logger.info("Cache attività accademica aggiornata")
        except Exception as e:
            logger.error(f"Errore refresh cache attività: {e}")

    def render(self):
        """Render componente principale."""
        # Determina modalità rendering
        if st.session_state.get('show_task_creator', False):
            self.render_task_creator()
        elif st.session_state.get('show_task_manager', False):
            self.render_task_manager()
        else:
            self.render_calendar_view()


def create_academic_planner(on_task_update: Optional[Callable] = None) -> AcademicPlanner:
    """Factory function per creare AcademicPlanner."""
    return AcademicPlanner(on_task_update)
