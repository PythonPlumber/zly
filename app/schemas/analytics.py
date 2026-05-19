from pydantic import BaseModel


class ClickStats(BaseModel):
    total_clicks: int
    clicks_over_time: list[dict]
    top_referrers: list[dict]
    browsers: list[dict]
    devices: list[dict]
    oss: list[dict]


class WorkspaceSummary(BaseModel):
    total_clicks: int
    total_links: int
    links: list[dict]
