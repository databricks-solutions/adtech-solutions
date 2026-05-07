import os
import time
import uuid
from typing import Any, Dict, List, Optional
import logging
import logging

from databricks.sdk import WorkspaceClient
from dash import Dash, Input, Output, State, dcc, html, no_update, ALL, ctx
import dash_bootstrap_components as dbc

from utils.lakebase import get_engine
from utils.databricks_utils import get_workspace_client, get_current_user_name
from models import MessageType
from services.chat_service import ChatService
from services.agent_service import AgentService
from utils.table_formatter import detect_and_format_tables
from utils.token_counter import (
    count_total_tokens,
    get_context_usage_info,
    should_show_warning,
)
from services.task_queue import (
    create_message_id,
    submit_generation,
    submit_streaming_generation,
    submit_save,
    get_generation_buffer,
    get_save_status,
    pop_save_status,
    submit_history_load,
    pop_history_result,
)


# Configure application logging from environment without hardcoding
_log_level_name = (os.getenv("LOG_LEVEL") or os.getenv("PYTHON_LOG_LEVEL") or "INFO").upper()
_log_level = getattr(logging, _log_level_name, logging.INFO)
logging.basicConfig(level=_log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def render_typing_indicator(typing_stage: str) -> html.Div:
    """Render typing indicator UI based on the current stage"""
    if typing_stage == "thinking":
        return html.Div([
            html.Span("🤔", className="me-2"),
            html.Span("Thinking..."),
        ], className=f"typing-indicator {typing_stage}")
    elif typing_stage == "generating":
        return html.Div([
            html.Span("💭", className="me-2"),
            html.Span("Generating"),
            html.Span(className="typing-dots"),
            html.Span(className="typing-cursor"),
        ], className=f"typing-indicator {typing_stage}")
    elif typing_stage == "finishing":
        return html.Div([
            html.Span("✨", className="me-2"),
            html.Span("Finishing up..."),
        ], className=f"typing-indicator {typing_stage}")
    else:
        return html.Div("", className="typing-indicator")


def build_app() -> Dash:
    client: WorkspaceClient = get_workspace_client()
    logger = logging.getLogger(__name__)

    db_name = os.getenv("LAKEBASE_DB_NAME", "adtech-series-db")
    engine = get_engine(client, db_name)

    # Build services per-request/user instead of at import time
    def service_for(user_name: str) -> ChatService:
        return ChatService(engine, user_name)

    agent_service = AgentService()

    app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
        title="AI Chatbot",
    )

    # Configurable client cache TTL (ms), default 1 day
    cache_ttl_ms = int(os.getenv("CHAT_CACHE_TTL_MS", str(24 * 60 * 60 * 1000)))

    def serve_layout():
        # Resolve user within a real request context
        resolved_user = get_current_user_name()
        resolved_cache_ttl_ms = int(os.getenv("CHAT_CACHE_TTL_MS", str(24 * 60 * 60 * 1000)))
        return dbc.Container(
            [
                dcc.Store(id="sessions-store", storage_type="session"),
                dcc.Store(id="chat-store", storage_type="session"),
                dcc.Store(id="chat-cache", storage_type="session"),
                dcc.Store(id="user-store", data={"user": resolved_user}),
                dcc.Store(id="config-store", data={"cacheTtlMs": resolved_cache_ttl_ms}),
                dcc.Store(id="errors-store", data=[]),
                dcc.Store(id="delete-target"),
                dcc.Store(id="scroll-trigger"),
                dcc.Store(id="dashboard-store", data={"isVisible": False}, storage_type="session"),
                dcc.Store(id="column-sizes", data={"chatWidth": 55, "dashboardWidth": 45}, storage_type="session"),
                dcc.Interval(id="tick", interval=int(os.getenv("TICK_SLOW_MS", "2000")), n_intervals=0),
                dcc.Interval(id="sessions-tick", interval=int(os.getenv("SESSIONS_TICK_MS", "10000")), n_intervals=0),

                dbc.Navbar(
                    dbc.Container(
                        [
                            dbc.NavbarBrand("Adtech Series Chat", className="fw-semibold"),
                            dbc.Badge(f"{resolved_user}", color="primary", className="ms-auto"),
                        ],
                        fluid=True,
                    ),
                    color="light",
                    className="rounded-3 shadow-sm my-3",
                ),

                html.Div(
                    [
                        # Sessions column (always fixed width)
                        html.Div(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            html.Div(
                                                [
                                                    html.Span("Chat Sessions", className="fw-semibold"),
                                                    dbc.Button("New", id="new-chat", color="primary", size="sm", className="ms-auto"),
                                                ],
                                                className="d-flex align-items-center gap-2",
                                            )
                                        ),
                                        dbc.CardBody(
                                            [
                                                html.Div(id="sessions-list"),
                                            ]
                                        ),
                                    ],
                                    className="shadow-sm",
                                ),
                            ],
                            className="sessions-column",
                        ),
                        # Resizable content area
                        html.Div(
                            [
                                # Chat column (resizable)
                                html.Div(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardHeader(
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    html.Span("AI Chatbot", className="h5 mb-0"),
                                                                    html.Span(id="current-chat-title", className="text-muted ms-2 small"),
                                                                ],
                                                                className="d-flex align-items-center gap-2",
                                                            ),
                                                            html.Div(
                                                                [
                                                                    dbc.Button(
                                                                        "Show Dashboard",
                                                                        id="toggle-dashboard",
                                                                        color="info",
                                                                        size="sm",
                                                                        outline=True,
                                                                        className="me-2",
                                                                    ),
                                                                    dbc.Button(
                                                                        "AI Rename",
                                                                        id="ai-rename",
                                                                        color="secondary",
                                                                        size="sm",
                                                                        outline=True,
                                                                    ),
                                                                ],
                                                                className="d-flex align-items-center",
                                                            ),
                                                        ],
                                                        className="d-flex align-items-center justify-content-between",
                                                    )
                                                ),
                                                dbc.CardBody(
                                                    [
                                                        html.Div(id="context-warning", className="mb-2"),
                                                        html.Div(id="chat-transcript", className="chat-transcript"),
                                                    ]
                                                ),
                                                dbc.CardFooter(
                                                    dbc.InputGroup(
                                                        [
                                                            dcc.Input(
                                                                id="chat-input",
                                                                placeholder="Type your message...",
                                                                type="text",
                                                                className="form-control",
                                                            ),
                                                            dbc.Button("Send", id="send", color="primary"),
                                                        ],
                                                        className="chat-input-group",
                                                    )
                                                ),
                                            ],
                                            className="shadow-sm",
                                        ),
                                        html.Div(id="toasts"),
                                    ],
                                    id="chat-column",
                                ),
                                # Splitter handle
                                html.Div(
                                    className="column-splitter",
                                    id="column-splitter",
                                    style={"display": "none"}
                                ),
                                # Dashboard column (resizable)
                                html.Div(
                                    [
                                        html.Div(id="dashboard-panel"),
                                    ],
                                    id="dashboard-column",
                                    style={"display": "none"},
                                ),
                            ],
                            id="resizable-content",
                            className="resizable-content-area",
                        ),
                    ],
                    id="main-layout",
                    className="main-layout-container",
                ),
                # Global delete confirmation modal
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle(id="delete-modal-title")),
                        dbc.ModalBody(id="delete-modal-body"),
                        dbc.ModalFooter([
                            dbc.Button("Cancel", id="cancel-delete", className="ms-auto", outline=True),
                            dbc.Button("Delete", id="confirm-delete", color="danger"),
                        ]),
                    ],
                    id="delete-confirm-modal",
                    is_open=False,
                    backdrop=True,
                ),
            ],
            fluid=True,
            className="py-2",
        )

    app.layout = serve_layout

    # Load sessions on startup
    @app.callback(
        Output("sessions-store", "data"),
        Input("sessions-tick", "n_intervals"),
        State("sessions-store", "data"),
        State("user-store", "data"),
        prevent_initial_call=False,
    )
    def refresh_sessions(_: int, existing: Optional[List[Dict[str, Any]]], user_data: Optional[Dict[str, Any]] = None):
        # Periodically refresh sessions in the background so new chats appear without page reload
        def _load_sessions() -> List[Dict[str, Any]]:
            user_name = (user_data or {}).get("user") or get_current_user_name()
            raw = service_for(user_name).get_user_chats()
            return [{"id": s.id, "title": s.title or "Untitled"} for s in raw]

        submit_history_load("__sessions__", _load_sessions)
        logger.debug("refresh_sessions: queued background sessions load (had_existing=%s)", bool(existing))
        # Never overwrite the store with None; let the tick callback set data when ready
        return no_update

    @app.callback(
        Output("sessions-list", "children"),
        Input("sessions-store", "data"),
        Input("chat-store", "data"),
    )
    def render_sessions(sessions: Optional[List[Dict[str, Any]]], chat_state: Optional[Dict[str, Any]]):
        current_chat_id = (chat_state or {}).get("currentChatId") if chat_state else None
        # Do not show a spinner if the store hasn't been explicitly cleared to None
        # We only render spinner when store has no data object yet AND no previous data
        if sessions is None:
            return dbc.Spinner(size="sm", children=" Loading chats...")
        if not sessions:
            return html.Div("No chats yet")
        rows = []
        for s in sessions:
            color = "secondary" if s["id"] != current_chat_id else "primary"
            rows.append(
                html.Div(
                    [
                        dbc.Button(
                            s.get("title") or "Untitled",
                            id={"type": "chat-select", "id": s["id"]},
                            color=color,
                            className="flex-grow-1",
                        ),
                        dbc.Button(
                            "🗑️",
                            id={"type": "chat-delete", "id": s["id"]},
                            color="danger",
                            outline=True,
                            size="sm",
                            className="ms-2",
                        ),
                    ],
                    className="d-flex mb-2",
                )
            )
        return rows

    # Show current chat title in header
    @app.callback(
        Output("current-chat-title", "children"),
        Input("sessions-store", "data"),
        Input("chat-store", "data"),
    )
    def render_current_title(sessions: Optional[List[Dict[str, Any]]], chat_state: Optional[Dict[str, Any]]):
        if not chat_state or not chat_state.get("currentChatId"):
            return ""
        current_chat_id = chat_state.get("currentChatId")
        if not sessions:
            return ""
        for s in sessions:
            if s.get("id") == current_chat_id:
                title = s.get("title") or "Untitled"
                return f"— {title}"
        return ""

    # Toggle dashboard visibility
    @app.callback(
        Output("dashboard-store", "data", allow_duplicate=True),
        Output("toggle-dashboard", "children"),
        Input("toggle-dashboard", "n_clicks"),
        State("dashboard-store", "data"),
        prevent_initial_call=True,
    )
    def toggle_dashboard(_: Optional[int], dashboard_state: Optional[Dict[str, Any]]):
        if not dashboard_state:
            dashboard_state = {"isVisible": False}

        current_visible = dashboard_state.get("isVisible", False)
        new_visible = not current_visible

        button_text = "Hide Dashboard" if new_visible else "Show Dashboard"

        return {"isVisible": new_visible}, button_text

    # Render dashboard panel and manage layout
    @app.callback(
        Output("dashboard-panel", "children"),
        Output("dashboard-column", "style"),
        Output("column-splitter", "style"),
        Output("resizable-content", "className"),
        Input("dashboard-store", "data"),
        State("column-sizes", "data"),
    )
    def render_dashboard_panel(dashboard_state: Optional[Dict[str, Any]], column_sizes: Optional[Dict[str, Any]]):
        if not dashboard_state or not dashboard_state.get("isVisible", False):
            return [], {"display": "none"}, {"display": "none"}, "resizable-content-area"

        # Get column sizes or use defaults
        sizes = column_sizes or {"chatWidth": 55, "dashboardWidth": 45}
        chat_width = sizes.get("chatWidth", 55)
        dashboard_width = sizes.get("dashboardWidth", 45)

        dashboard_url = os.getenv("DASHBOARD_IFRAME")
        if not dashboard_url:
            dashboard_content = dbc.Card(
                [
                    dbc.CardHeader("Dashboard"),
                    dbc.CardBody(
                        dbc.Alert(
                            "Dashboard URL not configured. Please set the DASHBOARD_IFRAME environment variable.",
                            color="warning",
                            className="mb-0"
                        )
                    )
                ],
                className="shadow-sm h-100"
            )
        else:
            dashboard_content = dbc.Card(
                [
                    dbc.CardHeader("Databricks Dashboard"),
                    dbc.CardBody(
                        html.Iframe(
                            src=dashboard_url,
                            style={
                                "width": "100%",
                                "border": "none",
                                "borderRadius": "8px"
                            },
                            className="dashboard-iframe"
                        ),
                        className="p-2"
                    )
                ],
                className="shadow-sm h-100"
            )

        # Set CSS custom properties for column widths
        dashboard_style = {
            "display": "block",
            "--dashboard-width": f"{dashboard_width}%"
        }

        splitter_style = {"display": "block"}

        resizable_class = f"resizable-content-area active-resize chat-width-{chat_width} dashboard-width-{dashboard_width}"

        return dashboard_content, dashboard_style, splitter_style, resizable_class

    # Handle column resizing with clientside callback
    app.clientside_callback(
        """
        function(dashboard_state, column_sizes) {
            console.log('Drag resize callback triggered', dashboard_state);

            // Only initialize if dashboard is visible
            if (!dashboard_state || !dashboard_state.isVisible) {
                console.log('Dashboard not visible, skipping initialization');
                return window.dash_clientside.no_update;
            }

            // Use setTimeout to ensure DOM is ready
            setTimeout(function() {
                console.log('Initializing drag resize functionality');

                // Initialize resize functionality
                const splitter = document.getElementById('column-splitter');
                const chatColumn = document.getElementById('chat-column');
                const dashboardColumn = document.getElementById('dashboard-column');
                const resizableContent = document.getElementById('resizable-content');

                if (!splitter || !chatColumn || !dashboardColumn || !resizableContent) {
                    console.warn('Missing DOM elements for resize:', {
                        splitter: !!splitter,
                        chatColumn: !!chatColumn,
                        dashboardColumn: !!dashboardColumn,
                        resizableContent: !!resizableContent
                    });
                    return;
                }

                // Clean up old event listeners
                if (splitter.dataset.initialized) {
                    console.log('Cleaning up existing event listeners');
                    splitter.removeEventListener('mousedown', window.startResize);
                    splitter.removeEventListener('dblclick', window.resetSizes);
                }

                let isResizing = false;
                let startX = 0;
                let startChatWidth = 0;
                let startDashboardWidth = 0;

                // Get current widths from CSS custom properties
                function getCurrentWidths() {
                    const root = document.documentElement;
                    const chatWidthStr = getComputedStyle(root).getPropertyValue('--chat-column-width').trim();
                    const dashboardWidthStr = getComputedStyle(root).getPropertyValue('--dashboard-column-width').trim();

                    const chatWidth = parseFloat(chatWidthStr);
                    const dashboardWidth = parseFloat(dashboardWidthStr);

                    console.log('Current widths:', { chatWidth, dashboardWidth });
                    return { chatWidth, dashboardWidth };
                }

                // Update CSS custom properties
                function updateColumnWidths(chatWidth, dashboardWidth) {
                    const root = document.documentElement;
                    root.style.setProperty('--chat-column-width', chatWidth + '%');
                    root.style.setProperty('--dashboard-column-width', dashboardWidth + '%');
                    console.log('Updated column widths:', { chatWidth, dashboardWidth });
                }

                // Start resize
                function startResize(e) {
                    console.log('Starting resize');
                    isResizing = true;
                    startX = e.clientX;
                    const widths = getCurrentWidths();
                    startChatWidth = widths.chatWidth;
                    startDashboardWidth = widths.dashboardWidth;

                    document.addEventListener('mousemove', doResize);
                    document.addEventListener('mouseup', stopResize);
                    document.body.style.cursor = 'col-resize';
                    document.body.style.userSelect = 'none';

                    // Visual feedback
                    splitter.style.background = 'linear-gradient(to right, rgba(255, 54, 33, 0.2) 0%, rgba(255, 54, 33, 0.4) 50%, rgba(255, 54, 33, 0.2) 100%)';

                    e.preventDefault();
                }

                // Do resize
                function doResize(e) {
                    if (!isResizing) return;

                    const deltaX = e.clientX - startX;
                    const containerWidth = resizableContent.offsetWidth;
                    const deltaPercent = (deltaX / containerWidth) * 100;

                    let newChatWidth = startChatWidth + deltaPercent;
                    let newDashboardWidth = startDashboardWidth - deltaPercent;

                    // Apply constraints
                    newChatWidth = Math.max(30, Math.min(70, newChatWidth));
                    newDashboardWidth = Math.max(25, Math.min(60, newDashboardWidth));

                    // Ensure total is close to 100%
                    const total = newChatWidth + newDashboardWidth;
                    if (Math.abs(total - 100) > 0.1) {
                        const adjustment = (100 - total) / 2;
                        newChatWidth += adjustment;
                        newDashboardWidth += adjustment;
                    }

                    // Update CSS custom properties
                    updateColumnWidths(newChatWidth, newDashboardWidth);

                    // Store in sessionStorage for persistence
                    try {
                        const sizes = { chatWidth: newChatWidth, dashboardWidth: newDashboardWidth };
                        sessionStorage.setItem('column-sizes', JSON.stringify(sizes));
                    } catch (err) {
                        console.warn('Failed to save to sessionStorage:', err);
                    }
                }

                // Stop resize
                function stopResize() {
                    if (!isResizing) return;
                    console.log('Stopping resize');

                    isResizing = false;
                    document.removeEventListener('mousemove', doResize);
                    document.removeEventListener('mouseup', stopResize);
                    document.body.style.cursor = '';
                    document.body.style.userSelect = '';

                    // Remove visual feedback
                    splitter.style.background = '';
                }

                // Double-click to reset to defaults
                function resetSizes() {
                    console.log('Resetting to default sizes');
                    updateColumnWidths(55, 45);
                    try {
                        const sizes = { chatWidth: 55, dashboardWidth: 45 };
                        sessionStorage.setItem('column-sizes', JSON.stringify(sizes));
                    } catch (err) {
                        console.warn('Failed to save reset to sessionStorage:', err);
                    }
                }

                // Store functions globally for cleanup
                window.startResize = startResize;
                window.resetSizes = resetSizes;

                // Attach event listeners
                splitter.addEventListener('mousedown', startResize);
                splitter.addEventListener('dblclick', resetSizes);
                splitter.dataset.initialized = 'true';

                // Load saved sizes on initialization
                try {
                    const saved = sessionStorage.getItem('column-sizes');
                    if (saved) {
                        const sizes = JSON.parse(saved);
                        console.log('Loading saved sizes:', sizes);
                        updateColumnWidths(sizes.chatWidth, sizes.dashboardWidth);
                    }
                } catch (err) {
                    console.warn('Failed to load from sessionStorage:', err);
                }

                console.log('Drag resize initialization complete');
            }, 100);

            return window.dash_clientside.no_update;
        }
        """,
        Output("column-sizes", "data"),
        Input("dashboard-store", "data"),
        State("column-sizes", "data"),
    )

    # Create new chat
    @app.callback(
        Output("chat-store", "data", allow_duplicate=True),
        Output("sessions-store", "data", allow_duplicate=True),
        Input("new-chat", "n_clicks"),
        State("sessions-store", "data"),
        State("user-store", "data"),
        prevent_initial_call=True,
    )
    def new_chat(_: int, sessions_data: Optional[List[Dict[str, Any]]], user_data: Optional[Dict[str, Any]] = None):
        new_id = str(uuid.uuid4())
        user_name = (user_data or {}).get("user") or get_current_user_name()
        service_for(user_name).create_new_chat_session(new_id)
        # Optimistically add the new chat to the sessions list so it shows immediately
        existing_sessions = sessions_data or []
        optimistic_sessions = [{"id": new_id, "title": "Untitled"}] + existing_sessions
        return {"currentChatId": new_id, "messages": []}, optimistic_sessions

    # Select chat
    @app.callback(
        Output("chat-store", "data", allow_duplicate=True),
        Input({"type": "chat-select", "id": ALL}, "n_clicks"),
        State("sessions-store", "data"),
        State("chat-cache", "data"),
        State("user-store", "data"),
        prevent_initial_call=True,
    )
    def select_chat(_: List[Optional[int]], sessions_data: List[Dict[str, Any]], cache_state: Optional[Dict[str, Any]], user_data: Optional[Dict[str, Any]] = None):
        # Fire only on a real button click (n_clicks > 0). Pattern-matching inputs
        # can trigger when components are created; guard against that.
        trigger = ctx.triggered_id
        if not trigger or not ctx.triggered or not isinstance(ctx.triggered, list):
            return no_update
        try:
            triggered_value = ctx.triggered[0].get("value", 0)
        except Exception:
            triggered_value = 0
        if not triggered_value:
            return no_update
        selected_id = trigger.get("id")
        if not selected_id:
            return no_update

        # Kick off background load for history to keep UI responsive
        def _load() -> List[Dict[str, Any]]:
            user_name = (user_data or {}).get("user") or get_current_user_name()
            history = service_for(user_name).load_chat_history(selected_id)
            msgs: List[Dict[str, Any]] = []
            for m in history:
                msgs.append({
                    "id": str(uuid.uuid4()),
                    "role": "user" if m.message_type == MessageType.USER else "assistant",
                    "content": m.message_content,
                    "order": m.message_order,
                    "saved": True,
                    "error": None,
                })
            msgs.sort(key=lambda x: x.get("order", 0))
            return msgs

        submit_history_load(selected_id, _load)
        logger.debug("select_chat: selected_id=%s queued load", selected_id)

        # If we have cached messages for this chat, show them immediately while background refresh runs
        try:
            chats_cache = (cache_state or {}).get("chats") if isinstance(cache_state, dict) else None
            if isinstance(chats_cache, dict) and selected_id in chats_cache:
                cached_entry = chats_cache.get(selected_id) or {}
                cached_messages = cached_entry.get("messages") or []
                updated_at = cached_entry.get("updatedAt") or 0
                now_ms = int(time.time() * 1000)
                ttl_ms = cache_ttl_ms
                try:
                    updated_at = int(updated_at)
                except Exception:
                    updated_at = 0
                if (now_ms - updated_at) <= ttl_ms:
                    return {"currentChatId": selected_id, "messages": cached_messages, "isLoading": True}
        except Exception:
            pass

        # Fallback: show loading indicator
        return {"currentChatId": selected_id, "messages": [], "isLoading": True}

    # Render transcript
    @app.callback(
        Output("chat-transcript", "children"),
        Input("chat-store", "data"),
    )
    def render_transcript(chat_state: Optional[Dict[str, Any]]):
        if chat_state and chat_state.get("isLoading") and not chat_state.get("messages"):
            return dbc.Spinner(size="sm", children=" Loading chat history...")
        if not chat_state or not chat_state.get("messages"):
            return html.Div("Welcome! Start a new chat or select an existing one.", className="text-muted")
        elements = []
        for m in sorted(chat_state["messages"], key=lambda x: x.get("order", 0)):
            is_user = m["role"] == "user"
            meta_bits = []
            if not m.get("saved", True):
                meta_bits.append("unsaved")
            if m.get("error"):
                meta_bits.append(f"error: {m['error']}")
            meta = f" {' • '.join(meta_bits)}" if meta_bits else ""
            
            # Handle typing indicators for assistant messages
            is_typing = not is_user and m.get("typing_stage") and not m.get("content")
            typing_stage = m.get("typing_stage")
            
            if is_typing:
                # Render typing indicator based on stage
                typing_content = render_typing_indicator(typing_stage)
                message_content = html.Div(typing_content, className="chat-bubble assistant typing")
            else:
                # Regular message content
                if m.get("content"):
                    message_content = dcc.Markdown(
                        m["content"],
                        className=f"chat-bubble {'user' if is_user else 'assistant'}",
                        link_target="_blank",
                    )
                else:
                    # Empty assistant message (placeholder)
                    message_content = html.Div("", className=f"chat-bubble {'user' if is_user else 'assistant'}")
                    
            elements.append(
                html.Div(
                    [
                        html.Div("You" if is_user else "Assistant", className="message-meta small text-muted"),
                        message_content,
                        html.Div(meta, className="message-status small text-muted"),
                    ],
                    className=f"message-row {'from-user' if is_user else 'from-assistant'}",
                )
            )
        # Sentinel div used by clientside callback to scroll to bottom
        elements.append(html.Div(id="scroll-anchor"))
        return elements

    # Render context warning
    @app.callback(
        Output("context-warning", "children"),
        Input("chat-store", "data"),
    )
    def render_context_warning(chat_state: Optional[Dict[str, Any]]):
        """Display context usage warning when approaching token limits."""
        if not chat_state or not chat_state.get("messages"):
            return ""
        
        # Get configuration values
        chat_context_limit_str = os.getenv("CHAT_CONTEXT_LIMIT", "5")
        try:
            chat_context_limit = int(chat_context_limit_str)
        except ValueError:
            chat_context_limit = 5
            
        # Only show warning for token-based limiting
        if chat_context_limit != 0:
            return ""
            
        context_window_size_str = os.getenv("CONTEXT_WINDOW_SIZE", "200000")
        try:
            context_window_size = int(context_window_size_str)
        except ValueError:
            context_window_size = 200000
            
        context_warning_threshold_str = os.getenv("CONTEXT_WARNING_THRESHOLD", "0.9")
        try:
            context_warning_threshold = float(context_warning_threshold_str)
        except ValueError:
            context_warning_threshold = 0.9
        
        # Convert messages to ChatMessage-like objects for token counting
        messages = []
        for m in chat_state["messages"]:
            if m.get("content"):
                # Create a simple object with content attribute for token counting
                class MessageStub:
                    def __init__(self, content):
                        self.content = content
                messages.append(MessageStub(m["content"]))
        
        # System prompt (same as in agent service)
        system_prompt = (
            """
        You are a helpful assistant that can answer questions and help with tasks, you are also able to search the chat history for relevant information.
        If the user asks a question that is not related to the chat history, you shouldn't mention you couldn't find anything related to the question.
        """
        ).strip()
        
        # Calculate current token usage
        current_tokens = count_total_tokens(system_prompt, messages)
        usage_info = get_context_usage_info(current_tokens, context_window_size)
        
        # Show warning if needed
        if not usage_info["show_warning"]:
            return ""
        
        # Create warning UI based on usage level
        if usage_info["status"] == "critical":
            color = "danger"
            icon = "⚠️"
            message = f"Context nearly full! Using {usage_info['usage_percentage']}% ({current_tokens:,}/{context_window_size:,} tokens). Older messages may be trimmed."
        else:
            color = "warning"
            icon = "ℹ️"
            message = f"Context usage high: {usage_info['usage_percentage']}% ({current_tokens:,}/{context_window_size:,} tokens)."
        
        return dbc.Alert(
            [
                html.Span(icon, className="me-2"),
                html.Span(message),
            ],
            color=color,
            is_open=True,
            fade=False,
            className="mb-0 py-2",
        )

    # Send message
    @app.callback(
        Output("chat-store", "data", allow_duplicate=True),
        Output("errors-store", "data", allow_duplicate=True),
        Output("chat-input", "value"),
        Input("send", "n_clicks"),
        Input("chat-input", "n_submit"),
        State("chat-input", "value"),
        State("chat-store", "data"),
        State("user-store", "data"),
        prevent_initial_call=True,
    )
    def send_message(_: Optional[int], __: Optional[int], text: Optional[str], chat_state: Optional[Dict[str, Any]], user_data: Optional[Dict[str, Any]] = None):
        if not text:
            return no_update, no_update, no_update
        if not chat_state or not chat_state.get("currentChatId"):
            return no_update, no_update, no_update

        chat_id = chat_state["currentChatId"]
        messages = chat_state.get("messages", []).copy()

        # Determine next order locally for snappier UX
        next_order = (max((m.get("order", -1) for m in messages), default=-1) + 1)

        # Create user message
        user_message_id = create_message_id()
        user_message = {
            "id": user_message_id,
            "role": "user",
            "content": text,
            "order": next_order,
            "saved": False,
            "saving": True,
            "error": None,
        }
        messages.append(user_message)

        # Placeholder assistant message
        assistant_message_id = create_message_id()
        assistant_message = {
            "id": assistant_message_id,
            "role": "assistant",
            "content": "",
            "order": next_order + 1,
            "saved": False,
            "error": None,
        }
        messages.append(assistant_message)

        # Background save for user message
        def save_user():
            user_name = (user_data or {}).get("user") or get_current_user_name()
            service_for(user_name).save_message_with_embedding(chat_id, MessageType.USER, text, next_order)

        submit_save(user_message_id, save_user)
        logger.debug("send_message: queued save user_message_id=%s order=%s", user_message_id, next_order)

        # Background streaming generation
        def generate_stream():
            # Build agent input from transcript including the new user msg
            from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
            history_msgs = []
            for m in sorted(messages, key=lambda x: x["order"]):
                role = ChatMessageRole.USER if m["role"] == "user" else ChatMessageRole.ASSISTANT
                history_msgs.append(ChatMessage(role=role, content=m["content"]))
            user_name_local = (user_data or {}).get("user") or get_current_user_name()
            return agent_service.generate_bot_response_stream(user_name_local, history_msgs)

        # Use streaming generation
        submit_streaming_generation(assistant_message_id, generate_stream)
        logger.debug("send_message: queued generation assistant_message_id=%s", assistant_message_id)

        new_state = {"currentChatId": chat_id, "messages": messages}
        return new_state, no_update, ""

    # Open delete confirmation modal
    @app.callback(
        Output("delete-target", "data"),
        Output("delete-modal-title", "children"),
        Output("delete-modal-body", "children"),
        Output("delete-confirm-modal", "is_open"),
        Input({"type": "chat-delete", "id": ALL}, "n_clicks"),
        State("sessions-store", "data"),
        prevent_initial_call=True,
    )
    def open_delete_modal(_: List[Optional[int]], sessions: Optional[List[Dict[str, Any]]]):
        trigger = ctx.triggered_id
        # Only respond to actual clicks (>0). Avoid firing on initial render or list refreshes.
        if not trigger or not ctx.triggered or not isinstance(ctx.triggered, list):
            return no_update, no_update, no_update, no_update
        try:
            triggered_value = ctx.triggered[0].get("value", 0)
        except Exception:
            triggered_value = 0
        if not triggered_value:
            return no_update, no_update, no_update, no_update
        target_id = trigger.get("id")
        if not target_id:
            return no_update, no_update, no_update, no_update
        title = None
        for s in sessions or []:
            if s.get("id") == target_id:
                title = s.get("title") or "this chat"
                break
        modal_title = f"Delete '{title}'?" if title else "Delete this chat?"
        modal_body = "This will permanently delete the conversation."
        return target_id, modal_title, modal_body, True

    # Confirm delete
    @app.callback(
        Output("sessions-store", "data", allow_duplicate=True),
        Output("chat-store", "data", allow_duplicate=True),
        Output("delete-confirm-modal", "is_open", allow_duplicate=True),
        Output("delete-target", "data", allow_duplicate=True),
        Input("confirm-delete", "n_clicks"),
        State("delete-target", "data"),
        State("sessions-store", "data"),
        State("chat-store", "data"),
        State("user-store", "data"),
        prevent_initial_call=True,
    )
    def confirm_delete(_: Optional[int], target_id: Optional[str], sessions: Optional[List[Dict[str, Any]]], chat_state: Optional[Dict[str, Any]] , user_data: Optional[Dict[str, Any]] = None):
        if not target_id:
            return no_update, no_update, False, None
        try:
            user_name = (user_data or {}).get("user") or get_current_user_name()
            service_for(user_name).delete_chat_session(target_id)
        except Exception as e:
            logging.getLogger(__name__).warning("Failed to delete chat %s: %s", target_id, e)
        # Update sessions list locally
        new_sessions = [s for s in (sessions or []) if s.get("id") != target_id]
        # Reset current chat if it was deleted
        if chat_state and chat_state.get("currentChatId") == target_id:
            new_chat_state = {"currentChatId": None, "messages": []}
        else:
            new_chat_state = no_update
        return new_sessions, new_chat_state, False, None

    # Cancel delete
    @app.callback(
        Output("delete-confirm-modal", "is_open", allow_duplicate=True),
        Output("delete-target", "data", allow_duplicate=True),
        Input("cancel-delete", "n_clicks"),
        prevent_initial_call=True,
    )
    def cancel_delete(_: Optional[int]):
        return False, None

    # Provide immediate visual feedback while deletion is in-flight
    @app.callback(
        Output("confirm-delete", "children"),
        Output("confirm-delete", "disabled"),
        Output("cancel-delete", "disabled"),
        Input("confirm-delete", "n_clicks"),
        Input("delete-confirm-modal", "is_open"),
        prevent_initial_call=False,
    )
    def toggle_delete_loading(n_clicks: Optional[int], is_open: bool):
        # When the modal has just been opened, always reset the button state
        try:
            if ctx.triggered_id == "delete-confirm-modal" and is_open:
                return "Delete", False, False
        except Exception:
            pass

        # When modal is open and user has clicked delete at least once, show loading state
        if is_open and (n_clicks or 0) > 0:
            return "Deleting...", True, True
        # Default state
        return "Delete", False, False

    # AI Rename current chat using first up to 5 messages
    @app.callback(
        Output("sessions-store", "data", allow_duplicate=True),
        Input("ai-rename", "n_clicks"),
        State("chat-store", "data"),
        State("sessions-store", "data"),
        State("user-store", "data"),
        prevent_initial_call=True,
    )
    def ai_rename_chat(_: Optional[int], chat_state: Optional[Dict[str, Any]], sessions_data: Optional[List[Dict[str, Any]]], user_data: Optional[Dict[str, Any]] = None):
        if not chat_state or not chat_state.get("currentChatId"):
            return no_update
        chat_id = chat_state["currentChatId"]
        try:
            user_name = (user_data or {}).get("user") or get_current_user_name()
            new_title = service_for(user_name).generate_chat_title(chat_id)
        except Exception:
            return no_update
        # Optimistically update local sessions list
        updated_sessions: List[Dict[str, Any]] = []
        for s in (sessions_data or []):
            if s.get("id") == chat_id:
                updated_sessions.append({**s, "title": new_title or s.get("title") or "Untitled"})
            else:
                updated_sessions.append(s)
        return updated_sessions

    # Tick: integrate stream/progress and save results
    @app.callback(
        Output("chat-store", "data", allow_duplicate=True),
        Output("errors-store", "data", allow_duplicate=True),
        Output("sessions-store", "data", allow_duplicate=True),
        Output("tick", "interval"),
        Input("tick", "n_intervals"),
        State("chat-store", "data"),
        State("errors-store", "data"),
        State("sessions-store", "data"),
        State("user-store", "data"),
        prevent_initial_call="initial_duplicate",
    )
    def tick(_: int, chat_state: Optional[Dict[str, Any]], errors_state: Optional[List[Dict[str, Any]]], sessions_data: Optional[List[Dict[str, Any]]], user_data: Optional[Dict[str, Any]] = None):
        fast_ms = int(os.getenv("TICK_FAST_MS", "150"))
        slow_ms = int(os.getenv("TICK_SLOW_MS", "2000"))
        next_interval_ms = slow_ms
        if not chat_state:
            # Still allow sessions update via background fetch
            loaded_sessions = pop_history_result("__sessions__")
            if loaded_sessions is not None:
                logger.debug("tick: loaded sessions=%d", len(loaded_sessions))
                return no_update, no_update, loaded_sessions, next_interval_ms
            return no_update, no_update, no_update, next_interval_ms

        # Integrate background history load completion
        loaded_history = None
        current_chat_id = chat_state.get("currentChatId") if chat_state else None
        if current_chat_id:
            loaded_history = pop_history_result(current_chat_id)

        # Integrate background sessions load completion
        loaded_sessions = pop_history_result("__sessions__")

        messages = chat_state.get("messages", []).copy()
        errors_list = (errors_state or []).copy()

        changed = False
        has_active_generation = False
        has_pending_save = False

        if loaded_history is not None:
            messages = loaded_history
            changed = True
            # Clear loading flag explicitly in the next state we return
            if chat_state.get("isLoading"):
                chat_state = {**chat_state, "isLoading": False}
            logger.debug("tick: merged history messages=%d for chat_id=%s", len(messages), current_chat_id)

        # Process streaming updates and completion
        for m in messages:
            if m["role"] != "assistant":
                continue
            buf = get_generation_buffer(m["id"])
            if buf is None:
                continue
            if not buf.is_done:
                has_active_generation = True

            # Update typing stage
            current_typing_stage = buf.typing_stage
            if current_typing_stage != m.get("typing_stage"):
                m["typing_stage"] = current_typing_stage
                changed = True

            # Update content
            full_text = buf.read_all()
            if full_text != m["content"]:
                m["content"] = full_text
                changed = True
                # Clear typing stage when content starts appearing
                if full_text and m.get("typing_stage"):
                    m.pop("typing_stage", None)

            if buf.is_done:
                # Clear typing stage when done
                if m.get("typing_stage"):
                    m.pop("typing_stage", None)
                    changed = True
                # Apply post-processing (e.g., TSV -> Markdown tables) once final text is ready
                try:
                    formatted_final = detect_and_format_tables(m.get("content") or "")
                    if formatted_final != m.get("content"):
                        m["content"] = formatted_final
                        changed = True
                except Exception:
                    pass
                    
                if buf.error and not m.get("error"):
                    m["error"] = buf.error
                    changed = True
                # When done and no error, trigger background save if not already saved
                if not m.get("error") and not m.get("saved") and m.get("content") and not m.get("saving", False):
                    order_val = m.get("order", 0)

                    def save_assistant(chat_id=chat_state["currentChatId"], content=m["content"], order_val=order_val, user_data=user_data):
                        user_name_inner = (user_data or {}).get("user") or get_current_user_name()
                        service_for(user_name_inner).save_message_with_embedding(chat_id, MessageType.ASSISTANT, content, order_val)

                    submit_save(m["id"], save_assistant)
                    logger.debug("tick: queued save assistant_message_id=%s", m["id"])
                    m["saving"] = True
                    changed = True

        # Process save statuses
        for m in messages:
            status = pop_save_status(m["id"])  # read-once
            if not status:
                if m.get("saving") and not m.get("saved"):
                    has_pending_save = True
                continue
            if status.ok:
                m["saved"] = True
                m["saving"] = False
                m["error"] = None
                logger.debug("tick: save success message_id=%s", m["id"])
                changed = True
            else:
                # Surface non-blocking error
                m["saved"] = False
                m["saving"] = False
                m["error"] = status.error or "Failed to save"
                errors_list.append({"messageId": m["id"], "stage": "save", "error": m["error"]})
                logger.debug("tick: save error message_id=%s error=%s", m["id"], m["error"])
                changed = True

        if has_active_generation or has_pending_save or chat_state.get("isLoading"):
            next_interval_ms = fast_ms
        else:
            next_interval_ms = slow_ms

        if not changed and loaded_sessions is None:
            return no_update, no_update, no_update, next_interval_ms

        # Only update sessions-store when we actually fetched new sessions.
        # Make loaded sessions authoritative to avoid re-adding deleted items from stale state
        sessions_out = no_update
        if loaded_sessions is not None:
            try:
                existing_by_id = {s.get("id"): s for s in (sessions_data or []) if s and s.get("id")}
                loaded_by_id = {s.get("id"): s for s in (loaded_sessions or []) if s and s.get("id")}
                # Start with loaded (authoritative)
                merged: List[Dict[str, Any]] = []
                # Preserve loaded order
                for s in loaded_sessions:
                    sid = s.get("id")
                    # If we had a local title change, keep the newer title if present
                    if sid in existing_by_id and existing_by_id[sid].get("title") and not s.get("title"):
                        merged.append({**s, "title": existing_by_id[sid].get("title")})
                    else:
                        merged.append(s)
                sessions_out = merged
            except Exception:
                sessions_out = loaded_sessions

        next_chat_state = {"currentChatId": current_chat_id, "messages": messages}
        # Preserve explicit isLoading=False once we have loaded history
        if chat_state.get("isLoading") and loaded_history is not None:
            next_chat_state["isLoading"] = False

        logger.debug("tick: state updated messages=%d errors=%d sessions_updated=%s", len(messages), len(errors_list), sessions_out is not no_update)
        return next_chat_state, errors_list, sessions_out, next_interval_ms

    # Render errors as toasts
    @app.callback(
        Output("toasts", "children"),
        Input("errors-store", "data"),
    )
    def render_toasts(errors_data: Optional[List[Dict[str, Any]]]):
        if not errors_data:
            return []
        items = []
        for e in errors_data[-3:]:  # show last few
            items.append(
                dbc.Toast(
                    [html.Div(f"Latest message failed to commit to history: {e.get('error','unknown error')}")],
                    header="Save Error",
                    icon="danger",
                    dismissable=True,
                    is_open=True,
                    duration=4000,
                    style={"position": "relative", "minWidth": "300px", "marginTop": "0.5rem"},
                )
            )
        return items

    # Auto-scroll transcript to bottom only when a thread is loaded AND the user is near the bottom
    app.clientside_callback(
        """
        function(children, chatState){
            try {
                // Only when a chat thread is selected
                if (!chatState || !chatState.currentChatId) {
                    return window.dash_clientside.no_update;
                }

                var el = document.getElementById('chat-transcript');
                if (!el) {
                    return window.dash_clientside.no_update;
                }

                // Reset userScrolled when switching chats
                try {
                    var currentId = chatState.currentChatId || '';
                    if (el.dataset.chatId !== currentId) {
                        el.dataset.chatId = currentId;
                        el.dataset.userScrolled = 'false';
                    }
                } catch (e) {}

                // Attach a one-time listener to detect manual scrolling intent
                try {
                    if (!el.dataset.scrollListenerAttached) {
                        el.addEventListener('scroll', function(){
                            try {
                                var gapNow = el.scrollHeight - el.scrollTop - el.clientHeight;
                                var atBottom = gapNow < 2;
                                if (atBottom) {
                                    el.dataset.userScrolled = 'false';
                                } else {
                                    el.dataset.userScrolled = 'true';
                                }
                            } catch (e) {}
                        }, { passive: true });
                        el.dataset.scrollListenerAttached = 'true';
                    }
                } catch (e) {}

                var anchor = document.getElementById('scroll-anchor');
                var bottomGap = el.scrollHeight - el.scrollTop - el.clientHeight;
                var userScrolled = el.dataset.userScrolled === 'true';

                // Initial load for selected chat: if at top and content present and no manual scroll yet, force scroll
                var hasContent = Array.isArray(children) ? children.length > 0 : !!children;
                if (!userScrolled && hasContent && el.scrollTop <= 1) {
                    if (anchor && anchor.scrollIntoView) {
                        anchor.scrollIntoView({behavior: 'auto', block: 'end'});
                    } else {
                        el.scrollTop = el.scrollHeight;
                    }
                    return 0;
                }

                // Keep auto-scrolling only when user is near bottom
                var isNearBottom = bottomGap < 5; // px threshold
                if (isNearBottom) {
                    if (anchor && anchor.scrollIntoView) {
                        anchor.scrollIntoView({behavior: 'auto', block: 'end'});
                    } else {
                        el.scrollTop = el.scrollHeight;
                    }
                    return 0;
                }

                return window.dash_clientside.no_update;
            } catch (e) {
                return window.dash_clientside.no_update;
            }
        }
        """,
        Output("scroll-trigger", "data"),
        Input("chat-transcript", "children"),
        State("chat-store", "data"),
    )

    # Keep a lightweight per-chat client-side cache to instantly render previously opened chats.
    # This stores only in the user's browser (localStorage) and is scoped per-user.
    app.clientside_callback(
        """
        function(chatState, cacheData, userData, configData){
            try {
                if (!chatState || !chatState.currentChatId || !Array.isArray(chatState.messages)) {
                    return window.dash_clientside.no_update;
                }
                var owner = (userData && userData.user) || null;
                var cache = cacheData || {};
                if (!cache.chats || cache.owner !== owner) {
                    cache = { owner: owner, chats: {} };
                }
                var chatId = chatState.currentChatId;
                var messages = chatState.messages.slice();
                cache.chats[chatId] = { messages: messages, updatedAt: Date.now() };
                var TTL_MS = (configData && configData.cacheTtlMs) || (24 * 60 * 60 * 1000); // default 1 day
                var now = Date.now();
                try {
                    // Prune stale entries beyond TTL
                    Object.keys(cache.chats || {}).forEach(function(k){
                        try {
                            var ua = (cache.chats[k] && cache.chats[k].updatedAt) || 0;
                            if ((now - ua) > TTL_MS) {
                                delete cache.chats[k];
                            }
                        } catch (e) {}
                    });
                } catch (e) {}
                // Cap cache size to the most recent 10 chats
                try {
                    var keys = Object.keys(cache.chats || {});
                    if (keys.length > 12) {
                        keys.sort(function(a,b){
                            var ba = (cache.chats[b] && cache.chats[b].updatedAt) || 0;
                            var aa = (cache.chats[a] && cache.chats[a].updatedAt) || 0;
                            return ba - aa;
                        });
                        for (var i = 10; i < keys.length; i++) {
                            delete cache.chats[keys[i]];
                        }
                    }
                } catch (e) {}
                return cache;
            } catch (e) {
                return window.dash_clientside.no_update;
            }
        }
        """,
        Output("chat-cache", "data"),
        Input("chat-store", "data"),
        State("chat-cache", "data"),
        State("user-store", "data"),
        State("config-store", "data"),
    )

    return app


app = build_app()
server = app.server


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run_server(host="0.0.0.0", port=port, debug=True)


