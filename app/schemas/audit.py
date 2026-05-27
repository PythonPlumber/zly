from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    workspace_id: str | None = None
    user_id: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    details: str | None = None
    ip_address: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedAuditLogs(BaseModel):
    total: int
    page: int
    page_size: int
    has_next: bool
    items: list[AuditLogResponse]
