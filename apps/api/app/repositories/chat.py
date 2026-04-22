from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models import ChatMessage, ChatSession


class ChatRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_session(self, connection_id: str, title: str) -> ChatSession:
        session = ChatSession(connection_id=connection_id, title=title)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: str) -> ChatSession | None:
        stmt = select(ChatSession).where(ChatSession.id == session_id).options(selectinload(ChatSession.messages))
        return self.db.scalars(stmt).first()

    def list_sessions(self, connection_id: str) -> list[ChatSession]:
        stmt = (
            select(ChatSession)
            .where(ChatSession.connection_id == connection_id)
            .options(selectinload(ChatSession.messages))
            .order_by(desc(ChatSession.updated_at))
        )
        return list(self.db.scalars(stmt).unique().all())

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        generated_sql: str | None = None,
        metadata_json: dict | None = None,
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            generated_sql=generated_sql,
            metadata_json=metadata_json,
        )
        self.db.add(message)
        session = self.db.get(ChatSession, session_id)
        if session:
            session.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(message)
        return message
