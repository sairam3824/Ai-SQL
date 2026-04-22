from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import ConnectionRepository
from app.services.connection_service import ConnectionService


def get_connection_or_404(connection_id: str, db: Session = Depends(get_db)):
    repo = ConnectionRepository(db)
    connection = repo.get_connection(connection_id)
    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found.")
    return connection


def get_connection_service() -> ConnectionService:
    return ConnectionService()
