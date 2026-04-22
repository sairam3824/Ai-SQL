from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_connection_or_404
from app.db.session import get_db
from app.repositories import ChatRepository
from app.schemas.chat import ChatSessionCreateRequest, ChatSessionResponse, SessionSummary
from app.services.chat_service import to_session_response, to_session_summary

router = APIRouter()


@router.get("/connections/{connection_id}/sessions", response_model=list[SessionSummary])
def list_sessions(connection=Depends(get_connection_or_404), db: Session = Depends(get_db)):
    repo = ChatRepository(db)
    return [to_session_summary(session) for session in repo.list_sessions(connection.id)]


@router.post("/connections/{connection_id}/sessions", response_model=ChatSessionResponse)
def create_session(
    payload: ChatSessionCreateRequest,
    connection=Depends(get_connection_or_404),
    db: Session = Depends(get_db),
):
    repo = ChatRepository(db)
    title = payload.title or "New analysis"
    session = repo.create_session(connection.id, title)
    session = repo.get_session(session.id)
    return to_session_response(session)


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    repo = ChatRepository(db)
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    return to_session_response(session)
