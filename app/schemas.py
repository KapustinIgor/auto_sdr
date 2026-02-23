from pydantic import BaseModel


class AccountCreate(BaseModel):
    name: str
    domain: str
    industry: str | None = None
    geo: str = "US"
    employee_range: str | None = None
    revenue_range: str | None = None


class ContactCreate(BaseModel):
    account_id: int
    name: str
    title: str
    email: str
    linkedin_url: str | None = None
    persona: str | None = None


class ApprovalAction(BaseModel):
    reviewer: str
    status: str
    notes: str | None = None
