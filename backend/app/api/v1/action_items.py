"""Action Items API Endpoints"""
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundException
from app.db.database import get_db
from app.db.models.user import User
from app.db.repositories.meeting_repo import MeetingRepository
from app.db.repositories.summary_repo import IntelligenceRepository
from app.schemas.action_item import ActionItemCreate, ActionItemRead, ActionItemUpdate
from app.schemas.common import ApiResponse

router = APIRouter(tags=["Action Items"])


@router.get(
    "/meetings/{meeting_id}/action-items",
    response_model=ApiResponse[List[ActionItemRead]],
    summary="Get action items for a meeting with status or assignee filter",
)
async def get_meeting_action_items(
    meeting_id: uuid.UUID,
    status: Optional[str] = Query(None, description="OPEN | IN_PROGRESS | COMPLETED | CANCELLED"),
    assignee: Optional[str] = Query(None, description="Filter by assignee name"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting_repo = MeetingRepository(db)
    meeting = await meeting_repo.get_by_id(user_id=current_user.id, entity_id=meeting_id)
    if not meeting:
        raise NotFoundException(message="Meeting not found")

    intel_repo = IntelligenceRepository(db)
    items = await intel_repo.get_action_items(meeting_id=meeting_id, status=status, assignee=assignee)
    return ApiResponse.ok(data=[ActionItemRead.model_validate(i) for i in items])


@router.post(
    "/meetings/{meeting_id}/action-items",
    response_model=ApiResponse[ActionItemRead],
    status_code=status.HTTP_201_CREATED,
    summary="Manually add a new action item to a meeting",
)
async def create_action_item(
    meeting_id: uuid.UUID,
    req: ActionItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting_repo = MeetingRepository(db)
    meeting = await meeting_repo.get_by_id(user_id=current_user.id, entity_id=meeting_id)
    if not meeting:
        raise NotFoundException(message="Meeting not found")

    intel_repo = IntelligenceRepository(db)
    item = await intel_repo.create_action_item(
        meeting_id=meeting_id,
        task=req.task,
        assignee=req.assignee,
        due_date=req.due_date,
        priority=req.priority,
        status=req.status,
        timestamp_seconds=req.timestamp_seconds,
    )
    return ApiResponse.ok(data=ActionItemRead.model_validate(item), message="Action item created successfully")


@router.put(
    "/action-items/{action_item_id}",
    response_model=ApiResponse[ActionItemRead],
    summary="Update action item status, assignee, priority, or task details",
)
async def update_action_item(
    action_item_id: uuid.UUID,
    req: ActionItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    intel_repo = IntelligenceRepository(db)
    update_data = req.model_dump(exclude_unset=True)
    item = await intel_repo.update_action_item(action_item_id=action_item_id, **update_data)
    if not item:
        raise NotFoundException(message="Action item not found")
    return ApiResponse.ok(data=ActionItemRead.model_validate(item), message="Action item updated successfully")


@router.delete(
    "/action-items/{action_item_id}",
    response_model=ApiResponse[dict],
    summary="Delete an action item",
)
async def delete_action_item(
    action_item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    intel_repo = IntelligenceRepository(db)
    deleted = await intel_repo.delete_action_item(action_item_id=action_item_id)
    if not deleted:
        raise NotFoundException(message="Action item not found")
    return ApiResponse.ok(data={"deleted": True}, message="Action item deleted successfully")
