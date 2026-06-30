from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Text, BigInteger, Boolean, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.sql import func


class Org(Base):
    __tablename__ = "org"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    level = Column(Integer, nullable=False)
    parent_code = Column(String(20))
    path = Column(String(100), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class SysUser(Base):
    __tablename__ = "sys_user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    name = Column(String(50), nullable=False)
    org_code = Column(String(20), nullable=False)
    scope_code = Column(String(20), nullable=False)
    role = Column(String(20), default="viewer")
    status = Column(String(20), default="active")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    owned_kbs = relationship("KnowledgeBase", back_populates="owner")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    scope_level = Column(Integer, default=1)
    org_code = Column(String(20), nullable=False)
    owner_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    status = Column(String(20), default="draft")
    doc_count = Column(Integer, default=0)
    total_pages = Column(Integer, default=0)
    last_updated = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    owner = relationship("SysUser", back_populates="owned_kbs")
    documents = relationship("KbDocument", back_populates="kb", cascade="all, delete-orphan")


class KbCollaborator(Base):
    __tablename__ = "kb_collaborator"

    id = Column(Integer, primary_key=True, index=True)
    kb_id = Column(Integer, ForeignKey("knowledge_base.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    role = Column(String(20), default="viewer")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (UniqueConstraint("kb_id", "user_id", name="uix_kb_user"),)


class KbDocument(Base):
    __tablename__ = "kb_document"

    id = Column(Integer, primary_key=True, index=True)
    kb_id = Column(Integer, ForeignKey("knowledge_base.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger)
    file_type = Column(String(50))
    folder_path = Column(String(200), default="/")
    scope_level = Column(Integer, default=1)
    org_code = Column(String(20), nullable=False)
    status = Column(String(20), default="parsing")
    current_version = Column(Integer, default=1)
    parse_error = Column(Text)
    created_by = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    kb = relationship("KnowledgeBase", back_populates="documents")
    versions = relationship("DocVersion", back_populates="doc", cascade="all, delete-orphan")


class DocVersion(Base):
    __tablename__ = "doc_version"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, ForeignKey("kb_document.id", ondelete="CASCADE"), nullable=False)
    version_no = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    change_note = Column(Text)
    created_by = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    doc = relationship("KbDocument", back_populates="versions")


class DocChunk(Base):
    __tablename__ = "doc_chunk"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, ForeignKey("kb_document.id", ondelete="CASCADE"), nullable=False)
    kb_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    meta = Column(JSON, default={})
    # embedding 列由 DDL 直接创建为 VECTOR 类型；ORM 层通过原始 SQL 操作向量
    scope_level = Column(Integer, default=1)
    org_code = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class BotConfig(Base):
    __tablename__ = "bot_config"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    avatar = Column(String(200))
    prompt = Column(Text, nullable=False)
    welcome_msg = Column(Text)
    model = Column(String(50), default="deepseek-chat")
    creator_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    share_type = Column(String(20), default="private")
    max_context_rounds = Column(Integer, default=5)
    status = Column(String(20), default="active")
    is_official = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class BotKnowledgeBase(Base):
    __tablename__ = "bot_knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bot_config.id", ondelete="CASCADE"), nullable=False)
    kb_id = Column(Integer, ForeignKey("knowledge_base.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (UniqueConstraint("bot_id", "kb_id", name="uix_bot_kb"),)


class BotAssignedUser(Base):
    __tablename__ = "bot_assigned_user"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bot_config.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (UniqueConstraint("bot_id", "user_id", name="uix_bot_user"),)


class ExternalAgent(Base):
    __tablename__ = "external_agent"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(200))
    category = Column(String(50))
    target_url = Column(String(500), nullable=False)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bot_config.id"))
    kb_id = Column(Integer)
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    sources = Column(JSON, default=[])
    is_useful = Column(Boolean)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Event(Base):
    __tablename__ = "event"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text)
    content = Column(Text, nullable=False)
    cover = Column(String(500))
    category = Column(String(50), nullable=False)
    status = Column(String(20), default="published")
    organizer = Column(String(100))
    location = Column(String(200))
    start_time = Column(TIMESTAMP)
    end_time = Column(TIMESTAMP)
    registration_open = Column(Boolean, default=True)
    max_participants = Column(Integer)
    created_by = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    registrations = relationship("EventRegistration", back_populates="event", cascade="all, delete-orphan")


class EventRegistration(Base):
    __tablename__ = "event_registration"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("event.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    contact_info = Column(String(200))
    remark = Column(Text)
    status = Column(String(20), default="registered")
    created_at = Column(TIMESTAMP, server_default=func.now())

    event = relationship("Event", back_populates="registrations")

    __table_args__ = (UniqueConstraint("event_id", "user_id", name="uix_event_user"),)


class UserLike(Base):
    __tablename__ = "user_like"

    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String(20), nullable=False)
    target_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (UniqueConstraint("target_type", "target_id", "user_id", name="uix_like"),)


class UserRating(Base):
    __tablename__ = "user_rating"

    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String(20), nullable=False)
    target_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    score = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (UniqueConstraint("target_type", "target_id", "user_id", name="uix_rating"),)


class UserComment(Base):
    __tablename__ = "user_comment"

    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String(20), nullable=False)
    target_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class SysConfig(Base):
    __tablename__ = "sys_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(JSON, default={})
    description = Column(Text)
    updated_by = Column(Integer, ForeignKey("sys_user.id"))
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
