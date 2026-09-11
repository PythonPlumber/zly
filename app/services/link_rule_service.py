from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link_rule import LinkRule
from app.schemas.link_rule import LinkRuleCreate


async def create_rule(db: AsyncSession, link_id: str, data: LinkRuleCreate) -> LinkRule:
    rule = LinkRule(
        link_id=link_id,
        type=data.type,
        match_value=data.match_value.strip(),
        destination_url=data.destination_url,
        priority=data.priority,
    )
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return rule


async def get_rules(db: AsyncSession, link_id: str) -> list[LinkRule]:
    result = await db.execute(select(LinkRule).where(LinkRule.link_id == link_id).order_by(LinkRule.priority.desc(), LinkRule.created_at))
    return list(result.scalars().all())


async def get_rule(db: AsyncSession, rule_id: str) -> LinkRule | None:
    result = await db.execute(select(LinkRule).where(LinkRule.id == rule_id))
    return result.scalar_one_or_none()


async def delete_rule(db: AsyncSession, rule: LinkRule) -> None:
    await db.delete(rule)
    await db.flush()


def evaluate_rules(rules: list[LinkRule], context: dict) -> str | None:
    """Evaluate rules against context (country, device, os, language, referrer). Returns matched destination or None."""
    # Highest priority first (already sorted), first match wins
    for rule in rules:
        t = rule.type
        mv = rule.match_value.lower()
        if t in ("geo", "country"):
            if (context.get("country") or "").lower() == mv:
                return rule.destination_url
        elif t == "device":
            if (context.get("device") or "").lower() == mv:
                return rule.destination_url
        elif t == "os":
            if (context.get("os") or "").lower() == mv:
                return rule.destination_url
        elif t == "language":
            langs = (context.get("accept_language") or "").lower()
            if mv in langs:
                return rule.destination_url
        elif t == "referrer":
            ref = (context.get("referrer") or "").lower()
            if mv in ref:
                return rule.destination_url
        elif t == "city":
            if (context.get("city") or "").lower() == mv:
                return rule.destination_url
    return None
