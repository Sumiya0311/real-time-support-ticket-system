from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import get_current_user
from app.database import get_db
from app.models.sla_policy import SLAPolicy
from app.models.user import User
from app.schemas.sla_policy import SLAPolicyCreate, SLAPolicyResponse

router = APIRouter(
    prefix="/sla-policies",
    tags=["SLA Policies"],
)


@router.post(
    "/",
    response_model=SLAPolicyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sla_policy(
    payload: SLAPolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create SLA policies",
        )

    result = await db.execute(
        select(SLAPolicy).where(SLAPolicy.priority == payload.priority)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An SLA policy already exists for this priority",
        )

    policy = SLAPolicy(
        priority=payload.priority,
        first_response_minutes=payload.first_response_minutes,
        resolution_minutes=payload.resolution_minutes,
    )

    db.add(policy)
    try:
        await db.commit()
        await db.refresh(policy)
    except Exception:
        await db.rollback()
        raise

    return policy


@router.get("/", response_model=list[SLAPolicyResponse])
async def list_sla_policies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SLAPolicy).order_by(SLAPolicy.id.asc())
    )
    return result.scalars().all()