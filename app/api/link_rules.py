from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.link_rule import LinkRuleCreate, LinkRuleResponse
from app.services.link_rule_service import create_rule, delete_rule, get_rule, get_rules
from app.services.link_service import get_link_by_id
from app.services.workspace_service import verify_workspace_access

router = APIRouter(tags=["link-rules"])


@router.post("/links/{link_id}/rules", response_model=LinkRuleResponse, status_code=status.HTTP_201_CREATED)
async def api_create_rule(
    link_id: str,
    data: LinkRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, current_user, required_permission="links:update")
    rule = await create_rule(db, link_id, data)
    return rule


@router.get("/links/{link_id}/rules", response_model=list[LinkRuleResponse])
async def api_list_rules(
    link_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, current_user, required_permission="analytics:view")
    rules = await get_rules(db, link_id)
    return rules


@router.delete("/links/{link_id}/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_rule(
    link_id: str,
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = await get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    await verify_workspace_access(db, link.workspace_id, current_user, required_permission="links:update")
    rule = await get_rule(db, rule_id)
    if not rule or rule.link_id != link_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    await delete_rule(db, rule)
