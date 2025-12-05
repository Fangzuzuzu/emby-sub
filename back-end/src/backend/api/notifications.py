from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from backend.api import deps
from backend.db import get_session
from backend.models import User, Notification

router = APIRouter()

@router.get("/", response_model=List[Notification])
def read_notifications(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(deps.get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    statement = select(Notification).where(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    return session.exec(statement).all()

@router.put("/{notification_id}/read", response_model=Notification)
def mark_read(
    notification_id: int,
    current_user: User = Depends(deps.get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    notification = session.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your notification")
    
    notification.is_read = True
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification
