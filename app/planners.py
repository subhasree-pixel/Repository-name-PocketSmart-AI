from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.history import RecommendationHistory
from app.models.user import User
from app.schemas.planners import (
    HomeRequest,
    PartyRequest,
    JewelryRequest,
    RecommendationResponse,
)
from app.services.recommender import (
    generate_home,
    generate_party,
    generate_jewelry,
)


router = APIRouter(
    tags=["Planners"]
)

settings = get_settings()


async def read_image(
    file: UploadFile | None,
):
    """
    Validate and read optional jewelry image.
    """

    if not file:
        return None

    if not file.filename:
        return None

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=(
                "Outfit image must be "
                "JPEG, PNG, or WEBP."
            ),
        )

    image_data = await file.read()

    max_bytes = (
        settings.max_upload_mb
        * 1024
        * 1024
    )

    if len(image_data) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Image must be "
                f"<= {settings.max_upload_mb} MB."
            ),
        )

    return image_data


def save_recommendation(
    db: Session,
    user: User,
    planner: str,
    request_data: dict,
    result: RecommendationResponse,
):
    """
    Persist recommendation history.
    """

    row = RecommendationHistory(
        user_id=user.id,
        planner_type=planner,
        budget=result.budget,
        query_data=request_data,
        result_data=result.model_dump(),
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return result


@router.post(
    "/generate-home",
    response_model=RecommendationResponse,
)
def generate_home_route(
    request: HomeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    result = generate_home(request)

    return save_recommendation(
        db=db,
        user=user,
        planner="home",
        request_data=request.model_dump(),
        result=result,
    )


@router.post(
    "/generate-party",
    response_model=RecommendationResponse,
)
def generate_party_route(
    request: PartyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    result = generate_party(request)

    return save_recommendation(
        db=db,
        user=user,
        planner="party",
        request_data=request.model_dump(),
        result=result,
    )


@router.post(
    "/generate-jewelry",
    response_model=RecommendationResponse,
)
async def generate_jewelry_route(
    request: JewelryRequest,
    outfit_image: UploadFile | None = File(
        default=None
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    image_data = await read_image(
        outfit_image
    )

    result = generate_jewelry(
        request,
        image_data,
    )

    return save_recommendation(
        db=db,
        user=user,
        planner="jewelry",
        request_data=request.model_dump(),
        result=result,
    )


@router.get("/history")
def history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    rows = db.scalars(
        select(RecommendationHistory)
        .where(
            RecommendationHistory.user_id
            == user.id
        )
        .order_by(
            RecommendationHistory.created_at.desc()
        )
        .limit(50)
    ).all()

    return [
        {
            "id": row.id,
            "planner_type": row.planner_type,
            "budget": row.budget,
            "created_at": row.created_at.isoformat(),
            "query_data": row.query_data,
            "result_data": row.result_data,
        }
        for row in rows
    ]


@router.get(
    "/recommendations-details/{recommendation_id}"
)
def recommendation_details(
    recommendation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    row = db.scalar(
        select(RecommendationHistory)
        .where(
            RecommendationHistory.id
            == recommendation_id,
            RecommendationHistory.user_id
            == user.id,
        )
    )

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Recommendation not found",
        )

    return {
        "id": row.id,
        "planner_type": row.planner_type,
        "budget": row.budget,
        "query_data": row.query_data,
        "result_data": row.result_data,
        "created_at": row.created_at.isoformat(),
    }