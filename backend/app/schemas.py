from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Optional, Any, Dict
import json

# Comment Schemas
class CommentBase(BaseModel):
    author: str
    text: str

class CommentCreate(CommentBase):
    pass

class Comment(CommentBase):
    id: int
    segment_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# Transcript Segment Schemas
class TranscriptSegmentBase(BaseModel):
    speaker: str
    start_time: float
    end_time: float
    text: str
    highlighted: bool = False

class TranscriptSegmentCreate(TranscriptSegmentBase):
    pass

class TranscriptSegment(TranscriptSegmentBase):
    id: int
    meeting_id: int
    comments: List[Comment] = []

    model_config = {"from_attributes": True}


# Summary Schemas
class ChapterSchema(BaseModel):
    title: str
    summary: str
    start_time: float
    end_time: float

class SummaryBase(BaseModel):
    overview: str
    chapters: List[ChapterSchema] = []
    key_topics: List[str] = []

class SummaryCreate(SummaryBase):
    pass

class Summary(BaseModel):
    id: int
    meeting_id: int
    overview: str
    chapters: List[ChapterSchema] = []
    key_topics: List[str] = []

    model_config = {"from_attributes": True}

    @field_validator('chapters', mode='before')
    @classmethod
    def parse_chapters(cls, v: Any) -> List[ChapterSchema]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return [ChapterSchema(**item) for item in parsed]
            except Exception:
                return []
        return v or []

    @field_validator('key_topics', mode='before')
    @classmethod
    def parse_key_topics(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v or []


# Action Item Schemas
class ActionItemBase(BaseModel):
    text: str
    completed: bool = False
    assignee: Optional[str] = None

class ActionItemCreate(ActionItemBase):
    pass

class ActionItem(ActionItemBase):
    id: int
    meeting_id: int

    model_config = {"from_attributes": True}


# Chat Message Schemas
class ChatMessageBase(BaseModel):
    sender: str  # "user" or "ai"
    message: str

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessage(ChatMessageBase):
    id: int
    meeting_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# Meeting Schemas
class MeetingBase(BaseModel):
    title: str
    date: str
    duration_seconds: int
    participants: List[str] = []
    video_url: Optional[str] = None

class MeetingCreate(BaseModel):
    title: str
    date: str
    duration_seconds: int
    participants: List[str] = []
    video_url: Optional[str] = None
    transcript_text: Optional[str] = None  # To support pasting transcript in form
    # We can also accept an optional uploaded file handled via form-data

class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    duration_seconds: Optional[int] = None
    participants: Optional[List[str]] = None
    video_url: Optional[str] = None

class MeetingBrief(BaseModel):
    id: int
    title: str
    date: str
    duration_seconds: int
    participants: List[str] = []
    video_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator('participants', mode='before')
    @classmethod
    def parse_participants(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [p.strip() for p in v.split(",") if p.strip()]
        return v or []

class MeetingDetail(MeetingBrief):
    transcript_segments: List[TranscriptSegment] = []
    summary: Optional[Summary] = None
    action_items: List[ActionItem] = []
    chat_messages: List[ChatMessage] = []

    model_config = {"from_attributes": True}


# Ask AI Request & Response
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
