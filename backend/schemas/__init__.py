from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserInfo] = None


class UserInfo(BaseModel):
    id: int
    username: str
    name: str
    org_code: str
    scope_code: str
    role: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str
    org_code: str
    scope_code: str


class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    org_code: str
    scope_code: str
    role: str = "viewer"


class OrgCreate(BaseModel):
    code: str
    name: str
    level: int
    parent_code: Optional[str] = None
    sort_order: int = 0


class OrgOut(BaseModel):
    id: int
    code: str
    name: str
    level: int
    parent_code: Optional[str]
    path: str
    sort_order: int

    class Config:
        from_attributes = True


class KbCreate(BaseModel):
    name: str
    description: Optional[str] = None
    org_code: str


class KbOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    org_code: str
    org_name: Optional[str] = None
    owner_id: int
    status: str
    doc_count: int
    total_pages: int
    last_updated: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class KbDetail(KbOut):
    documents: List["DocumentOut"] = []


class KbAdminOut(KbOut):
    owner_name: Optional[str] = None


class KbReviewRequest(BaseModel):
    status: str


class CollaboratorCreate(BaseModel):
    user_id: int
    role: str = "viewer"


class CollaboratorOut(BaseModel):
    id: int
    kb_id: int
    user_id: int
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    org_code: str
    folder_path: str = "/"


class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    folder_path: Optional[str] = None


class OnlineDocCreate(BaseModel):
    name: str
    content: str
    folder_path: str = "/"


class OnlineDocUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None


class DocumentContentOut(BaseModel):
    id: int
    name: str
    content: str
    file_type: str


class DocumentOut(BaseModel):
    id: int
    kb_id: int
    name: str
    file_size: Optional[int]
    file_type: Optional[str]
    folder_path: str
    org_code: str
    status: str
    current_version: int
    parse_error: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocVersionOut(BaseModel):
    id: int
    doc_id: int
    version_no: int
    file_path: str
    change_note: Optional[str]
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str
    kb_ids: List[int]
    top_k: int = 5


class SearchResult(BaseModel):
    id: int
    content: str
    meta: dict
    doc_id: int
    doc_name: str
    kb_id: int
    score: float


class SearchResponse(BaseModel):
    chunks: List[SearchResult]
    total: int


class PlazaSearchItem(BaseModel):
    id: int
    type: str  # kb | bot
    name: str
    description: Optional[str]
    org_code: Optional[str] = None
    is_official: Optional[bool] = None


class PlazaSearchResponse(BaseModel):
    results: List[PlazaSearchItem]
    total: int


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    kb_ids: Optional[List[int]] = None
    history: Optional[List[ChatMessage]] = []
    system_prompt: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    welcome_msg: Optional[str] = None


class BotCreate(BaseModel):
    name: str
    description: Optional[str] = None
    prompt: str
    welcome_msg: Optional[str] = None
    model: Optional[str] = "deepseek-chat"
    kb_ids: List[int] = []
    share_type: str = "private"
    status: Optional[str] = "active"
    avatar: Optional[str] = None


class BotOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    prompt: str
    welcome_msg: Optional[str]
    model: str
    creator_id: int
    share_type: str
    status: str
    is_official: bool
    avatar: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BotDetail(BotOut):
    kb_ids: List[int] = []
    creator_name: Optional[str] = None


class BotReviewRequest(BaseModel):
    status: str


class ExternalAgentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    target_url: str
    sort_order: int = 0


class ExternalAgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    target_url: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ExternalAgentOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    icon: Optional[str]
    category: Optional[str]
    target_url: str
    sort_order: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Event ==============
class EventCreate(BaseModel):
    title: str
    summary: Optional[str] = None
    content: str
    cover: Optional[str] = None
    category: str
    organizer: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    registration_open: bool = True
    max_participants: Optional[int] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    cover: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    organizer: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    registration_open: Optional[bool] = None
    max_participants: Optional[int] = None


class EventOut(BaseModel):
    id: int
    title: str
    summary: Optional[str]
    content: str
    cover: Optional[str]
    category: str
    status: str
    organizer: Optional[str]
    location: Optional[str]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    registration_open: bool
    max_participants: Optional[int]
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventDetail(EventOut):
    registration_count: int = 0
    is_registered: bool = False


class EventRegistrationCreate(BaseModel):
    contact_info: Optional[str] = None
    remark: Optional[str] = None


class EventRegistrationOut(BaseModel):
    id: int
    event_id: int
    user_id: int
    contact_info: Optional[str]
    remark: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Interaction ==============
class InteractionStats(BaseModel):
    likes: int
    rating_count: int
    rating_avg: float
    comments: int
    user_liked: bool
    user_rating: Optional[int]


class CommentCreate(BaseModel):
    content: str


class CommentOut(BaseModel):
    id: int
    target_type: str
    target_id: int
    user_id: int
    user_name: Optional[str] = None
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class RatingCreate(BaseModel):
    score: int = Field(..., ge=1, le=5)


# ============== SysConfig ==============
class SysConfigItem(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None


class SysConfigUpdate(BaseModel):
    value: Any
    description: Optional[str] = None


class SysConfigOut(BaseModel):
    key: str
    value: Any
    description: Optional[str]
    updated_by: Optional[int]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
