from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from backend.api import deps
from backend.core.security import create_access_token
from backend.models import User, UserRole
from backend.services.emby import emby_client
from backend.db import get_session

router = APIRouter()

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    try:
        # Authenticate with Emby
        emby_auth_response = await emby_client.authenticate(form_data.username, form_data.password)
        emby_user_id = emby_auth_response["User"]["Id"]
        emby_user_name = emby_auth_response["User"]["Name"]
        is_admin = emby_auth_response["User"]["Policy"]["IsAdministrator"]

        # Sync user to local DB
        user = session.get(User, emby_user_id)
        if not user:
            user = User(
                id=emby_user_id,
                name=emby_user_name,
                role=UserRole.ADMIN if is_admin else UserRole.USER
            )
            session.add(user)
        else:
            # Update role/name if changed
            user.name = emby_user_name
            user.role = UserRole.ADMIN if is_admin else UserRole.USER
            session.add(user)
        
        session.commit()
        session.refresh(user)

        access_token = create_access_token(subject=user.id)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }

    except Exception as e:
        print(f"Authentication error: {e}") # Log to console for debugging
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(deps.get_current_user)) -> Any:
    """
    Get current user.
    """
    return current_user


