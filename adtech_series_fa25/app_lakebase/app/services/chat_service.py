from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from utils.databricks_utils import get_workspace_client
from services.embeddings_service import generate_embedding, get_embedding_model_name
from models import ChatHistory, MessageType, ChatSession, MessageEmbedding


class ChatService:
    """
    Encapsulates business logic for chat sessions, messages, titles, and embeddings.
    The UI should call into this service rather than interacting with the database directly.
    """

    def __init__(self, engine, current_user: str):
        self.engine = engine
        self.current_user = current_user

    # ---------- Sessions ----------
    def get_user_chats(self) -> List[ChatSession]:
        with Session(self.engine) as session:
            chat_sessions = (
                session.query(ChatSession)
                .filter(ChatSession.user_name == self.current_user)
                .order_by(desc(ChatSession.updated_at))
                .all()
            )
            return chat_sessions

    def create_new_chat_session(self, chat_id: str) -> ChatSession:
        with Session(self.engine) as session:
            chat_session = ChatSession(
                id=chat_id,
                user_name=self.current_user,
                title=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(chat_session)
            session.commit()
            return chat_session

    def delete_chat_session(self, session_id: str) -> bool:
        with Session(self.engine) as session:
            chat_session = (
                session.query(ChatSession)
                .filter(
                    ChatSession.id == session_id,
                    ChatSession.user_name == self.current_user,
                )
                .first()
            )
            if chat_session:
                session.delete(chat_session)
                session.commit()
                return True
            return False

    def _update_session_timestamp(self, session_id: str) -> None:
        with Session(self.engine) as session:
            chat_session = (
                session.query(ChatSession)
                .filter(
                    ChatSession.id == session_id,
                    ChatSession.user_name == self.current_user,
                )
                .first()
            )
            if chat_session:
                chat_session.updated_at = datetime.utcnow()
                session.commit()

    # ---------- Titles ----------
    def _generate_title_with_llama(self, context_text: str) -> str:
        try:
            client = get_workspace_client()

            title_prompt = (
                """Generate a concise title for this conversation in exactly 15 words or fewer. Return only the title, no quotes, no explanations:

%s

Title:"""
                % context_text
            )

            message_dicts = [
                {
                    "role": "user",
                    "content": title_prompt,
                }
            ]

            payload = {
                "messages": message_dicts,
                "max_tokens": 50,
                "temperature": 0.1,
            }

            payload_json = json.dumps(payload)

            response = client.api_client.do(
                method="POST",
                path="/serving-endpoints/databricks-meta-llama-3-3-70b-instruct/invocations",
                headers={"Content-Type": "application/json"},
                data=payload_json,
            )

            if isinstance(response, list) and len(response) > 0:
                title = response[0].strip()
            elif isinstance(response, dict) and "choices" in response:
                title = response["choices"][0]["message"]["content"].strip()
            else:
                title = str(response).strip()

            title = title.strip().strip('"').strip("'").strip()
            prefixes_to_remove = [
                "Title:",
                "title:",
                "TITLE:",
                "Generated title:",
                "The title is:",
                "Here's a title:",
            ]
            for prefix in prefixes_to_remove:
                if title.lower().startswith(prefix.lower()):
                    title = title[len(prefix) :].strip()

            words = title.split()
            if len(words) > 15:
                title = " ".join(words[:15])

            if len(title) > 60:
                title = title[:57] + "..."

            return title if title else "New Chat"
        except Exception:
            return "New Chat"

    def generate_chat_title(self, session_id: str) -> str:
        try:
            with Session(self.engine) as session:
                messages = (
                    session.query(ChatHistory)
                    .filter(
                        ChatHistory.chat_id == session_id,
                        ChatHistory.user_name == self.current_user,
                    )
                    .order_by(ChatHistory.message_order)
                    .limit(5)
                    .all()
                )

                if len(messages) == 0:
                    return "New Chat"

                context_parts: List[str] = []
                for msg in messages:
                    role = "User" if msg.message_type == MessageType.USER else "Assistant"
                    context_parts.append(f"{role}: {msg.message_content[:150]}...")
                context_text = "\n".join(context_parts)

                title = self._generate_title_with_llama(context_text)

                chat_session = (
                    session.query(ChatSession)
                    .filter(
                        ChatSession.id == session_id,
                        ChatSession.user_name == self.current_user,
                    )
                    .first()
                )
                if chat_session:
                    chat_session.title = title
                    chat_session.updated_at = datetime.utcnow()
                    session.commit()

                return title
        except Exception:
            try:
                with Session(self.engine) as session:
                    first_message = (
                        session.query(ChatHistory)
                        .filter(
                            ChatHistory.chat_id == session_id,
                            ChatHistory.user_name == self.current_user,
                            ChatHistory.message_type == MessageType.USER,
                        )
                        .order_by(ChatHistory.message_order)
                        .first()
                    )
                    if first_message:
                        fallback_title = (
                            first_message.message_content[:30] + "..."
                            if len(first_message.message_content) > 30
                            else first_message.message_content
                        )
                        chat_session = (
                            session.query(ChatSession)
                            .filter(
                                ChatSession.id == session_id,
                                ChatSession.user_name == self.current_user,
                            )
                            .first()
                        )
                        if chat_session:
                            chat_session.title = fallback_title
                            session.commit()
                        return fallback_title
            except Exception:
                pass
            return "New Chat"

    # ---------- Messages ----------
    def load_chat_history(self, chat_id: str) -> List[ChatHistory]:
        with Session(self.engine) as session:
            messages = (
                session.query(ChatHistory)
                .filter(
                    ChatHistory.chat_id == chat_id,
                    ChatHistory.user_name == self.current_user,
                )
                .order_by(ChatHistory.message_order)
                .all()
            )
            return messages

    def save_message(self, chat_id: str, message_type: MessageType, content: str, message_order: int) -> None:
        with Session(self.engine) as session:
            # Idempotency guard: skip if message already exists
            existing = (
                session.query(ChatHistory)
                .filter(
                    ChatHistory.chat_id == chat_id,
                    ChatHistory.user_name == self.current_user,
                    ChatHistory.message_type == message_type,
                    ChatHistory.message_order == message_order,
                )
                .first()
            )
            if existing:
                return

            message = ChatHistory(
                chat_id=chat_id,
                user_name=self.current_user,
                message_type=message_type,
                message_content=content,
                message_order=message_order,
            )
            session.add(message)
            session.commit()

        self._update_session_timestamp(chat_id)

        if message_order >= 3:
            try:
                with Session(self.engine) as session:
                    chat_session = (
                        session.query(ChatSession)
                        .filter(
                            ChatSession.id == chat_id,
                            ChatSession.user_name == self.current_user,
                        )
                        .first()
                    )
                    if chat_session and not chat_session.title:
                        self.generate_chat_title(chat_id)
            except Exception:
                pass

    def save_message_with_embedding(
        self,
        chat_id: str,
        message_type: MessageType,
        content: str,
        message_order: int,
    ) -> None:
        embedding_vector = generate_embedding(content)
        model_name = get_embedding_model_name()

        with Session(self.engine) as session:
            with session.begin():
                # Idempotency guard: skip if message already exists
                existing = (
                    session.query(ChatHistory)
                    .filter(
                        ChatHistory.chat_id == chat_id,
                        ChatHistory.user_name == self.current_user,
                        ChatHistory.message_type == message_type,
                        ChatHistory.message_order == message_order,
                    )
                    .first()
                )
                if existing:
                    # Optionally update content if it's different (assistant finalization), but avoid re-inserting
                    if existing.message_content != content:
                        existing.message_content = content
                    # Ensure session timestamp is current
                    chat_session = session.get(ChatSession, chat_id)
                    if chat_session:
                        chat_session.updated_at = datetime.utcnow()
                    return

                message = ChatHistory(
                    chat_id=chat_id,
                    user_name=self.current_user,
                    message_type=message_type,
                    message_content=content,
                    message_order=message_order,
                )
                session.add(message)
                session.flush()

                embedding_row = MessageEmbedding(
                    message_id=message.id,
                    chat_id=chat_id,
                    user_name=self.current_user,
                    model_name=model_name,
                    embedding=embedding_vector,
                    created_at=datetime.utcnow(),
                )
                session.add(embedding_row)

                chat_session = session.get(ChatSession, chat_id)
                if chat_session:
                    chat_session.updated_at = datetime.utcnow()

        # Auto-generate a title once the conversation has a few messages, if not already titled
        try:
            if message_order >= 1:
                with Session(self.engine) as session:
                    chat_session = (
                        session.query(ChatSession)
                        .filter(
                            ChatSession.id == chat_id,
                            ChatSession.user_name == self.current_user,
                        )
                        .first()
                    )
                    if chat_session and not chat_session.title:
                        # Will set and persist the title internally
                        self.generate_chat_title(chat_id)
        except Exception:
            # Non-blocking best-effort
            pass

    def get_next_message_order(self, chat_id: str) -> int:
        with Session(self.engine) as session:
            last_message = (
                session.query(ChatHistory)
                .filter(
                    ChatHistory.chat_id == chat_id,
                    ChatHistory.user_name == self.current_user,
                )
                .order_by(desc(ChatHistory.message_order))
                .first()
            )
            return (last_message.message_order + 1) if last_message else 1


