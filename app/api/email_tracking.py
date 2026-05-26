import uuid
import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_db
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.models.user import User
from app.models.email_campaign import EmailContact
from app.services.email_campaign_service import record_open, record_click, get_campaign, unsubscribe_contact
from app.services.workspace_service import verify_workspace_access

logger = get_logger(__name__)

router = APIRouter(tags=["email_tracking"])


@router.get("/track/open/{campaign_id}/{contact_id}.gif")
async def track_open(
    campaign_id: str,
    contact_id: str,
    db: AsyncSession = Depends(get_db),
):
    campaign = await get_campaign(db, campaign_id)
    if not campaign:
        return Response(content=b"", media_type="image/gif")

    contact_result = await db.execute(
        select(EmailContact).where(
            EmailContact.id == contact_id,
            EmailContact.workspace_id == campaign.workspace_id,
        )
    )
    contact = contact_result.scalar_one_or_none()
    if not contact or contact.status == "unsubscribed":
        gif_px = bytes([0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00, 0x80, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x21, 0xF9, 0x04, 0x01, 0x00, 0x00, 0x00, 0x00, 0x2C, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44, 0x01, 0x00, 0x3B])
        return Response(content=gif_px, media_type="image/gif")

    await record_open(db, campaign_id, contact_id)
    await db.commit()

    gif_px = bytes([0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00, 0x80, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x21, 0xF9, 0x04, 0x01, 0x00, 0x00, 0x00, 0x00, 0x2C, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44, 0x01, 0x00, 0x3B])
    return Response(content=gif_px, media_type="image/gif")


@router.get("/unsubscribe/{campaign_id}/{contact_id}")
async def unsubscribe(
    campaign_id: str,
    contact_id: str,
    db: AsyncSession = Depends(get_db),
):
    campaign = await get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    ok = await unsubscribe_contact(db, contact_id)
    await db.commit()

    unsub_html = """
    <html><body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
    <h2>You've been unsubscribed</h2>
    <p>You will no longer receive emails from this campaign.</p>
    </body></html>
    """
    return Response(content=unsub_html, media_type="text/html")


@router.get("/l/track/{campaign_id}")
async def track_click(
    campaign_id: str,
    url: str = Query(...),
    contact_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    campaign = await get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    if contact_id:
        await record_click(db, campaign_id, contact_id)
        await db.commit()

    return Response(
        status_code=302,
        headers={"Location": url},
    )