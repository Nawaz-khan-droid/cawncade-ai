from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    display_name = Column(String(255), nullable=True)
    auth_provider = Column(String(50), default="local")  # local | google
    password_hash = Column(String(255), nullable=True)
    role = Column(String(20), default="user")  # user | admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    requests = relationship("AnalysisRequest", back_populates="user")
    feedback = relationship("UserFeedback", back_populates="user")


class TrustedSource(Base):
    __tablename__ = "trusted_sources"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    domain = Column(String(255), unique=True, index=True, nullable=False)
    source_name = Column(String(255), nullable=True)
    credibility_score = Column(Float, default=0.5)  # 0.0 to 1.0
    region = Column(String(100), default="global")  # global | india | us | eu
    category = Column(String(100), default="general")  # general | wire | broadcast | fact_check
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    sources = relationship("RetrievedSource", back_populates="trusted_source")


class AnalysisRequest(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    input_type = Column(String(20), nullable=False)  # text | url | image | video
    input_text = Column(Text, nullable=False)
    input_metadata = Column(JSON, nullable=True)  # extracted metadata
    status = Column(String(20), default="pending")  # pending | processing | completed | failed
    compute_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="requests")
    sources = relationship("RetrievedSource", back_populates="request")
    result = relationship("AnalysisResult", back_populates="request", uselist=False)
    feedback = relationship("UserFeedback", back_populates="request")


class RetrievedSource(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    trusted_source_id = Column(Integer, ForeignKey("trusted_sources.id"), nullable=True)
    url = Column(Text, nullable=False)
    title = Column(String(500), nullable=True)
    snippet = Column(Text, nullable=True)
    source_name = Column(String(255), nullable=True)
    credibility_score = Column(Float, default=0.5)
    published_at = Column(DateTime(timezone=True), nullable=True)
    relevance_score = Column(Float, default=0.0)
    is_conflicting = Column(Boolean, default=False)
    raw_content_hash = Column(String(64), nullable=True)  # SHA-256 for dedup

    request = relationship("AnalysisRequest", back_populates="sources")
    trusted_source = relationship("TrustedSource", back_populates="sources")


class AnalysisResult(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey("requests.id"), unique=True, nullable=False)
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    credibility_avg = Column(Float, default=0.0)
    agreement_score = Column(Float, default=0.0)
    diversity_score = Column(Float, default=0.0)
    recency_score = Column(Float, default=0.0)
    grounding_score = Column(Float, default=0.0)
    bias_score = Column(Float, default=0.0)
    conflict_score = Column(Float, default=0.0)
    ai_risk_score = Column(Float, default=0.0)
    tfidf_suspicion_score = Column(Float, nullable=True)
    output_text = Column(Text, nullable=False)
    output_metadata = Column(JSON, nullable=True)  # agreements, conflicts, context, disclaimers
    dynamic_disclaimers = Column(JSON, nullable=True)  # list of applicable disclaimers
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    request = relationship("AnalysisRequest", back_populates="result")


class UserFeedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    user_rating = Column(Integer, nullable=True)  # 1-5 star
    user_comment = Column(Text, nullable=True)
    was_helpful = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="feedback")
    request = relationship("AnalysisRequest", back_populates="feedback")
