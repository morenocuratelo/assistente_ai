# Copilot Instructions for Archivista AI

## Project Overview
Archivista AI is a Streamlit-based document analysis and conversational assistant. It leverages LlamaIndex, Ollama LLMs, and custom retrieval logic to answer user queries about uploaded or archived documents, or to engage in general chat.

## Architecture & Key Components
- **main.py**: Entry point and UI logic. Orchestrates document upload, retrieval, chat, and tool selection.
- **config.py**: Service initialization and configuration.
- **prompt_manager.py & prompts.json**: Centralized prompt management for LLMs and routing logic.
- **db_memoria/**: Persistent storage for document vectors, metadata, and indexes.
- **documenti_da_processare/**: Staging area for user-uploaded documents.
- **llama_index.core**: Used for retrieval, indexing, and query processing.
- **Ollama**: Local LLM backend for both chat and document QA.

## Developer Workflows
- **Run the app**: Use `streamlit run main.py` (ensure Ollama is running locally).
- **Add new prompts**: Update `prompts.json` and access via `prompt_manager.get_prompt()`.
- **Index new documents**: Place files in `documenti_da_processare/` and trigger indexing logic (see `get_short_term_retriever`).
- **Long-term storage**: Managed in `db_memoria/` via LlamaIndex APIs.

## Patterns & Conventions
- **Session State**: All user/session-specific state (e.g., uploaded files, focused file, retrievers) is managed via `st.session_state`.
- **Tool Routing**: Queries are routed to either document QA or chat via a manual LLM-based router (see `route_query`).
- **Streaming Responses**: Both chat and QA responses are streamed to the UI for better user experience.
- **Metadata Usage**: Document nodes are tagged with `file_name` for focused retrieval and source attribution.
- **Extensibility**: New tools or engines should be added to the `initialize_ai_components` function and described in the router prompt.

## Integration Points
- **Ollama**: Must be running locally for LLM inference.
- **LlamaIndex**: Used for all retrieval, indexing, and query logic.
- **Streamlit**: UI and session management.

## Example: Adding a New Tool
1. Implement a new QueryEngineTool in `initialize_ai_components`.
2. Add its description to the router prompt in `prompts.json`.
3. Update the output parser if the tool's output structure differs.

## Troubleshooting
- If the app fails to start, check Ollama status and Streamlit logs.
- For retrieval issues, inspect `db_memoria/` contents and session state.

---
For questions about unclear patterns or missing documentation, ask the user for clarification or examples from their workflow.
