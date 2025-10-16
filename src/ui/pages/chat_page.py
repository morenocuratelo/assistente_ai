"""
Chat page implementation using new UI components.
Enhanced chat interface with consistent styling and advanced features.
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_page import PageTemplate, get_session_state, set_session_state
from ..components.base import ComponentFactory
from ...core.errors.error_handler import handle_error


class ChatPage(PageTemplate):
    """Enhanced chat page with modern UI components."""

    def __init__(self):
        """Initialize chat page."""
        super().__init__("chat", "💬 AI Chat")
        self.components = ComponentFactory()
        self.messages: List[Dict[str, Any]] = []
        self.current_session_id: Optional[str] = None

    def get_page_icon(self) -> str:
        return "💬"

    def get_page_description(self) -> str:
        return "Chat with your documents using AI"

    def get_navigation_items(self) -> List[Dict[str, Any]]:
        return [
            {'id': 'chat', 'label': '💬 New Chat', 'help': 'Start new conversation', 'active': True},
            {'id': 'history', 'label': '📚 Chat History', 'help': 'Previous conversations'},
            {'id': 'documents', 'label': '📄 Document Chat', 'help': 'Chat with specific documents'},
            {'id': 'settings', 'label': '⚙️ Chat Settings', 'help': 'Configure chat preferences'},
        ]

    def render_content(self) -> None:
        """Render chat page content."""
        # Chat interface
        self._render_chat_interface()

        # Sidebar with chat history and settings
        self._render_chat_sidebar()

    def _render_chat_interface(self) -> None:
        """Render main chat interface."""
        # Chat header
        st.markdown("### 🤖 AI Assistant")

        # Chat messages area
        self._render_messages_area()

        # Message input
        self._render_message_input()

    def _render_messages_area(self) -> None:
        """Render chat messages area."""
        # Messages container
        messages_container = st.container()

        with messages_container:
            if not self.messages:
                # Welcome message
                self._render_welcome_message()
            else:
                # Render messages
                self._render_chat_messages()

    def _render_welcome_message(self) -> None:
        """Render welcome message for new chat."""
        card = self.components.get_card()

        welcome_content = """
        👋 **Welcome to AI Chat!**

        I'm your intelligent assistant, ready to help you with:

        - 📚 **Document Analysis**: Ask questions about your uploaded documents
        - 🔍 **Information Retrieval**: Find specific information across your archive
        - 📝 **Content Creation**: Help generate new content based on your documents
        - 🎯 **Task Planning**: Organize your study tasks and schedules
        - 🧠 **Knowledge Discovery**: Explore connections between different topics

        **Start by:**
        1. Uploading documents to your archive
        2. Asking questions about your content
        3. Exploring connections between topics

        What would you like to explore today?
        """

        card.render(
            "🤖 AI Assistant",
            welcome_content,
            "welcome_message",
            icon="🤖"
        )

    def _render_chat_messages(self) -> None:
        """Render chat messages."""
        for message in self.messages:
            self._render_single_message(message)

    def _render_single_message(self, message: Dict[str, Any]) -> None:
        """Render single chat message."""
        role = message.get('role', 'user')
        content = message.get('content', '')
        timestamp = message.get('timestamp', datetime.utcnow())

        if role == 'user':
            # User message styling
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: flex-end;
                margin: 1rem 0;
            ">
                <div style="
                    background: #1f77b4;
                    color: white;
                    padding: 0.75rem 1rem;
                    border-radius: 18px;
                    max-width: 70%;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    <div>{content}</div>
                    <div style="
                        font-size: 0.75rem;
                        opacity: 0.8;
                        margin-top: 0.25rem;
                        text-align: right;
                    ">
                        {timestamp.strftime('%H:%M')}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        else:
            # AI message styling
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: flex-start;
                margin: 1rem 0;
            ">
                <div style="
                    background: #f8f9fa;
                    color: #333;
                    padding: 0.75rem 1rem;
                    border-radius: 18px;
                    max-width: 70%;
                    border: 1px solid #e0e0e0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                ">
                    <div>{content}</div>
                    <div style="
                        font-size: 0.75rem;
                        opacity: 0.8;
                        margin-top: 0.25rem;
                        text-align: right;
                    ">
                        🤖 AI • {timestamp.strftime('%H:%M')}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    def _render_message_input(self) -> None:
        """Render message input area."""
        # Input form
        with st.form("chat_input_form"):
            col1, col2 = st.columns([4, 1])

            with col1:
                user_input = st.text_input(
                    "Type your message...",
                    key="chat_input",
                    placeholder="Ask me anything about your documents...",
                    help="Type your question or message here"
                )

            with col2:
                # Send button
                send_button = st.form_submit_button(
                    "Send",
                    type="primary"
                )

                # Quick action buttons
                st.markdown("**Quick Actions:**")

                action_col1, action_col2 = st.columns(2)

                with action_col1:
                    if st.form_submit_button("📄 Summarize", type="secondary"):
                        user_input = "Please summarize the main points of my documents"

                with action_col2:
                    if st.form_submit_button("🔍 Search", type="secondary"):
                        user_input = "Search for information in my documents"

        # Process input
        if send_button and user_input.strip():
            self._process_user_message(user_input.strip())

    def _process_user_message(self, message: str) -> None:
        """Process user message."""
        try:
            # Add user message to chat
            user_message = {
                'role': 'user',
                'content': message,
                'timestamp': datetime.utcnow()
            }
            self.messages.append(user_message)

            # Generate AI response (simplified)
            ai_response = self._generate_ai_response(message)

            # Add AI response to chat
            ai_message = {
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.utcnow()
            }
            self.messages.append(ai_message)

            # Store in session state
            set_session_state('chat_messages', self.messages)

            # Rerun to update display
            st.rerun()

        except Exception as e:
            handle_error(e, operation="process_user_message", component="chat_page")
            self.add_error_message("Error processing message")

    def _generate_ai_response(self, user_message: str) -> str:
        """Generate AI response to user message."""
        # This would integrate with actual AI service
        # For now, return mock response

        responses = {
            'hello': "Hello! I'm your AI assistant. How can I help you with your documents today?",
            'summarize': "I'll help you summarize your documents. Which documents would you like me to focus on?",
            'search': "I can search through your document archive. What specific information are you looking for?",
            'help': "I'm here to help! You can ask me questions about your documents, request summaries, or explore connections between topics.",
        }

        message_lower = user_message.lower()

        for key, response in responses.items():
            if key in message_lower:
                return response

        # Default response
        return f"I understand you said: '{user_message}'. I'm your AI assistant and I'm here to help you with your documents. You can ask me to summarize content, search for information, or explore connections between topics."

    def _render_chat_sidebar(self) -> None:
        """Render chat sidebar with history and settings."""
        # Chat sessions
        self._render_chat_sessions()

        # Quick document access
        self._render_document_quick_access()

        # Chat settings
        self._render_chat_settings()

    def _render_chat_sessions(self) -> None:
        """Render chat sessions list."""
        st.markdown("### 📚 Chat History")

        # Mock chat sessions
        sessions = [
            {'id': '1', 'title': 'Document Analysis', 'last_message': '2 hours ago', 'message_count': 15},
            {'id': '2', 'title': 'Study Planning', 'last_message': '1 day ago', 'message_count': 8},
            {'id': '3', 'title': 'Research Questions', 'last_message': '3 days ago', 'message_count': 22},
        ]

        for session in sessions:
            col1, col2 = st.columns([3, 1])

            with col1:
                if st.button(
                    f"💬 {session['title']}",
                    key=f"session_{session['id']}",
                    help=f"{session['message_count']} messages • {session['last_message']}"
                ):
                    self._load_chat_session(session['id'])

            with col2:
                if st.button("🗑️", key=f"delete_session_{session['id']}", help="Delete session"):
                    self._delete_chat_session(session['id'])

    def _render_document_quick_access(self) -> None:
        """Render quick access to recent documents."""
        st.markdown("### 📄 Recent Documents")

        # Mock recent documents
        documents = [
            {'name': 'Machine Learning Notes.pdf', 'category': 'AI'},
            {'name': 'Statistics Summary.docx', 'category': 'Math'},
            {'name': 'Research Paper.pdf', 'category': 'Academic'},
        ]

        for doc in documents:
            if st.button(
                f"📄 {doc['name']}",
                key=f"quick_doc_{doc['name']}",
                help=f"Category: {doc['category']}"
            ):
                # Set context to this document
                set_session_state('chat_context_document', doc['name'])
                self.add_success_message(f"Context set to: {doc['name']}")

    def _render_chat_settings(self) -> None:
        """Render chat settings."""
        st.markdown("### ⚙️ Chat Settings")

        # AI Model selection
        model = st.selectbox(
            "AI Model",
            options=['llama3', 'gpt-3.5-turbo', 'claude-3'],
            key="chat_model",
            help="Select AI model for responses"
        )

        # Response style
        style = st.selectbox(
            "Response Style",
            options=['concise', 'detailed', 'conversational'],
            key="chat_style",
            help="Choose response style"
        )

        # Context inclusion
        include_context = st.checkbox(
            "Include Document Context",
            value=True,
            key="chat_include_context",
            help="Include relevant document content in responses"
        )

        # Save settings
        if st.button("💾 Save Settings", key="save_chat_settings"):
            settings = {
                'model': model,
                'style': style,
                'include_context': include_context
            }
            set_session_state('chat_settings', settings)
            self.add_success_message("Chat settings saved")

    def _load_chat_session(self, session_id: str) -> None:
        """Load existing chat session."""
        try:
            # This would load session from database
            # For now, just set current session
            self.current_session_id = session_id
            set_session_state('current_chat_session', session_id)

            # Load messages for session
            # self.messages = self._get_session_messages(session_id)

            self.add_success_message(f"Loaded chat session: {session_id}")

        except Exception as e:
            handle_error(e, operation="load_chat_session", component="chat_page")
            self.add_error_message("Error loading chat session")

    def _delete_chat_session(self, session_id: str) -> None:
        """Delete chat session."""
        try:
            # This would delete session from database
            self.add_success_message(f"Chat session {session_id} deleted")
            st.rerun()

        except Exception as e:
            handle_error(e, operation="delete_chat_session", component="chat_page")
            self.add_error_message("Error deleting chat session")

    def render_sidebar_content(self) -> None:
        """Render chat-specific sidebar content."""
        super().render_sidebar_content()

        # Chat-specific metrics
        st.markdown("### 📊 Chat Metrics")

        # Mock metrics
        metrics = {
            'Total Conversations': 12,
            'Messages This Week': 45,
            'AI Response Time': '1.2s avg',
            'Documents Referenced': 8
        }

        for key, value in metrics.items():
            st.metric(key, value)

        # Quick document upload
        st.markdown("### 📤 Quick Upload")

        if st.button("📤 Upload Document for Chat", key="quick_upload_chat"):
            st.switch_page("main.py")

        # Chat tips
        with st.expander("💡 Chat Tips", expanded=False):
            st.markdown("""
            **Tips for better AI responses:**
            - Be specific in your questions
            - Mention document names when relevant
            - Ask follow-up questions for clarification
            - Use keywords from your documents
            """)

    def get_status_info(self) -> Optional[str]:
        """Get current chat status."""
        session_id = get_session_state('current_chat_session')
        if session_id:
            return f"Active session: {session_id}"
        return "No active chat session"

    def get_page_metrics(self) -> Optional[Dict[str, Any]]:
        """Get chat-specific metrics."""
        return {
            'Active Session': get_session_state('current_chat_session', 'None'),
            'Messages': len(self.messages),
            'AI Model': get_session_state('chat_settings', {}).get('model', 'llama3'),
            'Context Documents': len(get_session_state('chat_context_documents', []))
        }


class DocumentChatPage(PageTemplate):
    """Chat page focused on specific documents."""

    def __init__(self):
        """Initialize document chat page."""
        super().__init__("document_chat", "📄 Document Chat")
        self.selected_documents: List[str] = []

    def get_page_icon(self) -> str:
        return "📄"

    def get_page_description(self) -> str:
        return "Chat with specific documents in your archive"

    def render_content(self) -> None:
        """Render document chat content."""
        # Document selection
        self._render_document_selection()

        # Chat interface with document context
        self._render_document_chat()

    def _render_document_selection(self) -> None:
        """Render document selection interface."""
        st.markdown("### 📚 Select Documents for Chat")

        # Document search
        search_query = st.text_input(
            "Search documents...",
            key="doc_chat_search",
            placeholder="Find documents to chat with..."
        )

        # Mock document list
        documents = [
            {'name': 'Machine Learning Notes.pdf', 'category': 'AI', 'date': '2024-01-15'},
            {'name': 'Statistics Summary.docx', 'category': 'Math', 'date': '2024-01-14'},
            {'name': 'Research Paper.pdf', 'category': 'Academic', 'date': '2024-01-13'},
            {'name': 'Python Tutorial.txt', 'category': 'Programming', 'date': '2024-01-12'},
        ]

        # Filter documents based on search
        if search_query:
            documents = [
                doc for doc in documents
                if search_query.lower() in doc['name'].lower()
            ]

        # Document selection
        st.markdown("**Available Documents:**")

        cols = st.columns(2)

        for i, doc in enumerate(documents):
            col_idx = i % 2

            with cols[col_idx]:
                selected = st.checkbox(
                    f"📄 {doc['name']}",
                    key=f"doc_select_{doc['name']}",
                    help=f"Category: {doc['category']} • Date: {doc['date']}"
                )

                if selected:
                    if doc['name'] not in self.selected_documents:
                        self.selected_documents.append(doc['name'])
                else:
                    if doc['name'] in self.selected_documents:
                        self.selected_documents.remove(doc['name'])

        if self.selected_documents:
            st.success(f"Selected {len(self.selected_documents)} documents for chat")
        else:
            st.info("Select documents to start chatting")

    def _render_document_chat(self) -> None:
        """Render document-focused chat interface."""
        if not self.selected_documents:
            st.info("👆 Select documents above to start chatting")
            return

        st.markdown(f"### 💬 Chat with {len(self.selected_documents)} Documents")

        # Show selected documents
        with st.expander("📚 Selected Documents", expanded=False):
            for doc_name in self.selected_documents:
                st.markdown(f"• {doc_name}")

        # Chat interface (similar to main chat)
        self._render_document_chat_input()

    def _render_document_chat_input(self) -> None:
        """Render chat input for document chat."""
        with st.form("document_chat_form"):
            user_input = st.text_area(
                "Ask about your documents...",
                height=100,
                key="document_chat_input",
                placeholder="What would you like to know about these documents?"
            )

            col1, col2 = st.columns([1, 1])

            with col1:
                if st.form_submit_button("💬 Ask AI", type="primary"):
                    if user_input.strip():
                        self._process_document_chat(user_input.strip())

            with col2:
                if st.form_submit_button("📄 Summarize Documents"):
                    self._process_document_chat("Please summarize the main points of these documents")

    def _process_document_chat(self, message: str) -> None:
        """Process document-focused chat message."""
        try:
            # This would integrate with AI service using selected documents as context
            response = f"Based on the {len(self.selected_documents)} documents you've selected, I'll help you with: {message[:50]}..."

            # Add to chat (simplified)
            set_session_state('document_chat_response', response)
            st.rerun()

        except Exception as e:
            handle_error(e, operation="process_document_chat", component="document_chat_page")
            self.add_error_message("Error processing document chat")


class ChatHistoryPage(PageTemplate):
    """Chat history and management page."""

    def __init__(self):
        """Initialize chat history page."""
        super().__init__("chat_history", "📚 Chat History")

    def get_page_icon(self) -> str:
        return "📚"

    def get_page_description(self) -> str:
        return "Browse and manage your chat history"

    def render_content(self) -> None:
        """Render chat history content."""
        st.markdown("### 📚 Chat History")

        # History filters
        self._render_history_filters()

        # Chat sessions list
        self._render_chat_sessions()

    def _render_history_filters(self) -> None:
        """Render history filters."""
        col1, col2, col3 = st.columns(3)

        with col1:
            date_filter = st.selectbox(
                "Time Period",
                options=['all', 'today', 'week', 'month'],
                format_func=lambda x: {
                    'all': '📅 All Time',
                    'today': '📅 Today',
                    'week': '📅 This Week',
                    'month': '📅 This Month'
                }.get(x, x),
                key="history_date_filter"
            )

        with col2:
            type_filter = st.selectbox(
                "Chat Type",
                options=['all', 'document', 'general', 'planning'],
                format_func=lambda x: {
                    'all': '💬 All Chats',
                    'document': '📄 Document Chats',
                    'general': '💬 General Chats',
                    'planning': '📋 Planning Chats'
                }.get(x, x),
                key="history_type_filter"
            )

        with col3:
            if st.button("🔍 Search History", key="search_history"):
                st.info("History search would be implemented here")

    def _render_chat_sessions(self) -> None:
        """Render chat sessions list."""
        # Mock chat sessions with more details
        sessions = [
            {
                'id': '1',
                'title': 'Machine Learning Discussion',
                'preview': 'Can you explain neural networks in simple terms?',
                'date': '2024-01-15 14:30',
                'message_count': 12,
                'type': 'document'
            },
            {
                'id': '2',
                'title': 'Study Schedule Planning',
                'preview': 'Help me create a study schedule for exams',
                'date': '2024-01-14 09:15',
                'message_count': 8,
                'type': 'planning'
            },
            {
                'id': '3',
                'title': 'Document Analysis',
                'preview': 'What are the main findings in this research paper?',
                'date': '2024-01-13 16:45',
                'message_count': 15,
                'type': 'document'
            },
        ]

        for session in sessions:
            with st.expander(f"💬 {session['title']} ({session['message_count']} messages)", expanded=False):
                st.markdown(f"**Last message:** {session['preview']}")
                st.caption(f"Date: {session['date']}")

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("💬 Continue", key=f"continue_{session['id']}"):
                        self._continue_chat_session(session['id'])

                with col2:
                    if st.button("📤 Export", key=f"export_{session['id']}"):
                        self._export_chat_session(session['id'])

                with col3:
                    if st.button("🗑️ Delete", key=f"delete_history_{session['id']}"):
                        self._delete_chat_session(session['id'])

    def _continue_chat_session(self, session_id: str) -> None:
        """Continue existing chat session."""
        set_session_state('current_chat_session', session_id)
        st.switch_page("pages/1_Chat.py")

    def _export_chat_session(self, session_id: str) -> None:
        """Export chat session."""
        self.add_success_message(f"Chat session {session_id} exported")

    def _delete_chat_session(self, session_id: str) -> None:
        """Delete chat session."""
        self.add_success_message(f"Chat session {session_id} deleted")
        st.rerun()


# Page factory for chat pages

def create_chat_page(page_type: str = "main") -> PageTemplate:
    """Create chat page based on type.

    Args:
        page_type: Type of chat page (main, document, history)

    Returns:
        Chat page template
    """
    if page_type == "document":
        return DocumentChatPage()
    elif page_type == "history":
        return ChatHistoryPage()
    else:
        return ChatPage()


# Convenience function for getting chat page

def get_chat_page() -> ChatPage:
    """Get main chat page instance."""
    return ChatPage()
