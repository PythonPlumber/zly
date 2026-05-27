from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    has_next: bool
    items: list