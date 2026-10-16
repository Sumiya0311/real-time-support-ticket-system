from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.security import get_current_user
from app.models.user import User
from app.models.agent import Agent
from app.schemas.agent import (
    AgentCreate,
    AgentResponse,
    AgentAvailabilityUpdate,
)

router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


# 1. Create an agent (Admin only)
@router.post(
    "/",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_agent(
    payload: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create agents",
        )

    user_result = await db.execute(
        select(User).where(User.id == payload.user_id)
    )
    user = user_result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active user not found",
        )

    if user.role != "Agent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected user must have the Agent role",
        )

    existing_agent = await db.execute(
        select(Agent).where(
            (Agent.user_id == payload.user_id)
            | (Agent.email == str(payload.email))
        )
    )

    if existing_agent.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An agent already exists for this user or email",
        )

    agent = Agent(
        user_id=payload.user_id,
        name=payload.name,
        email=str(payload.email),
        availability=payload.availability,
        max_open_tickets=payload.max_open_tickets,
        is_active=True,
    )

    db.add(agent)

    try:
        await db.commit()
        await db.refresh(agent)
    except Exception:
        await db.rollback()
        raise

    return agent


# 2. List agents (Admin only)
@router.get(
    "/",
    response_model=list[AgentResponse],
)
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view the agent directory",
        )

    result = await db.execute(
        select(Agent).order_by(Agent.id)
    )

    return result.scalars().all()


# 3. Update agent availability
@router.patch(
    "/{agent_id}/availability",
    response_model=AgentResponse,
)
async def update_agent_availability(
    agent_id: int,
    payload: AgentAvailabilityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()

    if agent is None or not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active agent not found",
        )

    if (
        current_user.role != "Admin"
        and agent.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own availability",
        )

    agent.availability = payload.availability

    try:
        await db.commit()
        await db.refresh(agent)
    except Exception:
        await db.rollback()
        raise

    return agent