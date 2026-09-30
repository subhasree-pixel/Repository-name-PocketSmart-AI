from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
)

from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.history import RecommendationHistory
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    TokenResponse,
    UserOut,
)


router = APIRouter(
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=UserOut,
    status_code=201,
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):

    email = data.email.lower()

    existing_user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered",
        )

    user = User(
        email=email,
        full_name=data.full_name.strip(),
        password_hash=hash_password(
            data.password
        ),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/login",
    response_model=UserOut,
)
def login(
    data: OAuth2PasswordRequestForm = Depends(),
    response: Response = None,
    db: Session = Depends(get_db),
):

    email = data.username.lower()

    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = create_access_token(
        str(user.id)
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24,
    )

    return user


@router.post(
    "/token",
    response_model=TokenResponse,
)
def token(
    data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):

    email = data.username.lower()

    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    return TokenResponse(
        access_token=create_access_token(
            str(user.id)
        )
    )


@router.post("/logout")
def logout(response: Response):

    response.delete_cookie(
        key="access_token"
    )

    return {
        "message": "Logged out successfully"
    }


@router.get("/session-info")
def session_info(
    user: User = Depends(get_current_user),
):

    return {
        "authenticated": True,
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
    }


@router.get("/session-data")
def session_data(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    count = (
        db.query(RecommendationHistory)
        .filter(
            RecommendationHistory.user_id
            == user.id
        )
        .count()
    )

    return {
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "recommendation_count": count,
    }