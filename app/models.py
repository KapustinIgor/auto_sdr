from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    domain = Column(String, unique=True, nullable=False)
    industry = Column(String)
    geo = Column(String)
    employee_range = Column(String)
    revenue_range = Column(String)
    icp_fit = Column(Boolean, default=False)
    score = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    name = Column(String)
    title = Column(String)
    email = Column(String, unique=True)
    linkedin_url = Column(String)
    persona = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Signal(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    feature_key = Column(String, nullable=False)
    feature_value = Column(String)
    score_delta = Column(Float, default=0)
    evidence_url = Column(String)
    evidence_snippet = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class ResearchBrief(Base):
    __tablename__ = "research_briefs"
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    brief_json = Column(JSONB().with_variant(Text, "sqlite"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    channel = Column(String, default="email")
    step = Column(String, nullable=False)
    subject = Column(String)
    body = Column(Text)
    status = Column(String, default="DRAFT")
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    reviewer = Column(String)
    status = Column(String, default="PENDING")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Touch(Base):
    __tablename__ = "touches"
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    provider_msg_id = Column(String)
    status = Column(String)
    bounce_reason = Column(Text)


class Reply(Base):
    __tablename__ = "replies"
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow)
    raw_body = Column(Text)
    classification_json = Column(JSONB().with_variant(Text, "sqlite"))


class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    state = Column(String, nullable=False, default="DISCOVERED")
    next_action_at = Column(DateTime)
    metadata_json = Column(JSONB().with_variant(Text, "sqlite"))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Suppression(Base):
    __tablename__ = "suppression_list"
    email_or_domain = Column(String, primary_key=True)
    reason = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    actor = Column(String)
    action = Column(String)
    entity_type = Column(String)
    entity_id = Column(String)
    payload_json = Column(JSONB().with_variant(Text, "sqlite"))
    created_at = Column(DateTime, default=datetime.utcnow)
