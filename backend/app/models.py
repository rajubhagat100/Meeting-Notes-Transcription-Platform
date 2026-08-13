from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    date = Column(String)  # ISO Date String (YYYY-MM-DD)
    duration_seconds = Column(Integer)
    participants = Column(Text)  # Comma-separated or JSON list of participants
    video_url = Column(String, nullable=True)  # Placeholder or actual video link
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    transcript_segments = relationship("TranscriptSegment", back_populates="meeting", cascade="all, delete-orphan")
    summary = relationship("Summary", back_populates="meeting", uselist=False, cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="meeting", cascade="all, delete-orphan")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"))
    speaker = Column(String)
    start_time = Column(Float)  # in seconds
    end_time = Column(Float)    # in seconds
    text = Column(Text)
    highlighted = Column(Boolean, default=False)

    # Relationships
    meeting = relationship("Meeting", back_populates="transcript_segments")
    comments = relationship("Comment", back_populates="segment", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    segment_id = Column(Integer, ForeignKey("transcript_segments.id", ondelete="CASCADE"))
    author = Column(String)
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    segment = relationship("TranscriptSegment", back_populates="comments")


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), unique=True)
    overview = Column(Text)
    chapters = Column(Text)  # JSON string representing chapters: [{"title": ..., "summary": ..., "start_time": ..., "end_time": ...}]
    key_topics = Column(Text)  # JSON string representing key topics: ["AI", "API", ...]

    # Relationships
    meeting = relationship("Meeting", back_populates="summary")


class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"))
    text = Column(Text)
    completed = Column(Boolean, default=False)
    assignee = Column(String, nullable=True)

    # Relationships
    meeting = relationship("Meeting", back_populates="action_items")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"))
    sender = Column(String)  # "user" or "ai"
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    meeting = relationship("Meeting", back_populates="chat_messages")
