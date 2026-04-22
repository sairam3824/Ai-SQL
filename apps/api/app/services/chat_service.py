from app.repositories import ChatRepository
from app.schemas.chat import ChatMessageResponse, ChatSessionResponse, SessionSummary


def session_title_from_question(question: str) -> str:
    trimmed = " ".join(question.split())
    return trimmed[:72] or "New analysis"


def to_message_response(message) -> ChatMessageResponse:
    return ChatMessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        generated_sql=message.generated_sql,
        metadata=message.metadata_json,
        created_at=message.created_at,
    )


def to_session_response(session) -> ChatSessionResponse:
    return ChatSessionResponse(
        id=session.id,
        connection_id=session.connection_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[to_message_response(message) for message in session.messages],
    )


def to_session_summary(session) -> SessionSummary:
    last_message = session.messages[-1] if session.messages else None
    return SessionSummary(
        id=session.id,
        connection_id=session.connection_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        last_message=to_message_response(last_message) if last_message else None,
    )


def get_or_create_session(chat_repo: ChatRepository, connection_id: str, session_id: str | None, question: str):
    if session_id:
        session = chat_repo.get_session(session_id)
        if session:
            return session
    return chat_repo.create_session(connection_id, session_title_from_question(question))
