"""User profile: age, height, weight, region."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.routers.auth import get_current_user
from app.schemas import UserProfileResponse, UserProfileUpdate

router = APIRouter(prefix="/api/user", tags=["user-profile"])


@router.get("/profile", response_model=UserProfileResponse)
def get_profile(user: User = Depends(get_current_user)):
    """Get current user's profile."""
    return UserProfileResponse(
        age=user.age,
        height_cm=user.height_cm,
        weight_kg=user.weight_kg,
        region=user.region,
        state=user.state,
        city=user.city,
    )


@router.put("/profile", response_model=UserProfileResponse)
def update_profile(body: UserProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update current user's profile."""
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return UserProfileResponse(
        age=user.age,
        height_cm=user.height_cm,
        weight_kg=user.weight_kg,
        region=user.region,
        state=user.state,
        city=user.city,
    )
